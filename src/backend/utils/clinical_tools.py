"""
Deterministic clinical helpers for Sara.

These utilities keep high-risk arithmetic and FHIR bundle extraction outside
of the LLM loop. They are intentionally small, dependency-light, and reusable
from the local agent, Modal API, and IRIS Embedded Python wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

FHIRResource = Dict[str, Any]


@dataclass(frozen=True)
class LabObservation:
    """A normalized numeric lab/vital observation."""

    id: str
    code: str
    display: str
    value: float
    unit: str
    effective: datetime
    resource: FHIRResource


def bundle_entries(bundle_or_resource: FHIRResource) -> List[FHIRResource]:
    """Return resources from a FHIR Bundle, or the resource itself."""
    if not bundle_or_resource:
        return []
    if bundle_or_resource.get("resourceType") != "Bundle":
        return [bundle_or_resource]
    entries = bundle_or_resource.get("entry", [])
    return [
        entry["resource"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("resource"), dict)
    ]


def resources_by_type(resources: Iterable[FHIRResource], resource_type: str) -> List[FHIRResource]:
    """Filter a resource iterable by FHIR resourceType."""
    return [resource for resource in resources if resource.get("resourceType") == resource_type]


def parse_fhir_datetime(value: str | None) -> Optional[datetime]:
    """Parse a FHIR dateTime/date string into an aware datetime when possible."""
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        try:
            parsed_date = date.fromisoformat(value[:10])
            return datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc)
        except ValueError:
            return None


def patient_age(birth_date: str, now: datetime | None = None) -> Optional[int]:
    """Calculate age in years from a FHIR Patient.birthDate."""
    if not birth_date:
        return None
    try:
        born = date.fromisoformat(birth_date)
    except ValueError:
        return None
    today = (now or datetime.now(timezone.utc)).date()
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


def patient_display_name(patient: FHIRResource | None) -> str:
    """Build a readable patient name from FHIR Patient.name."""
    if not patient:
        return "Unknown patient"
    names = patient.get("name") or []
    if not names:
        return patient.get("id", "Unknown patient")
    primary = names[0]
    given = " ".join(primary.get("given", []))
    family = primary.get("family", "")
    return " ".join(part for part in [given, family] if part).strip() or patient.get("id", "Unknown patient")


def patient_identifier(patient: FHIRResource | None, preferred_system: str | None = None) -> str:
    """Return a stable patient identifier, preferring MRN-like identifiers."""
    if not patient:
        return ""
    identifiers = patient.get("identifier") or []
    if preferred_system:
        for identifier in identifiers:
            if identifier.get("system") == preferred_system and identifier.get("value"):
                return identifier["value"]
    for identifier in identifiers:
        if identifier.get("value"):
            return identifier["value"]
    return patient.get("id", "")


def coding_values(resource: FHIRResource) -> List[str]:
    """Return all useful code/display/text strings from a CodeableConcept-bearing resource."""
    values: List[str] = []
    code = resource.get("code") or {}
    if isinstance(code, dict):
        if code.get("text"):
            values.append(str(code["text"]))
        for coding in code.get("coding") or []:
            if coding.get("code"):
                values.append(str(coding["code"]))
            if coding.get("display"):
                values.append(str(coding["display"]))
    return values


def _observation_datetime(resource: FHIRResource) -> Optional[datetime]:
    return (
        parse_fhir_datetime(resource.get("effectiveDateTime"))
        or parse_fhir_datetime(resource.get("issued"))
        or parse_fhir_datetime(resource.get("effectivePeriod", {}).get("start"))
    )


def normalize_numeric_observations(
    resources: Iterable[FHIRResource],
    code: str | None = None,
) -> List[LabObservation]:
    """Extract numeric observations matching an optional code/display token."""
    observations: List[LabObservation] = []
    desired = code.lower() if code else None

    for resource in resources:
        if resource.get("resourceType") != "Observation":
            continue
        values = [value.lower() for value in coding_values(resource)]
        if desired and desired not in values:
            continue

        quantity = resource.get("valueQuantity")
        if not isinstance(quantity, dict) or "value" not in quantity:
            continue
        observed_at = _observation_datetime(resource)
        if not observed_at:
            continue
        try:
            numeric_value = float(quantity["value"])
        except (TypeError, ValueError):
            continue

        observations.append(
            LabObservation(
                id=str(resource.get("id", "")),
                code=code or (coding_values(resource)[0] if coding_values(resource) else ""),
                display=_display_text(resource),
                value=numeric_value,
                unit=str(quantity.get("unit") or quantity.get("code") or ""),
                effective=observed_at,
                resource=resource,
            )
        )

    return sorted(observations, key=lambda obs: obs.effective, reverse=True)


def latest_numeric_observation(
    resources: Iterable[FHIRResource],
    code: str,
    now: datetime | None = None,
    within: timedelta | None = None,
) -> Optional[LabObservation]:
    """Return the latest numeric observation matching code and optional lookback."""
    observations = normalize_numeric_observations(resources, code)
    if within is None:
        return observations[0] if observations else None

    anchor = now or datetime.now(timezone.utc)
    for observation in observations:
        if anchor - observation.effective <= within:
            return observation
    return None


def average_numeric_observation(
    resources: Iterable[FHIRResource],
    code: str,
    now: datetime | None = None,
    within: timedelta | None = None,
) -> Optional[float]:
    """Calculate the average numeric observation matching code and optional lookback."""
    anchor = now or datetime.now(timezone.utc)
    observations = normalize_numeric_observations(resources, code)
    if within is not None:
        observations = [obs for obs in observations if anchor - obs.effective <= within]
    if not observations:
        return None
    return round(mean(obs.value for obs in observations), 2)


def magnesium_repletion(magnesium_mg_dl: float | None) -> Optional[Dict[str, Any]]:
    """Return deterministic IV magnesium recommendation from contest dosing rules."""
    if magnesium_mg_dl is None or magnesium_mg_dl >= 2.0:
        return None
    if magnesium_mg_dl < 1.0:
        dose, hours, severity = 4, 4, "severe"
    elif magnesium_mg_dl < 1.5:
        dose, hours, severity = 2, 2, "moderate"
    else:
        dose, hours, severity = 1, 1, "mild"
    return {
        "type": "MedicationRequest",
        "severity": severity,
        "medication": "IV magnesium sulfate",
        "dose": dose,
        "doseUnit": "g",
        "duration": hours,
        "durationUnit": "h",
        "rationale": f"Serum magnesium {magnesium_mg_dl:g} mg/dL",
    }


def potassium_repletion(potassium_meq_l: float | None, goal: float = 3.5) -> Optional[Dict[str, Any]]:
    """Return deterministic oral potassium recommendation from contest dosing rules."""
    if potassium_meq_l is None or potassium_meq_l >= goal:
        return None
    deficit_tenths = round((goal - potassium_meq_l) * 10)
    dose = max(deficit_tenths * 10, 10)
    return {
        "type": "MedicationRequest",
        "medication": "oral potassium chloride",
        "dose": dose,
        "doseUnit": "mEq",
        "rationale": f"Serum potassium {potassium_meq_l:g} mEq/L; goal {goal:g} mEq/L",
        "pairedFollowUp": "Morning serum potassium level next day at 08:00",
    }


def needs_follow_up_lab(
    resources: Iterable[FHIRResource],
    code: str,
    now: datetime | None = None,
    max_age: timedelta = timedelta(days=365),
) -> bool:
    """Return true if no lab exists or the most recent result is older than max_age."""
    latest = latest_numeric_observation(resources, code)
    if not latest:
        return True
    return (now or datetime.now(timezone.utc)) - latest.effective > max_age


def describe_conditions(resources: Iterable[FHIRResource]) -> List[Dict[str, str]]:
    """Extract compact condition display rows."""
    rows = []
    for condition in resources_by_type(resources, "Condition"):
        rows.append(
            {
                "id": str(condition.get("id", "")),
                "display": _display_text(condition),
                "status": _coding_text(condition.get("clinicalStatus", {})) or str(condition.get("status", "")),
            }
        )
    return rows


def describe_medications(resources: Iterable[FHIRResource]) -> List[Dict[str, str]]:
    """Extract compact MedicationRequest display rows."""
    rows = []
    for med in resources_by_type(resources, "MedicationRequest"):
        med_text = _coding_text(med.get("medicationCodeableConcept", {})) or _display_text(med)
        rows.append(
            {
                "id": str(med.get("id", "")),
                "display": med_text,
                "status": str(med.get("status", "")),
                "intent": str(med.get("intent", "")),
            }
        )
    return rows


def _display_text(resource: FHIRResource) -> str:
    return _coding_text(resource.get("code", {})) or str(resource.get("id", resource.get("resourceType", "")))


def _coding_text(codeable: Any) -> str:
    if not isinstance(codeable, dict):
        return ""
    if codeable.get("text"):
        return str(codeable["text"])
    for coding in codeable.get("coding") or []:
        if coding.get("display"):
            return str(coding["display"])
        if coding.get("code"):
            return str(coding["code"])
    return ""
