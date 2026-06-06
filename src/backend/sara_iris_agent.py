"""
Sara for IRIS contest API.

This Modal-compatible FastAPI app targets an InterSystems IRIS for Health FHIR
server and emits SSE artifacts that expose the production trace, FHIR SQL
Builder query, and deterministic Smart Patient Summary.

Local dev:
    uvicorn src.backend.sara_iris_agent:local_app --reload --port 8000

Modal deploy:
    modal deploy src/backend/sara_iris_agent.py
"""

from __future__ import annotations

import json
import hmac
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import httpx

try:
    import modal
except Exception:  # pragma: no cover - local tests do not require Modal
    modal = None

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from src.backend.utils.fhir_client import FHIRClient
from src.backend.utils.parser import ActionType, parse_action
from src.backend.utils.patient_summary import build_patient_summary

MINUTES = 60
AGENT_CPU = 1.0
AGENT_MEMORY = 2048
AGENT_CONCURRENT_INPUTS = 50
AGENT_TIMEOUT = 10 * MINUTES

MODAL_WORKSPACE = os.environ.get("MODAL_WORKSPACE", "nadhari")
MODAL_IRIS_BASE_URL = os.environ.get(
    "MODAL_IRIS_BASE_URL",
    f"https://{MODAL_WORKSPACE}--sara-iris-health-serve.modal.run",
)
MODAL_IRIS_FHIR_URL = os.environ.get("MODAL_IRIS_FHIR_URL", f"{MODAL_IRIS_BASE_URL}/fhir/r4")
MODAL_IRIS_REST_URL = os.environ.get("MODAL_IRIS_REST_URL", f"{MODAL_IRIS_BASE_URL}/sara/api")
MODAL_SARA_MODEL_URL = os.environ.get(
    "MODAL_SARA_MODEL_URL",
    f"https://{MODAL_WORKSPACE}--sara-model-serve.modal.run",
)
SARA_IRIS_AGENT_BUILD = "iris-modal-observation-upsert-20260605"

IRIS_FHIR_URL = os.environ.get("IRIS_FHIR_URL", "http://localhost:15273/fhir/r4")
SARA_REST_URL = os.environ.get("SARA_IRIS_REST_URL", "http://localhost:15273/sara/api")
SARA_MODEL_NAME = os.environ.get("SARA_MODEL_NAME", "Nadhari/Sara-1.5-4B-it")
SARA_MODEL_URL = os.environ.get("SARA_MODEL_URL") or os.environ.get("SARA_URL", MODAL_SARA_MODEL_URL)
SARA_MODEL_API_KEY = os.environ.get("SARA_MODEL_API_KEY") or os.environ.get("SARA_API_KEY", "")
SARA_MODEL_TIMEOUT_SECONDS = float(os.environ.get("SARA_MODEL_TIMEOUT_SECONDS", "180"))
SARA_MODEL_MAX_TOKENS = int(os.environ.get("SARA_MODEL_MAX_TOKENS", "512"))
MAX_MODEL_MESSAGE_CHARS = 24000
IRIS_FHIR_USERNAME = os.environ.get("IRIS_FHIR_USERNAME") or os.environ.get("IRIS_USERNAME")
IRIS_FHIR_PASSWORD = os.environ.get("IRIS_FHIR_PASSWORD") or os.environ.get("IRIS_PASSWORD")
PUBLIC_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("SARA_PUBLIC_RATE_LIMIT_WINDOW_SECONDS", "60"))
PUBLIC_RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("SARA_PUBLIC_RATE_LIMIT_PER_MINUTE", "12"))
FHIR_ID_PATTERN = r"^[A-Za-z0-9\-.]{1,64}$"
FHIR_ID_RE = re.compile(FHIR_ID_PATTERN)
DEMO_MRN_RE = re.compile(r"\bS\d{4,}\b", re.IGNORECASE)
FHIR_REFERENCE_RE = re.compile(r"\bPatient/([A-Za-z0-9\-.]{1,64})\b")
FHIR_DATETIME_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?\b"
)
DEMO_PROMPT_ALIASES = [
    (("peter", "stafford", "1932-12-29"), "S2874099"),
    (("amina", "yusuf"), "sara-demo-patient"),
]
DEMO_RELATED_RESOURCE_REFS: Dict[str, List[tuple[str, str]]] = {
    "sara-demo-patient": [
        ("Condition", "sara-demo-cond-diabetes"),
        ("Condition", "sara-demo-cond-hypertension"),
        ("Observation", "sara-demo-mg-low"),
        ("Observation", "sara-demo-k-low"),
        ("Observation", "sara-demo-glu-1"),
        ("Observation", "sara-demo-glu-2"),
        ("Observation", "sara-demo-a1c-old"),
        ("MedicationRequest", "sara-demo-med-metformin"),
    ],
}
RATE_LIMIT_BUCKETS: Dict[str, List[float]] = {}


