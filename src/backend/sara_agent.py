# modal/sara_agent.py
# FastAPI endpoint for Sara Agent with SSE streaming
# Wraps the SaraAgent and deploys to Modal as a CPU-based function
#
# Run:   modal run modal/sara_agent.py
# Deploy: modal deploy modal/sara_agent.py

import modal

# --- Config values ---
MINUTES = 60
AGENT_CPU = 1.0
AGENT_MEMORY = 2048
AGENT_CONCURRENT_INPUTS = 50
AGENT_TIMEOUT = 10 * MINUTES

# Service URLs (can be overridden via environment variables)
# For production: use Modal-deployed FHIR server
# For development: use localhost:8080 (MedAgentBench Docker container)
import os
SARA_URL = os.environ.get("SARA_URL", "https://nadhari--sara-model-serve.modal.run")
FHIR_URL = os.environ.get("FHIR_URL", "https://nadhari--fhir-server-serve.modal.run/fhir")

# --- FHIR Functions (from MedAgentBench funcs_v1.json - exact copy) ---
FHIR_FUNCTIONS = [
    {"name": "GET {api_base}/Condition", "description": "Condition.Search (Problems) This web service retrieves problems from a patient's chart. This includes any data found in the patient's problem list across all encounters. This resource can be queried by a combination of patient ID and status.\n\nNote that this resource retrieves only data stored in problem list records. As a result, medical history data documented outside of a patient's problem list isn't available to applications using this service unless that data is retrieved using another method.\n\nThis resource does not return unconfirmed Condition resources in the \"holding tank\" that drives the EpicCare Reconcile Outside Data Activity. Note - once a clinician reconciles a problem, a new Condition resource associated with the reconciled problem will be available in the normal Condition.Search results.", "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "Always \"problem-list-item\" for this API."}, "patient": {"type": "string", "description": "Reference to a patient resource the condition is for."}}, "required": ["patient"]}},
    {"name": "GET {api_base}/Observation", "description": "Observation.Search (Labs) The Observation (Labs) resource returns component level data for lab results. ", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "The observation identifier (base name)."}, "date": {"type": "string", "description": "Date when the specimen was obtained."}, "patient": {"type": "string", "description": "Reference to a patient resource the condition is for."}}, "required": ["code", "patient"]}},
    {"name": "GET {api_base}/Observation", "description": "Observation.Search (Vitals) This web service will retrieve vital sign data from a patient's chart, as well as any other non-duplicable data found in the patient's flowsheets across all encounters.\n\nThis resource requires the use of encoded flowsheet IDs. Work with each organization to obtain encoded flowsheet IDs. Note that encoded flowsheet IDs will be different for each organization. Encoded flowsheet IDs are also different across production and non-production environments.", "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "Use \"vital-signs\" to search for vitals observations."}, "date": {"type": "string", "description": "The date range for when the observation was taken."}, "patient": {"type": "string", "description": "Reference to a patient resource the condition is for."}}, "required": ["category", "patient"]}},
    {"name": "POST {api_base}/Observation", "description": "Observation.Create (Vitals) The FHIR Observation.Create (Vitals) resource can file to all non-duplicable flowsheet rows, including vital signs. This resource can file vital signs for all flowsheets.", "parameters": {"type": "object", "properties": {"resourceType": {"type": "string", "description": "Use \"Observation\" for vitals observations."}, "category": {"type": "array", "items": {"type": "object", "properties": {"coding": {"type": "array", "items": {"type": "object", "properties": {"system": {"type": "string", "description": "Use \"http://hl7.org/fhir/observation-category\" "}, "code": {"type": "string", "description": "Use \"vital-signs\" "}, "display": {"type": "string", "description": "Use \"Vital Signs\" "}}}}}}}, "code": {"type": "object", "properties": {"text": {"type": "string", "description": "The flowsheet ID, encoded flowsheet ID, or LOINC codes to flowsheet mapping. What is being measured."}}}, "effectiveDateTime": {"type": "string", "description": "The date and time the observation was taken, in ISO format."}, "status": {"type": "string", "description": "The status of the observation. Only a value of \"final\" is supported. We do not support filing data that isn't finalized."}, "valueString": {"type": "string", "description": "Measurement value"}, "subject": {"type": "object", "properties": {"reference": {"type": "string", "description": "The patient FHIR ID for whom the observation is about."}}}}, "required": ["resourceType", "category", "code", "effectiveDateTime", "status", "valueString", "subject"]}},
    {"name": "GET {api_base}/MedicationRequest", "description": "MedicationRequest.Search (Signed Medication Order) You can use the search interaction to query for medication orders based on a patient and optionally status or category.\n\nThis resource can return various types of medications, including inpatient-ordered medications, clinic-administered medications (CAMS), patient-reported medications, and reconciled medications from Care Everywhere and other external sources.\n\nThe R4 version of this resource also returns patient-reported medications. Previously, patient-reported medications were not returned by the STU3 version of MedicationRequest and needed to be queried using the STU3 MedicationStatement resource. This is no longer the case. The R4 version of this resource returns patient-reported medications with the reportedBoolean element set to True. If the informant is known, it is also specified in the reportedReference element.", "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "The category of medication orders to search for. By default all categories are searched.\n\nSupported categories:\nInpatient\nOutpatient (those administered in the clinic - CAMS)\nCommunity (prescriptions)\nDischarge"}, "date": {"type": "string", "description": "The medication administration date. This parameter corresponds to the dosageInstruction.timing.repeat.boundsPeriod element. Medication orders that do not have start and end dates within the search parameter dates are filtered. If the environment supports multiple time zones, the search dates are adjusted one day in both directions, so more medications might be returned than expected. Use caution when filtering a medication list by date as it is possible to filter out important active medications. Starting in the November 2022 version of Epic, this parameter is respected. In May 2022 and earlier versions of Epic, this parameter is allowed but is ignored and no date filtering is applied."}, "patient": {"type": "string", "description": "The FHIR patient ID."}}, "required": ["patient"]}},
    {"name": "POST {api_base}/MedicationRequest", "description": "MedicationRequest.Create", "parameters": {"type": "object", "properties": {"resourceType": {"type": "string", "description": "Use \"MedicationRequest\" for medication requests."}, "medicationCodeableConcept": {"type": "object", "properties": {"coding": {"type": "array", "items": {"type": "object", "properties": {"system": {"type": "string", "description": "Coding system such as \"http://hl7.org/fhir/sid/ndc\" "}, "code": {"type": "string", "description": "The actual code"}, "display": {"type": "string", "description": "Display name"}}}}, "text": {"type": "string", "description": "The order display name of the medication, otherwise the record name."}}}, "authoredOn": {"type": "string", "description": "The date the prescription was written."}, "dosageInstruction": {"type": "array", "items": {"type": "object", "properties": {"route": {"type": "object", "properties": {"text": {"type": "string", "description": "The medication route."}}}, "doseAndRate": {"type": "array", "items": {"type": "object", "properties": {"doseQuantity": {"type": "object", "properties": {"value": {"type": "number"}, "unit": {"type": "string", "description": "unit for the dose such as \"g\" "}}}, "rateQuantity": {"type": "object", "properties": {"value": {"type": "number"}, "unit": {"type": "string", "description": "unit for the rate such as \"h\" "}}}}}}}}}, "status": {"type": "string", "description": "The status of the medication request. Use \"active\" "}, "intent": {"type": "string", "description": "Use \"order\" "}, "subject": {"type": "object", "properties": {"reference": {"type": "string", "description": "The patient FHIR ID for who the medication request is for."}}}}, "required": ["resourceType", "medicationCodeableConcept", "authoredOn", "dosageInstruction", "status", "intent", "subject"]}},
    {"name": "GET {api_base}/Procedure", "description": "Procedure.Search (Orders) The FHIR Procedure resource defines an activity performed on or with a patient as part of the provision of care. It corresponds with surgeries and procedures performed, including endoscopies and biopsies, as well as less invasive actions like counseling and physiotherapy.\n\nThis resource is designed for a high-level summarization around the occurrence of a procedure, and not for specific procedure log documentation - a concept that does not yet have a defined FHIR Resource. When searching, only completed procedures are returned.\n", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "External CPT codes associated with the procedure."}, "date": {"type": "string", "description": "Date or period that the procedure was performed, using the FHIR date parameter format."}, "patient": {"type": "string", "description": "Reference to a patient resource the condition is for."}}, "required": ["date", "patient"]}},
    {"name": "POST {api_base}/ServiceRequest", "description": "ServiceRequest.Create", "parameters": {"type": "object", "properties": {"resourceType": {"type": "string", "description": "Use \"ServiceRequest\" for service requests."}, "code": {"type": "object", "description": "The standard terminology codes mapped to the procedure, which can include LOINC, SNOMED, CPT, CBV, THL, or Kuntalitto codes.", "properties": {"coding": {"type": "array", "items": {"type": "object", "properties": {"system": {"type": "string", "description": "Coding system such as \"http://loinc.org\" "}, "code": {"type": "string", "description": "The actual code"}, "display": {"type": "string", "description": "Display name"}}}}}}, "authoredOn": {"type": "string", "description": "The order instant. This is the date and time of when an order is signed or signed and held."}, "status": {"type": "string", "description": "The status of the service request. Use \"active\" "}, "intent": {"type": "string", "description": "Use \"order\" "}, "priority": {"type": "string", "description": "Use \"stat\" "}, "subject": {"type": "object", "properties": {"reference": {"type": "string", "description": "The patient FHIR ID for who the service request is for."}}}, "note": {"type": "object", "properties": {"text": {"type": "string", "description": "Free text comment here"}}}, "occurrenceDateTime": {"type": "string", "description": "The date and time for the service request to be conducted, in ISO format."}}, "required": ["resourceType", "code", "authoredOn", "status", "intent", "priority", "subject"]}},
    {"name": "GET {api_base}/Patient", "description": "Patient.Search This web service allows filtering or searching for patients based on a number of parameters, and retrieves patient demographic information from a patient's chart for each matching patient record. This service also does not respect the same filtering as MyChart, with the exception of the careProvider parameter.", "parameters": {"type": "object", "properties": {"address": {"type": "string", "description": "The patient's street address."}, "address-city": {"type": "string", "description": "The city for patient's home address."}, "address-postalcode": {"type": "string", "description": "The postal code for patient's home address."}, "address-state": {"type": "string", "description": "The state for the patient's home address."}, "birthdate": {"type": "string", "description": "The patient's date of birth in the format YYYY-MM-DD."}, "family": {"type": "string", "description": "The patient's family (last) name."}, "gender": {"type": "string", "description": "The patient's legal sex. Starting in the August 2021 version of Epic, the legal-sex parameter is preferred."}, "given": {"type": "string", "description": "The patient's given name. May include first and middle names."}, "identifier": {"type": "string", "description": "The patient's identifier."}, "legal-sex": {"type": "string", "description": "The patient's legal sex. Takes precedence over the gender search parameter. Available starting in the August 2021 version of Epic."}, "name": {"type": "string", "description": "Any part of the patient's name. When discrete name parameters are used, such as family or given, this parameter is ignored."}, "telecom": {"type": "string", "description": "The patient's phone number or email."}}, "required": []}}
]

