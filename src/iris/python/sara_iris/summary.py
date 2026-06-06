"""Fallback copy of Sara summary logic for IRIS Embedded Python imports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


def build_patient_summary(
    bundle_or_resources: Dict[str, Any] | Iterable[Dict[str, Any]],
    role: str = "ed_clinician",
    now: datetime | None = None,
) -> Dict[str, Any]:
    """Compact fallback summary used when the full src.backend package is unavailable."""
    resources = _resources(bundle_or_resources)
    patient = next((resource for resource in resources if resource.get("resourceType") == "Patient"), {})
    observations = [resource for resource in resources if resource.get("resourceType") == "Observation"]
    conditions = [resource for resource in resources if resource.get("resourceType") == "Condition"]
    medications = [resource for resource in resources if resource.get("resourceType") == "MedicationRequest"]
    anchor = now or datetime.now(timezone.utc)

    labs = []
    for code in ["MG", "K", "GLU", "A1C"]:
        lab = _latest_lab(observations, code)
        if lab:
            labs.append(lab)

    actions = []
    mg = next((lab for lab in labs if lab["code"] == "MG"), None)
    if mg and mg["value"] < 2:
        actions.append({"type": "MedicationRequest", "medication": "IV magnesium sulfate", "rationale": f"Serum magnesium {mg['value']:g} mg/dL"})
    potassium = next((lab for lab in labs if lab["code"] == "K"), None)
    if potassium and potassium["value"] < 3.5:
        dose = max(round((3.5 - potassium["value"]) * 10) * 10, 10)
        actions.append({"type": "MedicationRequest", "medication": "oral potassium chloride", "dose": dose, "doseUnit": "mEq"})
    a1c = next((lab for lab in labs if lab["code"] == "A1C"), None)
    a1c_gap = not a1c or (anchor - _date(a1c["effectiveDateTime"])).days > 365
    if a1c_gap:
        actions.append({"type": "ServiceRequest", "test": "Hemoglobin A1C", "code": "4548-4"})

    patient_id = patient.get("id", "sara-demo-patient")
    patient_id_literal = _sql_string_literal(patient_id)
    name = _patient_name(patient)
    return {
        "artifactType": "SaraPatientSummary",
        "role": role,
        "patient": {"id": patient_id, "name": name, "birthDate": patient.get("birthDate", "")},
        "activeConditions": [{"display": _display(condition)} for condition in conditions],
        "recentLabs": labs,
        "medications": [{"display": _display(med)} for med in medications],
        "careGaps": [{"type": "lab", "description": "A1C is missing or older than 1 year"}] if a1c_gap else [],
        "recommendedActions": actions,
        "roleSummary": f"{role} summary for {name}: {len(conditions)} conditions, {len(labs)} recent labs, {len(actions)} suggested actions.",
        "plainLanguage": f"{name}'s available FHIR chart was summarized by Sara.",
        "irisEvidence": {
            "fhirServer": {
                "product": "InterSystems IRIS for Health",
                "endpoint": "/fhir/r4",
                "patientSearch": f"GET /fhir/r4/Patient/{patient_id}",
            },
            "interoperability": {
                "production": "Sara.Interop.Production",
                "businessService": "Sara.REST.TaskService",
                "businessProcess": "Sara.Interop.AgentProcess",
                "businessOperation": "Sara.Interop.FHIRServerOperation",
            },
            "sqlBuilder": {
                "title": "FHIR SQL Builder lab trend query",
                "sql": (
                    "SELECT PatientId, Code, EffectiveDateTime, ValueQuantity_Value, ValueQuantity_Unit "  # nosec B608
                    f"FROM HS_FHIR_R4_Observation WHERE PatientId = {patient_id_literal}"
                ),
            },
        },
    }


def _resources(value):
    if isinstance(value, dict) and value.get("resourceType") == "Bundle":
        return [entry["resource"] for entry in value.get("entry", []) if "resource" in entry]
    if isinstance(value, dict):
        return [value]
    return list(value)


def _sql_string_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _latest_lab(observations, code):
    matches = [obs for obs in observations if code in _codes(obs)]
    matches.sort(key=lambda obs: obs.get("effectiveDateTime", ""), reverse=True)
    if not matches:
        return None
    obs = matches[0]
    quantity = obs.get("valueQuantity", {})
    return {
        "code": code,
        "label": _display(obs),
        "value": float(quantity.get("value", 0)),
        "unit": quantity.get("unit", ""),
        "effectiveDateTime": obs.get("effectiveDateTime", ""),
        "resourceId": obs.get("id", ""),
    }


def _codes(resource):
    codeable = resource.get("code", {})
    values = [codeable.get("text", "")]
    values.extend(coding.get("code", "") for coding in codeable.get("coding", []))
    return values


def _display(resource):
    codeable = resource.get("code") or resource.get("medicationCodeableConcept") or {}
    if codeable.get("text"):
        return codeable["text"]
    for coding in codeable.get("coding", []):
        if coding.get("display"):
            return coding["display"]
    return resource.get("id", resource.get("resourceType", "FHIR resource"))


def _patient_name(patient):
    names = patient.get("name") or []
    if not names:
        return patient.get("id", "Unknown patient")
    primary = names[0]
    return " ".join(primary.get("given", []) + [primary.get("family", "")]).strip()


def _date(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)