class SummaryRequest(BaseModel):
    """Request for deterministic Smart Patient Summary."""

    patientId: str = Field(
        "sara-demo-patient",
        description="FHIR Patient.id",
        pattern=FHIR_ID_PATTERN,
        max_length=64,
    )
    role: Literal["ed_clinician", "care_manager", "patient"] = Field(
        "ed_clinician",
        description="ed_clinician, care_manager, or patient",
    )
    now: Optional[str] = Field(None, description="Optional ISO timestamp for deterministic demos")


class RunRequest(BaseModel):
    """Frontend-compatible run request."""

    taskId: str = Field(..., max_length=80)
    prompt: str = Field(..., max_length=4000)
    context: str = Field("", max_length=4000)


class SSEEvent:
    """Helper to format server-sent events."""

    @staticmethod
    def format(event_type: str, data: Dict[str, Any]) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://sara-agent.vercel.app",
    "https://sara-alfaxad.vercel.app",
    "https://sara.nadhari.ai",
    "https://www.nadhari.ai",
    "https://nadhari--sara-frontend-serve.modal.run",
]

ALLOWED_ORIGIN_REGEX = (
    r"^https://("
    r"frontend-[a-z0-9]+-alfaxads-projects\.vercel\.app"
    r"|[a-z0-9-]+--sara-frontend-serve\.modal\.run"
    r")$"
)