# --- Demo Tasks (EXACT examples from MedAgentBench test_data_v2.json) ---
TASKS = {
    "task1": {
        "name": "Patient Lookup (task1_1)",
        "context": "",
        "question": "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29? If the patient does not exist, the answer should be \"Patient not found\""
    },
    "task2": {
        "name": "Patient Age (task2_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now, and the answer should be rounded down to an integer.",
        "question": "What's the age of the patient with MRN of S2874099?"
    },
    "task3": {
        "name": "Record BP (task3_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The flowsheet ID for blood pressure is BP.",
        "question": "I just measured the blood pressure for patient with MRN of S2380121, and it is \"118/77 mmHg\". Help me record it."
    },
    "task4": {
        "name": "Magnesium Level (task4_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is \"MG\". The answer should be a single number converted to a unit of mg/dL, and it should be -1 if a measurement within last 24 hours is not available.",
        "question": "What's the most recent magnesium level of the patient S3032536 within last 24 hours?"
    },
    "task5": {
        "name": "Mg Check & Order (task5_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The code for magnesium is \"MG\". The NDC for replacement IV magnesium is 0338-1715-40. Dosing instructions: (1) Mild deficiency (eg, serum magnesium 1.5 to 1.9 mg/dL): IV: 1 g over 1 hour. (2) Moderate deficiency (eg, serum magnesium 1 to <1.5 mg/dL): IV: 2 g over 2 hours. (3) Severe deficiency (eg, serum magnesium <1 mg/dL): IV: 4 g over 4 hours.",
        "question": "Check patient S6315806's last serum magnesium level within last 24 hours. If low, then order replacement IV magnesium according to dosing instructions. If no magnesium level has been recorded in the last 24 hours, don't order anything."
    },
    "task6": {
        "name": "Avg CBG (task6_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The code for CBG is \"GLU\". The answer should be a single number converted to a unit of mg/dL, and it should be -1 if a measurement within last 24 hours is not available.",
        "question": "What is the average CBG of the patient S6307599 over the last 24 hours?"
    },
    "task7": {
        "name": "Recent CBG (task7_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The code for CBG is \"GLU\"",
        "question": "What is the most recent CBG of the patient S2823623?"
    },
    "task8": {
        "name": "Ortho Referral (task8_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The SNOMED code for orthopedic surgery referral is 306181000000106.",
        "question": "Order orthopedic surgery referral for patient S2016972. Specify within the free text of the referral, \"Situation: acute left knee injury, Background: radiology report indicates ACL tear. Assessment: ACL tear grade II. Recommendation: request for Orthopedic service to evaluate and provide management recommendations.\""
    },
    "task9": {
        "name": "K+ Check & Order (task9_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The code for potassium is \"K\". The NDC for replacement potassium is 40032-917-01. Dosing instructions: for every 0.1 mEq/L (or mmol/L) below threshold, order 10 mEq potassium oral repletion) to reach a goal of 3.5 serum level. The LOINC code for serum potassium level is 2823-3.",
        "question": "Check patient S3241217's most recent potassium level. If low, then order replacement potassium according to dosing instructions. Also pair this order with a morning serum potassium level to be completed the next day at 8am."
    },
    "task10": {
        "name": "HbA1C Check (task10_1)",
        "context": "It's 2023-11-13T10:15:00+00:00 now. The code for HbA1C is \"A1C\". The LOINC code for ordering HbA1C lab is: 4548-4. The answer should be [-1] if a measurement is not available.",
        "question": "What's the last HbA1C (hemoglobin A1C) value in the chart for patient S6227720 and when was it recorded? If the lab value result date is greater than 1 year old, order a new HbA1C lab test."
    }
}

