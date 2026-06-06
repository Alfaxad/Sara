"""
Smart Patient Summary for the Sara for IRIS contest edition.

The summary is deterministic by design: all patient facts, calculations, and
recommended actions are produced from FHIR resources before any optional LLM
wordsmithing. This makes the artifact auditable in the IRIS message trace.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List

from src.backend.utils.clinical_tools import (
    FHIRResource,
    average_numeric_observation,
    bundle_entries,
    describe_conditions,
    describe_medications,
    latest_numeric_observation,
    magnesium_repletion,
    needs_follow_up_lab,
    patient_age,
    patient_display_name,
    patient_identifier,
    potassium_repletion,
    resources_by_type,
)


def build_patient_summary(
    bundle_or_resources: FHIRResource | Iterable[FHIRResource],
    role: str = "ed_clinician",
    now: datetime | None = None,
) -> Dict[str, Any]:
    """Build a role-specific smart summary from FHIR resources."""
    resources = _coerce_resources(bundle_or_resources)
    anchor = now or datetime.now(timezone.utc)
    patients = resources_by_type(resources, "Patient")
    patient = patients[0] if patients else {}

    labs = _lab_digest(resources, anchor)
    actions = _recommended_actions(resources, labs, anchor)
    conditions = describe_conditions(resources)
    medications = describe_medications(resources)
    care_gaps = _care_gaps(resources, labs, anchor)

    summary = {
        "artifactType": "SaraPatientSummary",
        "role": role,
        "patient": {
            "id": patient.get("id", ""),
            "name": patient_display_name(patient),
            "mrn": patient_identifier(patient),
            "gender": patient.get("gender", ""),
            "birthDate": patient.get("birthDate", ""),
            "age": patient_age(str(patient.get("birthDate", "")), anchor),
        },
        "activeConditions": conditions,
        "recentLabs": labs,
        "medications": medications,
        "careGaps": care_gaps,
        "recommendedActions": actions,
        "roleSummary": _role_summary(role, patient, labs, conditions, medications, care_gaps, actions),
        "irisEvidence": iris_evidence(patient.get("id", "sara-demo-patient")),
    }
    summary["plainLanguage"] = _plain_language(summary)
    return summary


def iris_evidence(patient_id: str) -> Dict[str, Any]:
    """Describe the InterSystems-specific proof points for the UI and judges."""
    patient_id_literal = _sql_string_literal(patient_id)
    return {
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
            "messageTrace": [
                "REST request accepted by Sara.REST.TaskService",
                "TaskRequest routed through Sara.Interop.Production",
                "Embedded Python summary builder executed in Sara.Interop.AgentProcess",
                "FHIR read/write activity sent to InterSystems FHIR Server",
                "TaskResponse returned with summary and trace artifact",
            ],
        },
        "sqlBuilder": {
            "title": "FHIR SQL Builder lab trend query",
            "sql": (
                "SELECT PatientId, Code, EffectiveDateTime, ValueQuantity_Value, ValueQuantity_Unit "  # nosec B608
                "FROM HS_FHIR_R4_Observation "
                f"WHERE PatientId = {patient_id_literal} "
                "AND Code IN ('MG','K','GLU','A1C') "
                "ORDER BY EffectiveDateTime DESC"
            ),
        },
        "vectorSearch": {
            "status": "optional-ready",
            "useCase": "Retrieve patient-friendly explanations for abnormal labs and attach cited education text.",
        },
    }


def _sql_string_literal(value: str) -> str:
    """Render a value as a SQL string literal for display-only SQL artifacts."""
    return "'" + value.replace("'", "''") + "'"


def _coerce_resources(bundle_or_resources: FHIRResource | Iterable[FHIRResource]) -> List[FHIRResource]:
    if isinstance(bundle_or_resources, dict):
        return bundle_entries(bundle_or_resources)
    return list(bundle_or_resources)


def _lab_digest(resources: List[FHIRResource], now: datetime) -> List[Dict[str, Any]]:
    labels = {
        "MG": "Magnesium",
        "K": "Potassium",
        "GLU": "Blood glucose",
        "A1C": "Hemoglobin A1C",
    }
    labs: List[Dict[str, Any]] = []
    for code, label in labels.items():
        latest = latest_numeric_observation(resources, code)
        if not latest:
            continue
        entry = {
            "code": code,
            "label": label,
            "value": latest.value,
            "unit": latest.unit,
            "effectiveDateTime": latest.effective.isoformat(),
            "ageHours": round((now - latest.effective).total_seconds() / 3600, 1),
            "resourceId": latest.id,
        }
        if code == "GLU":
            avg = average_numeric_observation(resources, "GLU", now=now, within=timedelta(hours=24))
            if avg is not None:
                entry["average24h"] = avg
        labs.append(entry)
    return labs


def _recommended_actions(resources: List[FHIRResource], labs: List[Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
    latest_mg = latest_numeric_observation(resources, "MG", now=now, within=timedelta(hours=24))
    latest_k = latest_numeric_observation(resources, "K")
    actions: List[Dict[str, Any]] = []

    mg_action = magnesium_repletion(latest_mg.value if latest_mg else None)
    if mg_action:
        actions.append(mg_action)

    k_action = potassium_repletion(latest_k.value if latest_k else None)
    if k_action:
        actions.append(k_action)

    if needs_follow_up_lab(resources, "A1C", now=now):
        actions.append(
            {
                "type": "ServiceRequest",
                "test": "Hemoglobin A1C",
                "code": "4548-4",
                "rationale": "No current A1C found within the last year",
            }
        )

    if not actions and labs:
        actions.append(
            {
                "type": "Review",
                "rationale": "No deterministic medication or follow-up lab action triggered",
            }
        )
    return actions


def _care_gaps(resources: List[FHIRResource], labs: List[Dict[str, Any]], now: datetime) -> List[Dict[str, str]]:
    gaps: List[Dict[str, str]] = []
    if needs_follow_up_lab(resources, "A1C", now=now):
        gaps.append({"type": "lab", "description": "A1C is missing or older than 1 year"})
    if not any(lab["code"] == "MG" and lab["ageHours"] <= 24 for lab in labs):
        gaps.append({"type": "lab", "description": "No magnesium level in the last 24 hours"})
    return gaps


def _role_summary(
    role: str,
    patient: FHIRResource,
    labs: List[Dict[str, Any]],
    conditions: List[Dict[str, str]],
    medications: List[Dict[str, str]],
    care_gaps: List[Dict[str, str]],
    actions: List[Dict[str, Any]],
) -> str:
    name = patient_display_name(patient)
    condition_text = ", ".join(item["display"] for item in conditions[:3]) or "no active conditions listed"
    lab_text = "; ".join(
        f"{lab['label']} {lab['value']:g} {lab['unit']}".strip() for lab in labs[:4]
    ) or "no recent labs found"
    action_text = "; ".join(item.get("rationale", item.get("type", "review")) for item in actions[:3])

    if role == "patient":
        return f"{name}'s chart shows {condition_text}. Recent lab highlights: {lab_text}. Next steps: {action_text}."
    if role == "care_manager":
        gap_text = "; ".join(gap["description"] for gap in care_gaps) or "no immediate care gaps detected"
        return f"Care management view for {name}: {condition_text}. Medication count: {len(medications)}. Gaps: {gap_text}."
    return f"ED clinician view for {name}: {condition_text}. Recent labs: {lab_text}. Recommended actions: {action_text}."


def _plain_language(summary: Dict[str, Any]) -> str:
    patient = summary["patient"]
    gaps = summary.get("careGaps", [])
    if gaps:
        gap_text = "; ".join(gap["description"] for gap in gaps)
        return f"{patient['name']} has follow-up items to review: {gap_text}."
    return f"{patient['name']} has no urgent deterministic follow-up gaps from the available FHIR resources."