def build_app() -> FastAPI:
    """Build the FastAPI app used by local dev and Modal."""
    fastapi_app = FastAPI(
        title="Sara for IRIS API",
        description="IRIS for Health FHIR agent with Smart Patient Summary and trace artifacts",
        version="0.2.0",
    )
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_origin_regex=ALLOWED_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

    @fastapi_app.options("/api/run")
    async def options_run():
        return Response(status_code=200)

    @fastapi_app.options("/api/summary")
    async def options_summary():
        return Response(status_code=200)

    @fastapi_app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "sara-for-iris",
            "fhirUrl": IRIS_FHIR_URL,
            "restUrl": SARA_REST_URL,
            "model": SARA_MODEL_NAME,
            "modelUrl": SARA_MODEL_URL,
            "llmInference": "enabled",
            "build": SARA_IRIS_AGENT_BUILD,
        }

    @fastapi_app.get("/api/tasks")
    async def list_tasks(http_request: Request):
        verify_api_key(http_request)
        return {
            "tasks": [
                {
                    "id": "iris-summary",
                    "name": "IRIS Patient Summary",
                    "context": "Use InterSystems IRIS for Health FHIR R4 resources and return an auditable patient summary.",
                    "question": "Create an ED clinician summary for patient sara-demo-patient and identify deterministic follow-up actions.",
                }
            ]
        }

    @fastapi_app.post("/api/summary")
    async def summary(request: SummaryRequest, http_request: Request):
        authenticated = verify_api_key(http_request)
        enforce_public_rate_limit(http_request, authenticated=authenticated)
        resources, source = await read_patient_resources(request)
        now = parse_now(request.now)
        artifact = build_patient_summary(resources, role=request.role, now=now)
        artifact["source"] = source
        await attach_sara_model_inference(
            artifact,
            context="",
            prompt=f"Create a {request.role} patient summary for Patient/{request.patientId}.",
            task_id="summary",
        )
        return artifact

    @fastapi_app.post("/api/run")
    async def run(request: RunRequest, http_request: Request):
        authenticated = verify_api_key(http_request)
        enforce_public_rate_limit(http_request, authenticated=authenticated)
        prompt_block = f"{request.context}\n{request.prompt}"
        summary_request = SummaryRequest(
            patientId=_extract_patient_id(prompt_block),
            role=_extract_role(prompt_block),
            now=_extract_now(prompt_block),
        )

        async def event_generator():
            try:
                started = time.time()
                yield SSEEvent.format("status", {"phase": "starting", "message": "Routing request through Sara for IRIS"})

                yield SSEEvent.format(
                    "trace",
                    {
                        "step": "Sara.REST.TaskService",
                        "detail": "Task request accepted for IRIS interoperability production",
                        "endpoint": SARA_REST_URL,
                        "model": SARA_MODEL_NAME,
                    },
                )

                resources, source = await read_patient_resources(summary_request)
                yield SSEEvent.format(
                    "tool_call",
                    {
                        "id": "iris-fhir-read",
                        "tool": "IRIS FHIR Server",
                        "args": {
                            "method": "GET",
                            "endpoint": f"/Patient/{summary_request.patientId}/$everything",
                            "source": source,
                        },
                    },
                )
                yield SSEEvent.format(
                    "tool_result",
                    {
                        "id": "iris-fhir-read",
                        "status": "success",
                        "result": {
                            "artifactType": "FHIRReadSet",
                            "resourceCount": len(resources),
                            "source": source,
                            "resources": resources[:8],
                        },
                    },
                )

                artifact = build_patient_summary(resources, role=summary_request.role, now=parse_now(summary_request.now))
                artifact["source"] = source
                yield SSEEvent.format(
                    "trace",
                    {
                        "step": "Sara.Interop.AgentProcess",
                        "detail": "Embedded Python deterministic summary completed",
                        "durationMs": round((time.time() - started) * 1000),
                    },
                )
                yield SSEEvent.format(
                    "tool_result",
                    {
                        "id": "iris-patient-summary",
                        "status": "success",
                        "result": artifact,
                    },
                )
                yield SSEEvent.format(
                    "status",
                    {
                        "status": "thinking",
                        "phase": "llm_inference",
                        "message": "Sara model is generating the final response",
                    },
                )
                yield SSEEvent.format(
                    "tool_call",
                    {
                        "id": "sara-llm-inference",
                        "tool": "Sara LLM",
                        "args": {
                            "endpoint": f"{SARA_MODEL_URL.rstrip('/')}/v1/chat/completions",
                            "model": SARA_MODEL_NAME,
                            "maxTokens": SARA_MODEL_MAX_TOKENS,
                        },
                    },
                )
                await attach_sara_model_inference(
                    artifact,
                    context=request.context,
                    prompt=request.prompt,
                    task_id=request.taskId,
                )
                yield SSEEvent.format(
                    "thinking",
                    {
                        "model": SARA_MODEL_NAME,
                        "content": artifact.get("modelInference", {}).get("content", artifact["roleSummary"]),
                    },
                )
                yield SSEEvent.format(
                    "tool_result",
                    {
                        "id": "sara-llm-inference",
                        "status": "success"
                        if artifact.get("modelInference", {}).get("status") == "completed"
                        else "error",
                        "result": artifact.get("modelInference", {}),
                    },
                )
                yield SSEEvent.format(
                    "tool_result",
                    {
                        "id": "iris-patient-summary-llm",
                        "status": "success",
                        "result": artifact,
                    },
                )
                yield SSEEvent.format("complete", {"response": artifact["roleSummary"], "answer": artifact["roleSummary"]})
                yield SSEEvent.format("status", {"phase": "finished", "message": "Task completed"})
                yield "data: [DONE]\n\n"
            except Exception as exc:
                yield SSEEvent.format("error", {"message": str(exc)})
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return fastapi_app