# --- Modal Setup ---
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi[standard]>=0.115.0",
        "uvicorn>=0.34.0",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "httpx>=0.27.0",
    )
)

app = modal.App("sara-agent")


# --- Modal Function ---
@app.function(
    image=image,
    cpu=AGENT_CPU,
    memory=AGENT_MEMORY,
    timeout=AGENT_TIMEOUT,
    min_containers=1,  # Keep one instance warm for responsiveness
)
@modal.concurrent(max_inputs=AGENT_CONCURRENT_INPUTS)
@modal.asgi_app()
def api():
    """Serve the FastAPI application."""
    import json
    import re
    import time
    from dataclasses import dataclass, field
    from enum import Enum
    from typing import Any, AsyncGenerator, Dict, List, Optional
    from urllib.parse import parse_qs, urlparse

    import httpx
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from openai import AsyncOpenAI
    from pydantic import BaseModel, Field

    # =========================================================================
    # Parser (from modal/utils/parser.py)
    # =========================================================================

    class ActionType(Enum):
        """Types of actions Sara can output."""
        GET = "GET"
        POST = "POST"
        FINISH = "FINISH"
        UNKNOWN = "UNKNOWN"

    @dataclass
    class Action:
        """Represents a parsed action from Sara's output."""
        type: ActionType
        endpoint: str = ""
        params: Dict[str, str] = field(default_factory=dict)
        body: Dict[str, Any] = field(default_factory=dict)
        answer: str = ""
        raw_content: str = ""

    def parse_action(content: str) -> Action:
        """Parse Sara's output and return the appropriate Action."""
        if not content:
            return Action(type=ActionType.UNKNOWN, raw_content=content)

        # Try to parse FINISH action
        finish_action = _parse_finish(content)
        if finish_action:
            return finish_action

        # Try to parse GET action
        get_action = _parse_get(content)
        if get_action:
            return get_action

        # Try to parse POST action
        post_action = _parse_post(content)
        if post_action:
            return post_action

        return Action(type=ActionType.UNKNOWN, raw_content=content)

    def extract_action(raw: str) -> str:
        """Extract clean GET/POST/FINISH action from potentially verbose response.

        This handles cases where the model includes extra text before/after the action.
        Matches the logic from benchmark_models.py.
        """
        stripped = raw.strip()

        # If it already starts with the expected format, return as-is
        if stripped.startswith("GET ") or stripped.startswith("POST ") or stripped.startswith("FINISH("):
            return stripped

        # Try to find FINISH anywhere in the response
        finish_match = re.search(r'FINISH\(\[.*?\]\)', stripped, re.DOTALL)
        if finish_match:
            return finish_match.group(0)

        # Try to find GET with URL
        get_match = re.search(r'^(GET\s+https?://\S+)', stripped, re.MULTILINE)
        if get_match:
            return get_match.group(1)

        # Try to find POST with URL and JSON body
        post_match = re.search(r'^(POST\s+https?://\S+)\n(\{.*)', stripped, re.MULTILINE | re.DOTALL)
        if post_match:
            url_line = post_match.group(1)
            rest = post_match.group(2)
            # Find the complete JSON object by counting braces
            brace_count = 0
            end_idx = 0
            for i, c in enumerate(rest):
                if c == '{':
                    brace_count += 1
                elif c == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            if end_idx > 0:
                return url_line + "\n" + rest[:end_idx]

        return stripped

    def _parse_get(content: str) -> Action | None:
        """Parse a GET action from content."""
        pattern = r'^GET\s+(https?://[^\s]+)'
        match = re.match(pattern, content.strip())
        if not match:
            return None

        url = match.group(1)
        try:
            parsed = urlparse(url)
            endpoint = parsed.path
            params = {}
            if parsed.query:
                qs = parse_qs(parsed.query)
                params = {k: v[0] for k, v in qs.items()}
            return Action(type=ActionType.GET, endpoint=endpoint, params=params)
        except Exception:
            return None

    def _parse_post(content: str) -> Action | None:
        """Parse a POST action from content."""
        pattern = r'^POST\s+(https?://[^\s]+)\s*\n(.+)'
        match = re.match(pattern, content.strip(), re.DOTALL)
        if not match:
            return None

        url = match.group(1)
        json_str = match.group(2).strip()
        try:
            parsed = urlparse(url)
            endpoint = parsed.path
            body = json.loads(json_str)
            return Action(type=ActionType.POST, endpoint=endpoint, body=body)
        except (json.JSONDecodeError, Exception):
            return None

    def _parse_finish(content: str) -> Action | None:
        """Parse a FINISH action from content.

        Handles various FINISH formats:
        - FINISH(["S1234567"])  - quoted string
        - FINISH([S1234567])    - unquoted identifier
        - FINISH([42])          - number
        - FINISH([-1])          - negative number
        - FINISH([])            - empty array
        - FINISH([6.5, "2022-10-15"])  - multiple values
        """
        # Match FINISH with any content in brackets (including empty)
        pattern = r'FINISH\(\[(.*?)\]\)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return None

        array_content = match.group(1).strip()

        # Empty array case
        if not array_content:
            return Action(type=ActionType.FINISH, answer="")

        # Try to parse as JSON array
        try:
            parsed = json.loads(f"[{array_content}]")
            # Convert to string representation for answer
            if len(parsed) == 1:
                return Action(type=ActionType.FINISH, answer=str(parsed[0]))
            elif len(parsed) > 1:
                return Action(type=ActionType.FINISH, answer=json.dumps(parsed))
            else:
                return Action(type=ActionType.FINISH, answer="")
        except json.JSONDecodeError:
            # Fallback: extract the raw content
            # Handle unquoted identifiers like S1234567
            return Action(type=ActionType.FINISH, answer=array_content.strip())

    # =========================================================================
    # FHIR Client (from modal/utils/fhir_client.py)
    # =========================================================================

    @dataclass
    class FHIRResult:
        """Result of a FHIR operation."""
        success: bool
        status_code: int
        data: Dict[str, Any] = field(default_factory=dict)
        error: str = ""

    class FHIRClient:
        """Async FHIR client for executing GET/POST requests with retry logic."""

        MAX_RETRIES = 3
        RETRY_DELAY = 2.0  # seconds

        def __init__(self, base_url: str):
            self.base_url = base_url.rstrip("/")
            # Longer timeout for Modal cold starts, with separate connect timeout
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=120.0),  # 2-minute timeout for cold starts
                headers={"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"},
                follow_redirects=True
            )

        async def close(self) -> None:
            await self._client.aclose()

        async def execute(self, action: Action) -> FHIRResult:
            if action.type == ActionType.GET:
                return await self.get(action.endpoint, action.params)
            elif action.type == ActionType.POST:
                return await self.post(action.endpoint, action.body)
            elif action.type == ActionType.FINISH:
                return FHIRResult(success=True, status_code=200, data={"answer": action.answer})
            else:
                return FHIRResult(success=False, status_code=0, error=f"Unsupported action type: {action.type}")

        async def _request_with_retry(self, method: str, url: str, **kwargs) -> FHIRResult:
            """Execute HTTP request with retry logic for transient errors."""
            import asyncio

            last_error = None
            for attempt in range(self.MAX_RETRIES):
                try:
                    if method == "GET":
                        response = await self._client.get(url, **kwargs)
                    else:
                        response = await self._client.post(url, **kwargs)
                    return self._process_response(response)
                except httpx.TimeoutException as e:
                    last_error = f"Timeout: {repr(e)}"
                except httpx.ConnectError as e:
                    last_error = f"Connection error: {repr(e)}"
                except httpx.RequestError as e:
                    last_error = f"Request error: {type(e).__name__}: {repr(e)}"
                except Exception as e:
                    # Catch TransferEncodingError and similar issues
                    last_error = f"Unexpected error: {type(e).__name__}: {str(e)}"

                # Retry after delay if not last attempt
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

            return FHIRResult(success=False, status_code=0, error=last_error or "Unknown error")

        async def get(self, endpoint: str, params: Dict[str, str]) -> FHIRResult:
            # Endpoint may already contain /fhir prefix, avoid duplication
            if endpoint.startswith("/fhir"):
                endpoint = endpoint[5:]  # Remove /fhir prefix since base_url already has it
            url = f"{self.base_url}{endpoint}"
            return await self._request_with_retry("GET", url, params=params if params else None)

        async def post(self, endpoint: str, body: Dict[str, Any]) -> FHIRResult:
            # Endpoint may already contain /fhir prefix, avoid duplication
            if endpoint.startswith("/fhir"):
                endpoint = endpoint[5:]  # Remove /fhir prefix since base_url already has it
            url = f"{self.base_url}{endpoint}"
            return await self._request_with_retry("POST", url, json=body)

        def _process_response(self, response: httpx.Response) -> FHIRResult:
            status_code = response.status_code
            try:
                data = response.json()
            except Exception:
                data = {}
            if status_code >= 400:
                return FHIRResult(success=False, status_code=status_code, data=data, error=f"HTTP {status_code}")
            return FHIRResult(success=True, status_code=status_code, data=data)

    # =========================================================================
    # Agent Event and Sara Agent (from modal/agent.py)
    # =========================================================================

    MAX_ROUNDS = 8

    @dataclass
    class AgentEvent:
        """Event emitted by the Sara agent during execution."""
        type: str  # "thinking", "tool_call", "complete", "error"
        timestamp: float
        content: str = ""
        tool: str = ""
        result: Any = None

    # Exact prompt from benchmark_models.py - proven to work with Sara model
    MEDAGENTBENCH_PROMPT = """You are an expert in using FHIR functions to assist medical professionals. You are given a question and a set of possible functions. Based on the question, you will need to make one or more function/tool calls to achieve the purpose.

CRITICAL FORMAT RULES — your response must contain ONLY one of these three formats and NOTHING else (no explanations, no reasoning, no commentary):

1. To invoke a GET function:
GET url?param_name1=param_value1&param_name2=param_value2...

2. To invoke a POST function:
POST url
[your payload data in JSON format]

3. To finish with your answer (the list MUST be JSON parseable):
FINISH([answer1, answer2, ...])

IMPORTANT RULES:
- Your ENTIRE response must be ONLY the function call or FINISH — no other text before or after.
- Do NOT include any reasoning, explanation, or commentary in your response.
- Do NOT prefix your response with phrases like "I'll help you", "Let me", "Based on", etc.
- Each response must start with exactly "GET", "POST", or "FINISH(" as the very first characters.
- You can call only one function per response.
- FINISH answers must contain ONLY simple numeric values, simple strings, or -1. NEVER include objects, descriptions, or explanations inside FINISH.
- If the task asks you to check a value and take action only if needed, and no action is needed, call FINISH([]) with an empty list.
- If the task says to return -1 when something is unavailable, return FINISH([-1]) — just the number, no explanation text.

ANSWER FORMAT RULES FOR SPECIFIC TASK TYPES:

When asked for a lab value (e.g., magnesium, glucose, potassium, HbA1C):
- Return ONLY the numeric value: FINISH([2.1]) — NOT FINISH([{{"value": 2.1, "unit": "mg/dL"}}])
- If no measurement available, return: FINISH([-1])
- IMPORTANT: When finding the "most recent" observation, you MUST compare the effectiveDateTime fields to find the latest one chronologically. Do NOT assume the first entry in the FHIR Bundle is the most recent — entries may NOT be sorted by date. You must check ALL entries and pick the one with the latest effectiveDateTime.

When asked for the average of lab values:
- Return ONLY a single number as a float: FINISH([97.5])
- Make sure to only include observations within the specified time window (compare effectiveDateTime against the cutoff)

When asked to check a value and conditionally order something:
- If the value is normal/not low and no order is needed: FINISH([])
- If no measurement is available and instructions say don't order: FINISH([])
- If you placed orders, finish with: FINISH([]) or FINISH([the_value])

When asked for a value AND its date (e.g., HbA1C):
- Return as: FINISH([6.5, "2022-10-15T08:30:00+00:00"]) — value first, then the exact ISO timestamp string from the FHIR response
- If no measurement available: FINISH([-1])
- IMPORTANT: If the task says "if the lab value result date is greater than 1 year old, order a new lab test" — you MUST still order the test even when no value exists at all (no measurement = definitely older than 1 year). First POST the ServiceRequest to order the test, THEN call FINISH([-1]).
- Similarly, if a value exists but is older than 1 year from the current time, POST the ServiceRequest first, then FINISH with the value and date.

When ordering potassium replacement (task involving potassium dosing):
- The dosing formula is: for every 0.1 mEq/L below 3.5, order 10 mEq. So if K=3.1, dose = (3.5-3.1)/0.1 * 10 = 40 mEq
- The route must be: {{"text": "oral"}}
- You must make TWO POST requests: first the MedicationRequest for potassium, then the ServiceRequest for the follow-up serum potassium lab
- For the follow-up lab ServiceRequest, set occurrenceDateTime to the next day at 8:00 AM (e.g., "2023-11-14T08:00:00+00:00")

When ordering medications (MedicationRequest POST):
- The "route" field in dosageInstruction must be a plain string: "IV" for intravenous or "oral" for oral. NOT an object like {{"text": "IV"}} — just the string directly.
- Always include doseQuantity (with value and unit) and rateQuantity (with value and unit) where applicable
- Use authoredOn = "2023-11-13T10:15:00+00:00" (the current time from context)

When ordering IV magnesium replacement:
- Mild deficiency (1.5-1.9 mg/dL): dose=1g, rate=1h → doseQuantity: {{"value": 1, "unit": "g"}}, rateQuantity: {{"value": 1, "unit": "h"}}
- Moderate deficiency (1.0 to <1.5 mg/dL): dose=2g, rate=2h → doseQuantity: {{"value": 2, "unit": "g"}}, rateQuantity: {{"value": 2, "unit": "h"}}
- Severe deficiency (<1.0 mg/dL): dose=4g, rate=4h → doseQuantity: {{"value": 4, "unit": "g"}}, rateQuantity: {{"value": 4, "unit": "h"}}

When ordering lab tests or referrals (ServiceRequest POST):
- Always include: resourceType, code (with coding system/code), authoredOn, status ("active"), intent ("order"), priority ("stat"), subject
- For scheduled tests, include occurrenceDateTime with the scheduled time

EXAMPLES of correct FINISH calls:
FINISH(["S1234567"])
FINISH([42])
FINISH([125.5])
FINISH([-1])
FINISH([])
FINISH([6.5, "2022-10-15T08:30:00+00:00"])

EXAMPLES of WRONG FINISH calls (NEVER do these):
FINISH([{{"value": 191.0, "unit": "mg/dL"}}])  ← objects not allowed, use FINISH([191.0])
FINISH(["The potassium level is 4.5 mmol/L, no replacement needed"])  ← descriptions not allowed, use FINISH([])
FINISH([-1, "No measurement available", "Test ordered"])  ← extra explanation strings not allowed, use FINISH([-1])
FINISH([4.5, "above threshold, no action needed"])  ← use FINISH([]) when no action needed

Here is a list of functions in JSON format that you can invoke. Note that you should use {api_base} as the api_base.
{functions}

Context: {context}
Question: {question}"""

    class SaraAgent:
        """Custom agent that handles Sara's text-based tool calling."""

        def __init__(self, sara_url: str, fhir_url: str, functions: List[Dict]):
            self.sara_url = sara_url
            self.fhir_url = fhir_url
            self.functions = functions
            self._sara_client = AsyncOpenAI(
                base_url=f"{sara_url}/v1",
                api_key="not-needed"
            )

        def _build_prompt(self, context: str, question: str) -> str:
            functions_str = json.dumps(self.functions, indent=2)
            return MEDAGENTBENCH_PROMPT.format(
                api_base=self.fhir_url,
                functions=functions_str,
                context=context,
                question=question
            )

        async def _call_sara(self, messages: List[Dict]) -> str:
            response = await self._sara_client.chat.completions.create(
                model="sara",
                messages=messages,
                temperature=0.0,
                max_tokens=2048
            )
            return response.choices[0].message.content

        def _format_fhir_result(self, result: FHIRResult, action_type: ActionType) -> str:
            """Format FHIR result using EXACT MedAgentBench feedback messages."""
            if action_type == ActionType.GET:
                if result.success:
                    # Exact format from MedAgentBench __init__.py
                    return f"Here is the response from the GET request:\n{json.dumps(result.data, indent=2)}. Please call FINISH if you have got answers for all the questions and finished all the requested tasks"
                else:
                    # Exact error format
                    error_msg = result.error
                    if result.data and result.data.get("resourceType") == "OperationOutcome":
                        issues = result.data.get("issue", [])
                        if issues:
                            diagnostics = issues[0].get("diagnostics", "")
                            if diagnostics:
                                error_msg += f" - {diagnostics}"
                    return f"Error in sending the GET request: {error_msg}"
            elif action_type == ActionType.POST:
                if result.success:
                    # Exact format from MedAgentBench __init__.py
                    return "POST request accepted and executed successfully. Please call FINISH if you have got answers for all the questions and finished all the requested tasks"
                else:
                    return "Invalid POST request"
            else:
                return json.dumps(result.data, indent=2) if result.success else result.error

        async def run(self, context: str, question: str) -> AsyncGenerator[AgentEvent, None]:
            initial_prompt = self._build_prompt(context, question)
            messages = [{"role": "user", "content": initial_prompt}]
            fhir_client = FHIRClient(self.fhir_url)

            try:
                for round_num in range(MAX_ROUNDS):
                    try:
                        response = await self._call_sara(messages)
                    except Exception as e:
                        yield AgentEvent(type="error", content=f"Sara model error: {str(e)}", timestamp=time.time())
                        return

                    # Clean the response like benchmark_models.py does
                    cleaned = response.strip().replace("```tool_code", "").replace("```", "").strip()
                    cleaned = extract_action(cleaned)

                    yield AgentEvent(type="thinking", content=cleaned, timestamp=time.time())

                    action = parse_action(cleaned)

                    if action.type == ActionType.FINISH:
                        yield AgentEvent(type="complete", result=action.answer, timestamp=time.time())
                        return

                    if action.type == ActionType.UNKNOWN:
                        messages.append({"role": "assistant", "content": cleaned})
                        messages.append({
                            "role": "user",
                            "content": "Your response did not contain a valid action. Please use GET, POST, or FINISH format."
                        })
                        continue

                    fhir_result = await fhir_client.execute(action)

                    # Build result for the event
                    if fhir_result.success:
                        event_result = fhir_result.data
                    else:
                        # Include both error message and any FHIR OperationOutcome details
                        event_result = {
                            "error": fhir_result.error,
                            "status_code": fhir_result.status_code,
                        }
                        # Add OperationOutcome details if available
                        if fhir_result.data and fhir_result.data.get("resourceType") == "OperationOutcome":
                            event_result["details"] = fhir_result.data

                    yield AgentEvent(
                        type="tool_call",
                        tool=action.type.value,
                        result=event_result,
                        timestamp=time.time()
                    )

                    # Use exact MedAgentBench feedback format
                    formatted_result = self._format_fhir_result(fhir_result, action.type)
                    messages.append({"role": "assistant", "content": cleaned})
                    messages.append({"role": "user", "content": formatted_result})

                yield AgentEvent(
                    type="error",
                    content=f"Agent reached maximum rounds ({MAX_ROUNDS}) without completing the task.",
                    timestamp=time.time()
                )
            finally:
                await fhir_client.close()

    # =========================================================================
    # FastAPI Application
    # =========================================================================

    class RunRequest(BaseModel):
        """Request model for running the agent."""
        taskId: str = Field(..., description="Task ID from predefined tasks or 'custom'")
        prompt: str = Field(..., description="The prompt/question for the agent")
        context: Optional[str] = Field(None, description="Optional context for the task")

    class SSEEvent:
        """Helper class to format SSE events."""
        @staticmethod
        def format(event_type: str, data: dict) -> str:
            json_data = json.dumps(data)
            return f"event: {event_type}\ndata: {json_data}\n\n"

    fastapi_app = FastAPI(
        title="Sara Agent API",
        description="Clinical workflow agent API with SSE streaming",
        version="1.0.0"
    )

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://*.vercel.app",
            "*"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @fastapi_app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "service": "sara-agent"}

    @fastapi_app.get("/api/tasks")
    async def list_tasks():
        """List all available demo tasks."""
        return {
            "tasks": [
                {"id": task_id, **task_data}
                for task_id, task_data in TASKS.items()
            ]
        }

    @fastapi_app.post("/api/run")
    async def run_agent(request: RunRequest):
        """
        Run the Sara agent with SSE streaming.

        Returns a Server-Sent Events stream with the following event types:
        - status: Lifecycle updates (starting, running, finished)
        - thinking: Sara's reasoning/response
        - tool_call: FHIR API call being executed
        - tool_result: Result of the FHIR API call
        - complete: Task completed with final answer
        - error: Error occurred
        """
        async def event_generator():
            tool_call_id = 0

            try:
                yield SSEEvent.format("status", {
                    "phase": "starting",
                    "message": "Connecting to Sara model..."
                })

                if request.taskId in TASKS:
                    task = TASKS[request.taskId]
                    context = request.context or task["context"]
                    question = request.prompt or task["question"]
                else:
                    context = request.context or ""
                    question = request.prompt

                agent = SaraAgent(
                    sara_url=SARA_URL,
                    fhir_url=FHIR_URL,
                    functions=FHIR_FUNCTIONS
                )

                yield SSEEvent.format("status", {
                    "phase": "running",
                    "message": "Agent is processing your request..."
                })

                async for event in agent.run(context=context, question=question):
                    if event.type == "thinking":
                        yield SSEEvent.format("thinking", {
                            "content": event.content,
                            "timestamp": event.timestamp
                        })

                    elif event.type == "tool_call":
                        tool_call_id += 1
                        tc_id = f"tc_{tool_call_id:03d}"

                        endpoint = ""
                        if isinstance(event.result, dict):
                            resource_type = event.result.get("resourceType", "")
                            if resource_type:
                                endpoint = f"/fhir/{resource_type}"

                        yield SSEEvent.format("tool_call", {
                            "id": tc_id,
                            "tool": event.tool,
                            "endpoint": endpoint,
                            "status": "running"
                        })

                        start_time = event.timestamp
                        duration_ms = int((time.time() - start_time) * 1000)

                        success = True
                        if isinstance(event.result, dict):
                            success = "error" not in event.result

                        yield SSEEvent.format("tool_result", {
                            "id": tc_id,
                            "status": "success" if success else "error",
                            "duration_ms": duration_ms,
                            "result": event.result
                        })

                    elif event.type == "complete":
                        yield SSEEvent.format("complete", {
                            "success": True,
                            "answer": event.result,
                            "artifacts": []
                        })

                    elif event.type == "error":
                        yield SSEEvent.format("error", {
                            "message": event.content
                        })

                yield SSEEvent.format("status", {
                    "phase": "finished",
                    "message": "Task completed"
                })

            except Exception as e:
                yield SSEEvent.format("error", {
                    "message": f"Agent error: {str(e)}"
                })

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    return fastapi_app


