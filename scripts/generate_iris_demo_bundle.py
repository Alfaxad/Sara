"""Generate the Sara for IRIS demo FHIR transaction bundle.

The old Sara UI tasks refer to several MedAgentBench-style MRNs. The original
HAPI database is packaged inside the MedAgentBench Docker image, so this bundle
keeps a lightweight, deterministic synthetic slice that exercises those same
task paths against IRIS for Health.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MRN_SYSTEM = "http://nadhari.ai/sara/mrn"
LAB_SYSTEM = "http://nadhari.ai/sara/lab-code"
UCUM_SYSTEM = "http://unitsofmeasure.org"


def transaction_entry(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "fullUrl": f"urn:uuid:{resource['id']}",
        "resource": resource,
        "request": {
            "method": "PUT",
            "url": f"{resource['resourceType']}/{resource['id']}",
        },
    }


def patient(
    patient_id: str,
    mrn: str,
    given: str,
    family: str,
    birth_date: str,
    gender: str,
) -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [{"system": MRN_SYSTEM, "value": mrn}],
        "name": [{"use": "official", "family": family, "given": given.split()}],
        "gender": gender,
        "birthDate": birth_date,
    }


def condition(
    condition_id: str,
    patient_id: str,
    display: str,
    recorded_date: str,
    snomed_code: str = "64572001",
) -> dict[str, Any]:
    return {
        "resourceType": "Condition",
        "id": condition_id,
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active",
                }
            ]
        },
        "code": {
            "coding": [{"system": "http://snomed.info/sct", "code": snomed_code, "display": display}],
            "text": display,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "recordedDate": recorded_date,
    }


def lab_observation(
    observation_id: str,
    patient_id: str,
    code: str,
    label: str,
    loinc_code: str,
    value: float,
    unit: str,
    effective: str,
) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": observation_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {"system": "http://loinc.org", "code": loinc_code, "display": label},
                {"system": LAB_SYSTEM, "code": code, "display": label},
            ],
            "text": code,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": effective,
        "valueQuantity": {
            "value": value,
            "unit": unit,
            "system": UCUM_SYSTEM,
            "code": unit,
        },
    }


def blood_pressure_observation(
    observation_id: str,
    patient_id: str,
    systolic: int,
    diastolic: int,
    effective: str,
) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": observation_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure panel with all children optional",
                },
                {"system": LAB_SYSTEM, "code": "BP", "display": "Blood pressure"},
            ],
            "text": "BP",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": effective,
        "component": [
            {
                "code": {
                    "coding": [
                        {"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}
                    ],
                    "text": "Systolic blood pressure",
                },
                "valueQuantity": {"value": systolic, "unit": "mmHg", "system": UCUM_SYSTEM, "code": "mm[Hg]"},
            },
            {
                "code": {
                    "coding": [
                        {"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}
                    ],
                    "text": "Diastolic blood pressure",
                },
                "valueQuantity": {"value": diastolic, "unit": "mmHg", "system": UCUM_SYSTEM, "code": "mm[Hg]"},
            },
        ],
    }


def medication_request(
    request_id: str,
    patient_id: str,
    medication: str,
    authored_on: str,
    status: str = "active",
) -> dict[str, Any]:
    return {
        "resourceType": "MedicationRequest",
        "id": request_id,
        "status": status,
        "intent": "order",
        "medicationCodeableConcept": {"text": medication},
        "subject": {"reference": f"Patient/{patient_id}"},
        "authoredOn": authored_on,
    }


def service_request(
    request_id: str,
    patient_id: str,
    code: str,
    display: str,
    authored_on: str,
    note: str | None = None,
) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "ServiceRequest",
        "id": request_id,
        "status": "active",
        "intent": "order",
        "code": {
            "coding": [{"system": "http://snomed.info/sct", "code": code, "display": display}],
            "text": display,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "authoredOn": authored_on,
    }
    if note:
        resource["note"] = [{"text": note}]
    return resource


def diagnostic_report(
    report_id: str,
    patient_id: str,
    text: str,
    effective: str,
) -> dict[str, Any]:
    return {
        "resourceType": "DiagnosticReport",
        "id": report_id,
        "status": "final",
        "code": {"text": "Left knee MRI report"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": effective,
        "conclusion": text,
    }


def build_bundle() -> dict[str, Any]:
    resources: list[dict[str, Any]] = [
        patient("sara-demo-patient", "SARA1001", "Amina", "Yusuf", "1974-04-12", "female"),
        condition("sara-demo-cond-diabetes", "sara-demo-patient", "Type 2 diabetes mellitus", "2025-01-20", "44054006"),
        condition("sara-demo-cond-hypertension", "sara-demo-patient", "Hypertension", "2024-08-14", "38341003"),
        lab_observation("sara-demo-mg-low", "sara-demo-patient", "MG", "Magnesium", "2601-3", 1.3, "mg/dL", "2026-06-05T06:00:00+00:00"),
        lab_observation("sara-demo-k-low", "sara-demo-patient", "K", "Potassium", "2823-3", 3.2, "mEq/L", "2026-06-05T05:30:00+00:00"),
        lab_observation("sara-demo-glu-1", "sara-demo-patient", "GLU", "Blood glucose", "2339-0", 144, "mg/dL", "2026-06-05T04:00:00+00:00"),
        lab_observation("sara-demo-glu-2", "sara-demo-patient", "GLU", "Blood glucose", "2339-0", 118, "mg/dL", "2026-06-04T21:00:00+00:00"),
        lab_observation("sara-demo-a1c-old", "sara-demo-patient", "A1C", "Hemoglobin A1C", "4548-4", 8.2, "%", "2024-11-12T09:30:00+00:00"),
        medication_request("sara-demo-med-metformin", "sara-demo-patient", "Metformin 500 mg tablet", "2026-03-10"),
        patient("S2874099", "S2874099", "Peter", "Stafford", "1932-12-29", "male"),
        condition("S2874099-cond-afib", "S2874099", "Atrial fibrillation", "2021-06-18", "49436004"),
        medication_request("S2874099-med-apixaban", "S2874099", "Apixaban 5 mg tablet", "2023-08-01"),
        patient("S2380121", "S2380121", "Lena", "Morrison", "1968-05-21", "female"),
        condition("S2380121-cond-htn", "S2380121", "Hypertension", "2020-03-12", "38341003"),
        blood_pressure_observation("S2380121-bp-20231113", "S2380121", 118, 77, "2023-11-13T10:15:00+00:00"),
        patient("S3032536", "S3032536", "Grace", "Owens", "1955-02-18", "female"),
        condition("S3032536-cond-ckd", "S3032536", "Chronic kidney disease stage 3", "2022-04-02", "433144002"),
        lab_observation("S3032536-mg-recent", "S3032536", "MG", "Magnesium", "2601-3", 1.8, "mg/dL", "2023-11-13T08:20:00+00:00"),
        lab_observation("S3032536-mg-older", "S3032536", "MG", "Magnesium", "2601-3", 1.6, "mg/dL", "2023-11-11T08:20:00+00:00"),
        patient("S3084624", "S3084624", "Martin", "Kim", "1971-07-03", "male"),
        condition("S3084624-cond-hypomag", "S3084624", "Hypomagnesemia", "2023-11-12", "190855004"),
        lab_observation("S3084624-mg-low", "S3084624", "MG", "Magnesium", "2601-3", 1.2, "mg/dL", "2023-11-13T05:45:00+00:00"),
        patient("S6307599", "S6307599", "Elaine", "Baker", "1984-10-09", "female"),
        condition("S6307599-cond-diabetes", "S6307599", "Type 2 diabetes mellitus", "2022-09-22", "44054006"),
        lab_observation("S6307599-glu-1", "S6307599", "GLU", "Blood glucose", "2339-0", 164, "mg/dL", "2023-11-13T08:00:00+00:00"),
        lab_observation("S6307599-glu-2", "S6307599", "GLU", "Blood glucose", "2339-0", 148, "mg/dL", "2023-11-13T02:30:00+00:00"),
        lab_observation("S6307599-glu-3", "S6307599", "GLU", "Blood glucose", "2339-0", 132, "mg/dL", "2023-11-12T18:00:00+00:00"),
        lab_observation("S6307599-glu-old", "S6307599", "GLU", "Blood glucose", "2339-0", 210, "mg/dL", "2023-11-10T08:00:00+00:00"),
        patient("S2197736", "S2197736", "Victor", "Nguyen", "1979-03-14", "male"),
        condition("S2197736-cond-diabetes", "S2197736", "Diabetes mellitus", "2019-05-03", "73211009"),
        lab_observation("S2197736-glu-recent", "S2197736", "GLU", "Blood glucose", "2339-0", 202, "mg/dL", "2023-11-13T09:40:00+00:00"),
        lab_observation("S2197736-glu-older", "S2197736", "GLU", "Blood glucose", "2339-0", 176, "mg/dL", "2023-11-12T19:15:00+00:00"),
        patient("S2016972", "S2016972", "Nora", "Patel", "1992-01-30", "female"),
        condition("S2016972-cond-acl", "S2016972", "Left anterior cruciate ligament tear grade II", "2023-11-13", "239725005"),
        diagnostic_report("S2016972-rad-knee", "S2016972", "Radiology report indicates ACL tear, grade II.", "2023-11-13T09:00:00+00:00"),
        service_request(
            "S2016972-ortho-referral",
            "S2016972",
            "306181000000106",
            "Referral to orthopedic surgery service",
            "2023-11-13T10:15:00+00:00",
            "Situation: acute left knee injury, Background: radiology report indicates ACL tear. Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to evaluate and provide management recommendations.",
        ),
        patient("S3241217", "S3241217", "Caleb", "Johnson", "1961-12-04", "male"),
        condition("S3241217-cond-hypokalemia", "S3241217", "Hypokalemia", "2023-11-13", "43339004"),
        lab_observation("S3241217-k-low", "S3241217", "K", "Potassium", "2823-3", 3.2, "mEq/L", "2023-11-13T06:10:00+00:00"),
        service_request("S3241217-k-follow-up", "S3241217", "2823-3", "Serum potassium level", "2023-11-13T10:15:00+00:00", "Morning serum potassium level next day at 08:00."),
        patient("S1311412", "S1311412", "Iris", "Morgan", "1976-06-26", "female"),
        condition("S1311412-cond-diabetes", "S1311412", "Type 2 diabetes mellitus", "2020-02-10", "44054006"),
        lab_observation("S1311412-a1c-old", "S1311412", "A1C", "Hemoglobin A1C", "4548-4", 8.6, "%", "2022-09-01T11:00:00+00:00"),
        service_request("S1311412-a1c-order", "S1311412", "4548-4", "Hemoglobin A1C lab test", "2023-11-13T10:15:00+00:00", "A1C result is more than one year old."),
    ]

    return {
        "resourceType": "Bundle",
        "id": "sara-demo-patient-bundle",
        "type": "transaction",
        "entry": [transaction_entry(resource) for resource in resources],
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / "data" / "iris-fhir" / "sara-demo-patient-bundle.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(build_bundle(), indent=2) + "\n")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