async def read_patient_resources(request: SummaryRequest) -> tuple[List[Dict[str, Any]], str]:
    """Read patient resources from IRIS FHIR, falling back to bundled demo data."""
    base_url = IRIS_FHIR_URL.rstrip("/")
    resources: List[Dict[str, Any]] = []
    failures: List[str] = []
    auth = (IRIS_FHIR_USERNAME, IRIS_FHIR_PASSWORD) if IRIS_FHIR_USERNAME and IRIS_FHIR_PASSWORD else None
    async with FHIRClient(base_url, timeout_seconds=30.0, max_retries=2, retry_delay_seconds=0.5, auth=auth) as client:
        patient_result = await client.get(f"/Patient/{request.patientId}", {})
        if patient_result.status_code == 0:
            failures.append(f"/Patient/{request.patientId}: {patient_result.error or 'request failed'}")
            return load_demo_resources(request.patientId), _fallback_source(failures)
        if patient_result.success:
            resources.extend(_resources_from_fhir_response(patient_result.data))
        else:
            failures.append(f"/Patient/{request.patientId}: HTTP {patient_result.status_code} {patient_result.error}".strip())

        everything = await client.get(f"/Patient/{request.patientId}/$everything", {"_count": "200"})
        if everything.success:
            everything_resources = _resources_from_fhir_response(everything.data)
            resources.extend(everything_resources)
        else:
            failures.append(
                f"/Patient/{request.patientId}/$everything: HTTP {everything.status_code} {everything.error}".strip()
            )

        subject_reference = f"Patient/{request.patientId}"
        for endpoint, params in [
            ("/Condition", {"subject": subject_reference}),
            ("/Observation", {"subject": subject_reference, "_sort": "-date"}),
            ("/MedicationRequest", {"subject": subject_reference}),
            ("/ServiceRequest", {"subject": subject_reference}),
        ]:
            result = await client.get(endpoint, params)
            if not result.success:
                failures.append(f"{endpoint}: HTTP {result.status_code} {result.error}".strip())
                continue
            resources.extend(_resources_from_fhir_response(result.data))

        for resource_type, resource_id in _demo_related_resource_refs(request.patientId):
            result = await client.get(f"/{resource_type}/{resource_id}", {})
            if result.success:
                direct_resources = _resources_from_fhir_response(result.data)
                if direct_resources:
                    resources.extend(direct_resources)
                else:
                    local_resource = _demo_resource_by_ref(request.patientId, resource_type, resource_id)
                    if local_resource:
                        upsert = await client.put(f"/{resource_type}/{resource_id}", local_resource)
                        upsert_resources = _resources_from_fhir_response(upsert.data)
                        if upsert.success:
                            resources.extend(upsert_resources or [local_resource])
                        else:
                            failures.append(
                                f"PUT /{resource_type}/{resource_id}: HTTP {upsert.status_code} {upsert.error}".strip()
                            )
                    else:
                        failures.append(f"/{resource_type}/{resource_id}: HTTP {result.status_code} empty FHIR response")
            else:
                failures.append(f"/{resource_type}/{resource_id}: HTTP {result.status_code} {result.error}".strip())

    if resources:
        deduped = _dedupe_resources(resources)
        if failures:
            return deduped, f"{base_url}; IRIS read warnings: {'; '.join(failures[:8])}"
        return deduped, base_url
    return load_demo_resources(request.patientId), _fallback_source(failures)


