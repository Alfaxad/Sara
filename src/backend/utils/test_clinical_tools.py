from datetime import datetime, timezone, timedelta

from src.backend.utils.clinical_tools import (
    average_numeric_observation,
    latest_numeric_observation,
    magnesium_repletion,
    patient_age,
    potassium_repletion,
)
from src.backend.utils.patient_summary import build_patient_summary


def _observation(code: str, value: float, effective: str):
    return {
        "resourceType": "Observation",
        "id": f"obs-{code}-{value}",
        "status": "final",
        "code": {"coding": [{"code": code, "display": code}]},
        "valueQuantity": {"value": value, "unit": "mg/dL"},
        "effectiveDateTime": effective,
    }


def test_patient_age_rounds_down_before_birthday():
    now = datetime(2026, 6, 5, tzinfo=timezone.utc)

    assert patient_age("1980-06-06", now) == 45


def test_latest_observation_respects_window():
    now = datetime(2026, 6, 5, 12, tzinfo=timezone.utc)
    resources = [
        _observation("MG", 1.9, "2026-06-04T13:00:00+00:00"),
        _observation("MG", 1.2, "2026-06-03T12:00:00+00:00"),
    ]

    latest = latest_numeric_observation(resources, "MG", now=now, within=timedelta(hours=24))

    assert latest is not None
    assert latest.value == 1.9


def test_average_observation_over_window():
    now = datetime(2026, 6, 5, 12, tzinfo=timezone.utc)
    resources = [
        _observation("GLU", 100, "2026-06-05T10:00:00+00:00"),
        _observation("GLU", 140, "2026-06-05T08:00:00+00:00"),
        _observation("GLU", 999, "2026-06-01T08:00:00+00:00"),
    ]

    assert average_numeric_observation(resources, "GLU", now=now, within=timedelta(hours=24)) == 120


def test_repletion_rules_are_deterministic():
    assert magnesium_repletion(1.4)["dose"] == 2
    assert potassium_repletion(3.2)["dose"] == 30


def test_build_patient_summary_contains_iris_evidence():
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "sara-demo-patient", "birthDate": "1974-04-12", "name": [{"given": ["Amina"], "family": "Yusuf"}]}},
            {"resource": _observation("MG", 1.3, "2026-06-05T06:00:00+00:00")},
            {"resource": _observation("K", 3.2, "2026-06-05T05:00:00+00:00")},
        ],
    }

    summary = build_patient_summary(bundle, now=datetime(2026, 6, 5, 12, tzinfo=timezone.utc))

    assert summary["artifactType"] == "SaraPatientSummary"
    assert summary["patient"]["name"] == "Amina Yusuf"
    assert len(summary["recommendedActions"]) >= 2
    assert summary["irisEvidence"]["interoperability"]["production"] == "Sara.Interop.Production"
