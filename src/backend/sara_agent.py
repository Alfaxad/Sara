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

# Service URLs (Modal internal URLs when deployed)
# Note: Update these with the actual deployed URLs after deployment
SARA_URL = "https://nadhari--sara-model-serve.modal.run"
FHIR_URL = "https://nadhari--fhir-server-serve.modal.run"

# --- FHIR Functions (from MedAgentBench) ---
FHIR_FUNCTIONS = [
    {
        "name": "GET {api_base}/Condition",
        "description": "Condition.Search (Problems) - Retrieves problems from a patient's chart.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": 'Always "problem-list-item".'},
                "patient": {"type": "string", "description": "Patient reference."}
            },
            "required": ["patient"]
        }
    },
    {
        "name": "GET {api_base}/Observation",
        "description": "Observation.Search (Labs) - Returns lab results.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Observation identifier."},
                "date": {"type": "string", "description": "Date specimen was obtained."},
                "patient": {"type": "string", "description": "Patient reference."}
            },
            "required": ["code", "patient"]
        }
    },
    {
        "name": "GET {api_base}/MedicationRequest",
        "description": "MedicationRequest.Search - Query for medication orders.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category of medication orders."},
                "date": {"type": "string", "description": "Medication administration date."},
                "patient": {"type": "string", "description": "The FHIR patient ID."}
            },
            "required": ["patient"]
        }
    },
    {
        "name": "POST {api_base}/MedicationRequest",
        "description": "MedicationRequest.Create - Create a new medication request.",
        "parameters": {
            "type": "object",
            "properties": {
                "resourceType": {"type": "string"},
                "medicationCodeableConcept": {"type": "object"},
                "authoredOn": {"type": "string"},
                "dosageInstruction": {"type": "array"},
                "status": {"type": "string"},
                "intent": {"type": "string"},
                "subject": {"type": "object"}
            },
            "required": ["resourceType", "medicationCodeableConcept", "authoredOn", "dosageInstruction", "status", "intent", "subject"]
        }
    },
    {
        "name": "GET {api_base}/Procedure",
        "description": "Procedure.Search - Retrieves completed procedures.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "CPT codes."},
                "date": {"type": "string", "description": "Date or period."},
                "patient": {"type": "string", "description": "Patient reference."}
            },
            "required": ["date", "patient"]
        }
    },
    {
        "name": "POST {api_base}/ServiceRequest",
        "description": "ServiceRequest.Create - Create a new service/order request.",
        "parameters": {
            "type": "object",
            "properties": {
                "resourceType": {"type": "string"},
                "code": {"type": "object"},
                "authoredOn": {"type": "string"},
                "status": {"type": "string"},
                "intent": {"type": "string"},
                "priority": {"type": "string"},
                "subject": {"type": "object"},
                "note": {"type": "object"},
                "occurrenceDateTime": {"type": "string"}
            },
            "required": ["resourceType", "code", "authoredOn", "status", "intent", "priority", "subject"]
        }
    },
    {
        "name": "GET {api_base}/Patient",
        "description": "Patient.Search - Search for patients based on demographics.",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "address-city": {"type": "string"},
                "address-postalcode": {"type": "string"},
                "address-state": {"type": "string"},
                "birthdate": {"type": "string"},
                "family": {"type": "string"},
                "gender": {"type": "string"},
                "given": {"type": "string"},
                "identifier": {"type": "string"},
                "name": {"type": "string"},
                "telecom": {"type": "string"}
            },
            "required": []
        }
    }
]