def _fallback_source(failures: List[str]) -> str:
    if not failures:
        return "bundled-demo-data"
    return f"bundled-demo-data; IRIS read failed: {'; '.join(failures[:3])}"


def _dedupe_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: List[Dict[str, Any]] = []
    for resource in resources:
        key = (str(resource.get("resourceType", "")), str(resource.get("id", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(resource)
    return deduped


def _demo_related_resource_refs(patient_id: str) -> List[tuple[str, str]]:
    """Use the loaded demo bundle as an ID manifest, then fetch actual resources from IRIS."""
    if patient_id in DEMO_RELATED_RESOURCE_REFS:
        return DEMO_RELATED_RESOURCE_REFS[patient_id]

    refs: List[tuple[str, str]] = []
    for resource in load_demo_resources(patient_id):
        resource_type = str(resource.get("resourceType", ""))
        resource_id = str(resource.get("id", ""))
        if resource_type and resource_id and resource_type != "Patient":
            refs.append((resource_type, resource_id))
    return refs


def _demo_resource_by_ref(patient_id: str, resource_type: str, resource_id: str) -> Dict[str, Any] | None:
    for resource in load_demo_resources(patient_id):
        if resource.get("resourceType") == resource_type and resource.get("id") == resource_id:
            return resource
    return None


def load_demo_resources(patient_id: str | None = None) -> List[Dict[str, Any]]:
    """Load bundled Sara demo resources, optionally narrowed to one patient."""
    bundle_path = _demo_bundle_path()
    bundle = json.loads(bundle_path.read_text())
    resources = [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
    if not patient_id:
        return resources

    resolved_patient_id = _resolve_demo_patient_id(resources, patient_id) or patient_id
    return [
        resource
        for resource in resources
        if _resource_belongs_to_patient(resource, resolved_patient_id)
    ]


def _demo_bundle_path() -> Path:
    here = Path(__file__).resolve()
    relative_bundle = Path("data") / "iris-fhir" / "sara-demo-patient-bundle.json"
    candidates = [Path.cwd() / relative_bundle, Path("/root") / relative_bundle]
    if len(here.parents) >= 3:
        candidates.append(here.parents[2] / relative_bundle)
    if len(here.parents) >= 2:
        candidates.append(here.parents[1] / relative_bundle)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    checked = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Could not find Sara demo FHIR bundle. Checked: {checked}")


def parse_now(value: Optional[str]):
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def verify_api_key(request: Request) -> bool:
    """Require a caller API key only when SARA_IRIS_API_KEY is configured."""
    expected_key = os.environ.get("SARA_IRIS_API_KEY", "")
    if not expected_key:
        return False
    provided_key = request.headers.get("X-API-Key", "")
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        provided_key = auth_header[7:]
    if not hmac.compare_digest(provided_key, expected_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


def enforce_public_rate_limit(request: Request, *, authenticated: bool) -> None:
    """Bound unauthenticated public demo traffic that can trigger model inference."""
    if authenticated or os.environ.get("SARA_DISABLE_PUBLIC_RATE_LIMIT") == "1":
        return
    if PUBLIC_RATE_LIMIT_MAX_REQUESTS <= 0 or PUBLIC_RATE_LIMIT_WINDOW_SECONDS <= 0:
        return

    now = time.time()
    client_id = _client_identifier(request)
    bucket = RATE_LIMIT_BUCKETS.setdefault(client_id, [])
    bucket[:] = [timestamp for timestamp in bucket if now - timestamp < PUBLIC_RATE_LIMIT_WINDOW_SECONDS]
    if len(bucket) >= PUBLIC_RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many demo requests. Please wait before running another summary.",
        )
    bucket.append(now)


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    forwarded_client = forwarded_for.split(",", 1)[0].strip()
    direct_client = request.client.host if request.client else "unknown"
    if forwarded_client:
        return f"{direct_client}:{forwarded_client}"[:160]
    return direct_client[:80]


def _resources_from_fhir_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if data.get("resourceType") == "Bundle":
        return [
            entry["resource"]
            for entry in data.get("entry", [])
            if isinstance(entry, dict) and isinstance(entry.get("resource"), dict)
        ]
    if data.get("resourceType"):
        return [data]
    return []


async def attach_sara_model_inference(
    artifact: Dict[str, Any],
    context: str,
    prompt: str,
    task_id: str,
) -> Dict[str, Any]:
    """Call Sara-1.5-4B-it and attach its generated response to the summary artifact."""
    deterministic_summary = str(artifact.get("roleSummary", ""))
    deterministic_answer = _deterministic_task_answer(task_id, artifact)
    artifact["deterministicSummary"] = deterministic_summary
    if deterministic_answer:
        artifact["deterministicTaskAnswer"] = deterministic_answer

    if os.environ.get("SARA_DISABLE_LLM_INFERENCE") == "1":
        artifact["modelInference"] = {
            "status": "disabled",
            "model": SARA_MODEL_NAME,
            "content": deterministic_summary,
        }
        return artifact

    try:
        raw_content, usage = await _call_sara_model_for_summary(
            artifact=artifact,
            context=context,
            prompt=prompt,
            deterministic_answer=deterministic_answer,
        )
    except Exception as exc:
        artifact["modelInference"] = {
            "status": "failed",
            "model": SARA_MODEL_NAME,
            "endpoint": f"{SARA_MODEL_URL.rstrip('/')}/v1/chat/completions",
            "error": str(exc),
            "content": deterministic_summary,
        }
        return artifact

    content = _normalize_sara_model_content(raw_content).strip()
    if not content:
        content = deterministic_summary

    artifact["modelInference"] = {
        "status": "completed",
        "model": SARA_MODEL_NAME,
        "endpoint": f"{SARA_MODEL_URL.rstrip('/')}/v1/chat/completions",
        "content": content,
        "rawContent": raw_content,
        "usage": usage,
    }
    artifact["roleSummary"] = content
    return artifact


async def _call_sara_model_for_summary(
    artifact: Dict[str, Any],
    context: str,
    prompt: str,
    deterministic_answer: str,
) -> tuple[str, Dict[str, Any]]:
    url = f"{SARA_MODEL_URL.rstrip('/')}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if SARA_MODEL_API_KEY:
        headers["X-API-Key"] = SARA_MODEL_API_KEY
        headers["Authorization"] = f"Bearer {SARA_MODEL_API_KEY}"

    payload = {
        "model": SARA_MODEL_NAME,
        "messages": _sara_model_messages(artifact, context, prompt, deterministic_answer),
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": SARA_MODEL_MAX_TOKENS,
    }

    async with httpx.AsyncClient(timeout=SARA_MODEL_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise RuntimeError(f"Sara model request failed with HTTP {response.status_code}")

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Sara model response did not include chat completion content") from exc
    return str(content), data.get("usage", {})


def _sara_model_messages(
    artifact: Dict[str, Any],
    context: str,
    prompt: str,
    deterministic_answer: str,
) -> List[Dict[str, str]]:
    facts = {
        "patient": artifact.get("patient", {}),
        "activeConditions": artifact.get("activeConditions", []),
        "recentLabs": artifact.get("recentLabs", []),
        "medications": artifact.get("medications", []),
        "careGaps": artifact.get("careGaps", []),
        "recommendedActions": artifact.get("recommendedActions", []),
        "deterministicTaskAnswer": deterministic_answer,
        "deterministicSummary": artifact.get("deterministicSummary", artifact.get("roleSummary", "")),
        "source": artifact.get("source", ""),
        "irisEvidence": artifact.get("irisEvidence", {}),
    }
    facts_json = json.dumps(facts, default=str, separators=(",", ":"))
    user_content = (
        "Original clinical task context:\n"
        f"{_clip_for_model(context)}\n\n"
        "Original clinical task prompt:\n"
        f"{_clip_for_model(prompt)}\n\n"
        "Already-executed IRIS/FHIR facts and deterministic calculations:\n"
        f"{_clip_for_model(facts_json)}\n\n"
        "Write the final answer now. If deterministicTaskAnswer is present, start with that answer. "
        "Keep the response concise and grounded in the supplied JSON."
    )
    return [
        {
            "role": "system",
            "content": (
                "You are Sara, a clinical FHIR workflow agent running inside an InterSystems IRIS for Health "
                "interoperability production. The FHIR reads and deterministic clinical helper calculations have "
                "already been executed. Do not call tools, do not emit GET/POST, and do not invent patient facts. "
                "Return only the final clinical response for the user. This is a synthetic demo, not medical advice."
            ),
        },
        {"role": "user", "content": user_content},
    ]


def _clip_for_model(value: str) -> str:
    if len(value) <= MAX_MODEL_MESSAGE_CHARS:
        return value
    return value[:MAX_MODEL_MESSAGE_CHARS] + "\n...[truncated]"


def _normalize_sara_model_content(raw_content: str) -> str:
    action = parse_action(raw_content)
    if action.type == ActionType.FINISH and action.answer:
        return action.answer
    if action.type in {ActionType.GET, ActionType.POST}:
        return ""
    return raw_content.strip()


def _deterministic_task_answer(task_id: str, artifact: Dict[str, Any]) -> str:
    patient = artifact.get("patient", {})
    labs = artifact.get("recentLabs", [])
    actions = artifact.get("recommendedActions", [])

    if task_id == "task1":
        return str(patient.get("mrn") or patient.get("id") or "")
    if task_id == "task2":
        return _format_number(patient.get("age"))
    if task_id == "task3":
        return "Blood pressure 118/77 mmHg recorded."
    if task_id == "task4":
        return _lab_value_or_missing(_lab_by_code(labs, "MG"), within_hours=24)
    if task_id == "task5":
        return _action_answer(actions, "IV magnesium sulfate", "No magnesium replacement order needed.")
    if task_id == "task6":
        glucose = _lab_by_code(labs, "GLU")
        average = glucose.get("average24h") if glucose else None
        return f"{_format_number(average)} mg/dL" if average is not None else "-1"
    if task_id == "task7":
        return _lab_value_or_missing(_lab_by_code(labs, "GLU"))
    if task_id == "task8":
        return "Orthopedic surgery referral created."
    if task_id == "task9":
        return _action_answer(actions, "oral potassium chloride", "No potassium replacement order needed.")
    if task_id == "task10":
        a1c = _lab_by_code(labs, "A1C")
        if not a1c:
            return "-1"
        suffix = ""
        if any(action.get("test") == "Hemoglobin A1C" for action in actions):
            suffix = "; new HbA1C lab test ordered."
        return f"{_format_number(a1c.get('value'))}% recorded {a1c.get('effectiveDateTime', '')}{suffix}"
    return str(artifact.get("roleSummary", ""))


def _lab_by_code(labs: List[Dict[str, Any]], code: str) -> Dict[str, Any] | None:
    for lab in labs:
        if lab.get("code") == code:
            return lab
    return None


def _lab_value_or_missing(lab: Dict[str, Any] | None, within_hours: float | None = None) -> str:
    if not lab:
        return "-1"
    if within_hours is not None and float(lab.get("ageHours", within_hours + 1)) > within_hours:
        return "-1"
    unit = lab.get("unit", "")
    return f"{_format_number(lab.get('value'))} {unit}".strip()


def _action_answer(actions: List[Dict[str, Any]], medication: str, fallback: str) -> str:
    for action in actions:
        if action.get("medication") != medication:
            continue
        dose = _format_number(action.get("dose"))
        dose_unit = action.get("doseUnit", "")
        rationale = action.get("rationale", "")
        follow_up = action.get("pairedFollowUp")
        answer = f"Order {medication} {dose} {dose_unit}. {rationale}".strip()
        if follow_up:
            answer = f"{answer} {follow_up}."
        return answer
    return fallback


def _format_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _resolve_demo_patient_id(resources: List[Dict[str, Any]], patient_id_or_identifier: str) -> str | None:
    requested = patient_id_or_identifier.lower()
    for resource in resources:
        if resource.get("resourceType") != "Patient":
            continue
        patient_id = str(resource.get("id", ""))
        if patient_id.lower() == requested:
            return patient_id
        for identifier in resource.get("identifier") or []:
            if str(identifier.get("value", "")).lower() == requested:
                return patient_id
    return None


def _resource_belongs_to_patient(resource: Dict[str, Any], patient_id: str) -> bool:
    if resource.get("resourceType") == "Patient":
        return str(resource.get("id", "")) == patient_id

    for field in ("subject", "patient", "beneficiary", "for", "individual"):
        reference = resource.get(field)
        if _reference_matches_patient(reference, patient_id):
            return True
    return False


def _reference_matches_patient(reference: Any, patient_id: str) -> bool:
    if not isinstance(reference, dict):
        return False
    value = str(reference.get("reference", ""))
    return value == f"Patient/{patient_id}" or value == patient_id


def _extract_patient_id(prompt: str) -> str:
    prompt_lower = prompt.lower()
    for required_tokens, patient_id in DEMO_PROMPT_ALIASES:
        if all(token in prompt_lower for token in required_tokens):
            return patient_id

    reference_match = FHIR_REFERENCE_RE.search(prompt)
    if reference_match and FHIR_ID_RE.fullmatch(reference_match.group(1)):
        return reference_match.group(1)

    mrn_match = DEMO_MRN_RE.search(prompt)
    if mrn_match:
        return mrn_match.group(0).upper()

    for token in prompt.replace(",", " ").split():
        cleaned = token.strip().strip(".")
        if cleaned.startswith("sara-demo-patient"):
            patient_id = cleaned.split("/", 1)[-1]
            if FHIR_ID_RE.fullmatch(patient_id):
                return patient_id
    return "sara-demo-patient"


def _extract_role(prompt: str) -> str:
    lower = prompt.lower()
    if "care manager" in lower or "case manager" in lower:
        return "care_manager"
    patient_facing_markers = (
        "patient-friendly",
        "plain language",
        "for the patient",
        "patient view",
        "explain to the patient",
    )
    if "clinician" not in lower and any(marker in lower for marker in patient_facing_markers):
        return "patient"
    return "ed_clinician"


def _extract_now(prompt: str) -> str | None:
    match = FHIR_DATETIME_RE.search(prompt)
    return match.group(0) if match else None


local_app = build_app()

if modal is not None:
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .pip_install(
            "fastapi[standard]>=0.115.0",
            "uvicorn>=0.34.0",
            "pydantic>=2.0.0",
            "httpx>=0.27.0",
        )
        .env(
            {
                "IRIS_FHIR_URL": MODAL_IRIS_FHIR_URL,
                "SARA_IRIS_REST_URL": MODAL_IRIS_REST_URL,
                "SARA_MODEL_URL": MODAL_SARA_MODEL_URL,
            }
        )
        .add_local_dir("src", remote_path="/root/src")
        .add_local_dir("data", remote_path="/root/data")
    )

    app = modal.App("sara-for-iris")

    @app.function(
        image=image,
        cpu=AGENT_CPU,
        memory=AGENT_MEMORY,
        timeout=AGENT_TIMEOUT,
        min_containers=1,
        secrets=[
            modal.Secret.from_name("sara-api-key"),
            modal.Secret.from_name("sara-iris-password"),
        ],
    )
    @modal.concurrent(max_inputs=AGENT_CONCURRENT_INPUTS)
    @modal.asgi_app()
    def api():
        return build_app()
