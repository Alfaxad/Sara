"""
Embedded Python entrypoints called from Sara.Interop.AgentProcess.

The direct IRIS install copies this package into the namespace manager
directory. At runtime IRIS Embedded Python can import it and build the same
deterministic summary artifact used by the Modal/local API.
"""

from __future__ import annotations

import json
import os
from base64 import b64encode
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


def run_task_json(
    payload_json: str,
    patient_id: str = "sara-demo-patient",
    role: str = "ed_clinician",
    fhir_base: str | None = None,
    fhir_username: str | None = None,
    fhir_password: str | None = None,
) -> str:
    """Return a JSON summary payload for a Sara task request."""
    payload = _loads(payload_json)
    patient_id = payload.get("patientId") or patient_id or "sara-demo-patient"
    role = payload.get("role") or role or "ed_clinician"
    now = _parse_now(payload.get("now"))

    resources = []
    source = "bundled-demo-data"
    for base_url in _candidate_fhir_bases(fhir_base):
        resources = _read_patient_compartment(base_url, patient_id, fhir_username, fhir_password)
        if resources:
            source = base_url
            break
    if not resources:
        resources = _read_demo_bundle()
    summary = _build_summary(resources, role, now)
    if isinstance(summary, dict):
        summary["source"] = source
    return json.dumps(summary, separators=(",", ":"))


def _build_summary(resources: List[Dict[str, Any]], role: str, now):
    try:
        from src.backend.utils.patient_summary import build_patient_summary
    except Exception:
        from sara_iris.summary import build_patient_summary

    return build_patient_summary(resources, role=role, now=now)


def _read_patient_compartment(
    fhir_base: str,
    patient_id: str,
    fhir_username: str | None = None,
    fhir_password: str | None = None,
) -> List[Dict[str, Any]]:
    endpoints = [
        f"Patient/{patient_id}",
        "Condition?" + urlencode({"patient": patient_id}),
        "Observation?" + urlencode({"patient": patient_id, "_sort": "-date"}),
        "MedicationRequest?" + urlencode({"patient": patient_id}),
        "ServiceRequest?" + urlencode({"patient": patient_id}),
    ]
    resources: List[Dict[str, Any]] = []
    for endpoint in endpoints:
        data = _get_json(f"{fhir_base.rstrip('/')}/{endpoint}", fhir_username, fhir_password)
        if data.get("resourceType") == "Bundle":
            for entry in data.get("entry") or []:
                resource = entry.get("resource")
                if isinstance(resource, dict):
                    resources.append(resource)
        elif data:
            resources.append(data)

    return resources


def _candidate_fhir_bases(configured_base: str | None) -> List[str]:
    candidates = [
        configured_base,
        os.environ.get("IRIS_FHIR_URL"),
        "http://localhost:15273/fhir/r4",
        "http://localhost:52773/fhir/r4",
    ]
    seen = set()
    result = []
    for candidate in candidates:
        if not candidate:
            continue
        normalized = candidate.rstrip("/")
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _read_demo_bundle() -> List[Dict[str, Any]]:
    current = Path(__file__).resolve()
    candidates = []
    if len(current.parents) > 2:
        candidates.append(current.parents[2] / "sara-demo-fhir" / "sara-demo-patient-bundle.json")
    if len(current.parents) > 4:
        candidates.append(current.parents[4] / "data" / "iris-fhir" / "sara-demo-patient-bundle.json")

    for demo_path in candidates:
        if demo_path.exists():
            bundle = json.loads(demo_path.read_text())
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
    return []


def _get_json(url: str, fhir_username: str | None = None, fhir_password: str | None = None) -> Dict[str, Any]:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return {}
    headers = {"Accept": "application/fhir+json"}
    if fhir_username and fhir_password:
        token = b64encode(f"{fhir_username}:{fhir_password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=15) as response:  # nosec B310
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}


def _loads(payload_json: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(payload_json or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _parse_now(value: str | None):
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)