# --- Local Test Entrypoint ---
@app.local_entrypoint()
def main():
    """Test the agent API locally."""
    import json
    import asyncio

    try:
        import aiohttp
    except ImportError:
        import subprocess as sp
        sp.run(["pip", "install", "aiohttp"], check=True)
        import aiohttp

    async def test():
        url = api.get_web_url()
        print(f"\nSara Agent API: {url}")
        print(f"Health: {url}/health")
        print(f"Tasks: {url}/api/tasks")
        print(f"Run: {url}/api/run\n")

        async with aiohttp.ClientSession() as session:
            print("Waiting for server to be ready...")
            for attempt in range(60):
                try:
                    async with session.get(
                        f"{url}/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            print("Server is healthy!\n")
                            break
                except Exception:
                    pass
                await asyncio.sleep(2)
            else:
                print("Server did not become ready in time.")
                return

            print("Available tasks:")
            async with session.get(f"{url}/api/tasks") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    for task in result["tasks"]:
                        print(f"  - {task['id']}: {task['name']}")
                    print()

            print("Running test task (task1: Patient Lookup)...")
            print("-" * 50)

            payload = {
                "taskId": "task1",
                "prompt": "What's the MRN?"
            }

            async with session.post(
                f"{url}/api/run",
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as resp:
                if resp.status == 200:
                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("event:"):
                            event_type = line.split(":")[1].strip()
                            print(f"\n[{event_type}]")
                        elif line.startswith("data:"):
                            data = line[5:].strip()
                            try:
                                parsed = json.loads(data)
                                print(json.dumps(parsed, indent=2))
                            except json.JSONDecodeError:
                                print(data)
                else:
                    print(f"Error: {resp.status}")
                    text = await resp.text()
                    print(text)

            print("-" * 50)
            print("\nTest complete!")

    asyncio.run(test())