# --- Demo Tasks ---
TASKS = {
    "task1": {
        "name": "Patient Lookup",
        "context": "Patient with name John Smith and DOB 1985-03-15",
        "question": "What's the MRN?"
    },
    "task2": {
        "name": "Medication Refill",
        "context": "Patient S6200102",
        "question": "Refill the current Metformin prescription"
    },
    "task3": {
        "name": "Lab Results",
        "context": "Patient S6200103",
        "question": "What were the most recent HbA1c results?"
    },
    "task4": {
        "name": "Problem List",
        "context": "Patient S6200104",
        "question": "List all active conditions on the problem list"
    },
    "task5": {
        "name": "Allergy Check",
        "context": "Patient S6200105",
        "question": "Does this patient have any documented allergies to penicillin?"
    },
    "task6": {
        "name": "Procedure History",
        "context": "Patient S6200106, reviewing past year",
        "question": "What procedures were performed in the last 12 months?"
    },
    "task7": {
        "name": "Vitals Review",
        "context": "Patient S6200107",
        "question": "What were the most recent vital signs recorded?"
    },
    "task8": {
        "name": "Order Lab",
        "context": "Patient S6200108, routine checkup",
        "question": "Order a comprehensive metabolic panel"
    },
    "task9": {
        "name": "Medication List",
        "context": "Patient S6200109",
        "question": "List all active outpatient medications"
    },
    "task10": {
        "name": "Demographics",
        "context": "Patient S6200110",
        "question": "What is the patient's current address and phone number?"
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
        """Parse a FINISH action from content."""
        pattern = r'FINISH\(\[([^\]]+)\]\)'
        match = re.search(pattern, content)
        if not match:
            return None

        try:
            array_content = match.group(1)
            string_pattern = r'"([^"]*)"'
            strings = re.findall(string_pattern, array_content)
            if not strings:
                string_pattern = r"'([^']*)'"
                strings = re.findall(string_pattern, array_content)
            if strings:
                return Action(type=ActionType.FINISH, answer=strings[0])
        except Exception:
            pass
        return None

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
        """Async FHIR client for executing GET/POST requests."""

        def __init__(self, base_url: str):
            self.base_url = base_url.rstrip("/")
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"}
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

        async def get(self, endpoint: str, params: Dict[str, str]) -> FHIRResult:
            url = f"{self.base_url}{endpoint}"
            try:
                response = await self._client.get(url, params=params if params else None)
                return self._process_response(response)
            except httpx.ConnectError as e:
                return FHIRResult(success=False, status_code=0, error=f"Connection error: {str(e)}")
            except httpx.RequestError as e:
                return FHIRResult(success=False, status_code=0, error=f"Request error: {str(e)}")

        async def post(self, endpoint: str, body: Dict[str, Any]) -> FHIRResult:
            url = f"{self.base_url}{endpoint}"
            try:
                response = await self._client.post(url, json=body)
                return self._process_response(response)
            except httpx.ConnectError as e:
                return FHIRResult(success=False, status_code=0, error=f"Connection error: {str(e)}")
            except httpx.RequestError as e:
                return FHIRResult(success=False, status_code=0, error=f"Request error: {str(e)}")

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

    MEDAGENTBENCH_PROMPT = """You are an expert in using FHIR functions to assist medical professionals. You are given a question and a set of possible functions. Based on the question, you may need to make one or more function calls to get the information needed or to take actions.

1. If you decide to invoke a GET function, you MUST put it in the format of
GET url?param_name1=param_value1&param_name2=param_value2...

2. If you decide to invoke a POST function, you MUST put it in the format of
POST url
[your payload data in JSON format]

3. If you have got answers for all the questions and finished all the requested tasks, you MUST call to finish the conversation in the format of
FINISH([answer1, answer2, ...])

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

        def _format_fhir_result(self, result: FHIRResult) -> str:
            if result.success:
                return json.dumps(result.data, indent=2)
            else:
                return f"Error (HTTP {result.status_code}): {result.error}"

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

                    yield AgentEvent(type="thinking", content=response, timestamp=time.time())

                    action = parse_action(response)

                    if action.type == ActionType.FINISH:
                        yield AgentEvent(type="complete", result=action.answer, timestamp=time.time())
                        return

                    if action.type == ActionType.UNKNOWN:
                        messages.append({"role": "assistant", "content": response})
                        messages.append({
                            "role": "user",
                            "content": "Your response did not contain a valid action. Please use GET, POST, or FINISH format."
                        })
                        continue

                    fhir_result = await fhir_client.execute(action)

                    yield AgentEvent(
                        type="tool_call",
                        tool=action.type.value,
                        result=fhir_result.data if fhir_result.success else {
                            "error": fhir_result.error,
                            "status_code": fhir_result.status_code
                        },
                        timestamp=time.time()
                    )

                    formatted_result = self._format_fhir_result(fhir_result)
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Result: {formatted_result}"})

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
