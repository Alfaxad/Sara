from datetime import datetime, timezone

from fastapi import HTTPException
import pytest
from starlette.requests import Request

from src.backend.sara_iris_agent import (
    RATE_LIMIT_BUCKETS,
    _deterministic_task_answer,
    _extract_now,
    _extract_patient_id,
    _extract_role,
    _normalize_sara_model_content,
    attach_sara_model_inference,
    enforce_public_rate_limit,
    load_demo_resources,
    verify_api_key,
)
from src.backend.utils.patient_summary import build_patient_summary, iris_evidence


def _make_request(headers=None) -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/summary",
            "headers": raw_headers,
            "client": ("198.51.100.7", 443),
        }
    )


def test_extract_patient_id_from_old_sara_patient_lookup_prompt():
    prompt = 'What\'s the MRN of the patient with name Peter Stafford and DOB of 1932-12-29?'

    assert _extract_patient_id(prompt) == "S2874099"


def test_extract_patient_id_from_old_sara_mrn_prompt():
    prompt = "What's the most recent magnesium level of the patient S3032536 within last 24 hours?"

    assert _extract_patient_id(prompt) == "S3032536"


def test_extract_now_from_old_sara_context():
    context = "It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is \"MG\"."

    assert _extract_now(context) == "2023-11-13T10:15:00+00:00"


def test_extract_role_does_not_treat_old_task_patient_mentions_as_patient_facing():
    prompt = "What's the most recent magnesium level of the patient S3032536 within last 24 hours?"

    assert _extract_role(prompt) == "ed_clinician"


def test_load_demo_resources_filters_to_requested_patient():
    resources = load_demo_resources("S3032536")

    assert {resource["id"] for resource in resources} == {
        "S3032536",
        "S3032536-cond-ckd",
        "S3032536-mg-recent",
        "S3032536-mg-older",
    }


def test_old_sara_magnesium_task_triggers_deterministic_repletion():
    resources = load_demo_resources("S3084624")
    summary = build_patient_summary(
        resources,
        now=datetime(2023, 11, 13, 10, 15, tzinfo=timezone.utc),
    )

    assert summary["patient"]["id"] == "S3084624"
    assert summary["recentLabs"][0]["code"] == "MG"
    assert summary["recommendedActions"][0]["medication"] == "IV magnesium sulfate"
    assert summary["recommendedActions"][0]["dose"] == 2


def test_old_sara_average_glucose_uses_24_hour_window():
    resources = load_demo_resources("S6307599")
    summary = build_patient_summary(
        resources,
        now=datetime(2023, 11, 13, 10, 15, tzinfo=timezone.utc),
    )

    glucose = next(lab for lab in summary["recentLabs"] if lab["code"] == "GLU")
    assert glucose["average24h"] == 148


def test_deterministic_task_answer_for_old_sara_average_glucose():
    resources = load_demo_resources("S6307599")
    summary = build_patient_summary(
        resources,
        now=datetime(2023, 11, 13, 10, 15, tzinfo=timezone.utc),
    )

    assert _deterministic_task_answer("task6", summary) == "148 mg/dL"


def test_verify_api_key_requires_configured_iris_key(monkeypatch):
    monkeypatch.setenv("SARA_IRIS_API_KEY", "expected-demo-key")

    with pytest.raises(HTTPException) as missing:
        verify_api_key(_make_request())

    assert missing.value.status_code == 401
    assert verify_api_key(_make_request({"Authorization": "Bearer expected-demo-key"})) is True


def test_public_rate_limit_blocks_excess_unauthenticated_requests(monkeypatch):
    RATE_LIMIT_BUCKETS.clear()
    monkeypatch.delenv("SARA_DISABLE_PUBLIC_RATE_LIMIT", raising=False)
    monkeypatch.setattr("src.backend.sara_iris_agent.PUBLIC_RATE_LIMIT_MAX_REQUESTS", 2)
    monkeypatch.setattr("src.backend.sara_iris_agent.PUBLIC_RATE_LIMIT_WINDOW_SECONDS", 60)
    request = _make_request({"X-Forwarded-For": "203.0.113.20"})

    enforce_public_rate_limit(request, authenticated=False)
    enforce_public_rate_limit(request, authenticated=False)
    with pytest.raises(HTTPException) as blocked:
        enforce_public_rate_limit(request, authenticated=False)

    assert blocked.value.status_code == 429
    RATE_LIMIT_BUCKETS.clear()


def test_iris_sql_artifact_escapes_patient_id_literal():
    sql = iris_evidence("patient' OR '1'='1")["sqlBuilder"]["sql"]

    assert "patient'' OR ''1''=''1" in sql


def test_normalize_sara_model_finish_response():
    assert _normalize_sara_model_content('FINISH(["148 mg/dL"])') == "148 mg/dL"


@pytest.mark.asyncio
async def test_attach_sara_model_inference_replaces_role_summary(monkeypatch):
    async def fake_call(**kwargs):
        return "Sara generated final answer.", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    monkeypatch.setattr("src.backend.sara_iris_agent._call_sara_model_for_summary", fake_call)
    resources = load_demo_resources("S6307599")
    summary = build_patient_summary(
        resources,
        now=datetime(2023, 11, 13, 10, 15, tzinfo=timezone.utc),
    )

    await attach_sara_model_inference(
        summary,
        context="It's 2023-11-13T10:15:00+00:00 now. The code for CBG is GLU.",
        prompt="What is the average CBG of the patient S6307599 over the last 24 hours?",
        task_id="task6",
    )

    assert summary["deterministicTaskAnswer"] == "148 mg/dL"
    assert summary["deterministicSummary"]
    assert summary["roleSummary"] == "Sara generated final answer."
    assert summary["modelInference"]["status"] == "completed"
