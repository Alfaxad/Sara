# Sara Backend

> Modal-based serverless backend for the Sara Clinical Workflow Agent

## Overview

The Sara backend consists of three Modal services that work together to power an AI-driven clinical workflow agent:

| Service | Resource | Endpoint | Description |
|---------|----------|----------|-------------|
| **Sara Model** | A100 GPU | `/v1/chat/completions` | OpenAI-compatible LLM endpoint (Sara 1.5 4B) |
| **Sara Agent** | CPU | `/api/run` | FastAPI with SSE streaming, agent orchestration |
| **FHIR Server** | CPU | `/fhir/*` | HAPI FHIR R4 with 100 synthetic patients |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Modal Cloud                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────────┐     ┌──────────────────┐                     │
│   │   sara-model     │     │   fhir-server    │                     │
│   │   (A100 GPU)     │     │   (CPU)          │                     │
│   │                  │     │                  │                     │
│   │ /v1/chat/        │     │ /fhir/Patient    │                     │
│   │   completions    │     │ /fhir/Observation│                     │
│   └────────▲─────────┘     │ /fhir/Medication │                     │
│            │               │ /fhir/...        │                     │
│            │               └────────▲─────────┘                     │
│            │                        │                               │
│   ┌────────┴────────────────────────┴─────────┐                     │
│   │              sara-agent (CPU)              │                     │
│   │                                            │                     │
│   │  /api/run     - SSE streaming endpoint     │                     │
│   │  /api/tasks   - List available tasks       │                     │
│   │  /health      - Health check               │                     │
│   │                                            │                     │
│   │  Agent Loop:                               │                     │
│   │  1. Receive prompt from frontend           │                     │
│   │  2. Call Sara model for next action        │                     │
│   │  3. Parse GET/POST/FINISH commands         │                     │
│   │  4. Execute FHIR calls                     │                     │
│   │  5. Stream results back via SSE            │                     │
│   └────────────────────────────────────────────┘                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Vercel Frontend │
                    │  (Next.js)       │
                    └─────────────────┘
```

## Services

### 1. Sara Model (`sara_model.py`)

Deploys the fine-tuned Sara 1.5 4B model (based on MedGemma) on an A100 GPU.

**Features:**
- OpenAI-compatible `/v1/chat/completions` endpoint
- Automatic model caching via Modal Volumes
- 15-minute warm window to reduce cold starts
- Concurrent request handling (8 max)

**Configuration:**
```python
MODEL_NAME = "Nadhari/Sara-1.5-4B-it"
GPU = "A100"
WARM_WINDOW = 15 minutes
TIMEOUT = 10 minutes
```

### 2. Sara Agent (`sara_agent.py`)

FastAPI service that orchestrates the agent loop with Server-Sent Events (SSE) streaming.

**Endpoints:**
- `POST /api/run` - Execute a task with SSE streaming
- `GET /api/tasks` - List available demo tasks
- `GET /health` - Health check

**SSE Event Types:**
```typescript
type SSEEvent =
  | { type: 'status', data: { status: 'thinking' | 'processing' } }
  | { type: 'tool_call', data: { id, tool, args } }
  | { type: 'tool_result', data: { id, result, status } }
  | { type: 'complete', data: { response, answer } }
  | { type: 'error', data: { error, message } }
```

**Agent Action Format (Sara's output):**
```
GET {api_base}/Patient?name=John&birthdate=1990-01-01
POST {api_base}/Observation {...json body...}
FINISH(result)
```

### 3. FHIR Server (`fhir_server.py`)

Deploys HAPI FHIR R4 server with MedAgentBench synthetic data.

**Features:**
- 100 pre-loaded synthetic patient records
- Full FHIR R4 REST API
- H2 database (in-memory, loaded from Docker image)

**Available Resources:**
- `/fhir/Patient` - Patient demographics
- `/fhir/Observation` - Labs (MG, GLU, A1C, K) and vitals
- `/fhir/MedicationRequest` - Medication orders
- `/fhir/Condition` - Problem list
- `/fhir/Procedure` - Procedures
- `/fhir/ServiceRequest` - Orders and referrals

## File Structure

```
src/backend/
├── README.md              # This file
├── config.py              # Shared configuration
├── sara_model.py          # GPU model service (Modal)
├── sara_agent.py          # Agent orchestrator (Modal)
├── fhir_server.py         # FHIR server (Modal)
├── Dockerfile.fhir        # Multi-stage Dockerfile for FHIR
├── agent.py               # Agent class (orchestration logic)
├── test_agent.py          # Agent tests
├── test_services.py       # Service integration tests
└── utils/
    ├── __init__.py
    ├── parser.py          # GET/POST/FINISH action parser
    ├── fhir_client.py     # Async FHIR HTTP client
    ├── test_parser.py     # Parser tests
    └── test_fhir_client.py # FHIR client tests
```

## Deployment

### Prerequisites

```bash
# Install Modal CLI
pip install modal

# Authenticate with Modal
modal setup
```

### Deploy All Services

```bash
# Deploy model (A100 GPU)
modal deploy src/backend/sara_model.py

# Deploy FHIR server
modal deploy src/backend/fhir_server.py

# Deploy agent (depends on model + FHIR)
modal deploy src/backend/sara_agent.py
```

### Verify Deployments

```bash
# Check model endpoint
curl https://nadhari--sara-model-serve.modal.run/health

# Check FHIR server
curl https://nadhari--fhir-server-serve.modal.run/fhir/metadata

# Check agent endpoint
curl https://nadhari--sara-agent-api.modal.run/health
```

## Local Development

### Run FHIR Server Locally (via Docker)

```bash
docker run -p 8080:8080 jyxsu6/medagentbench:latest
```

### Run Tests

```bash
# All backend tests
pytest src/backend/ -v

# Specific test files
pytest src/backend/utils/test_parser.py -v
pytest src/backend/test_agent.py -v
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SARA_URL` | Modal URL | Sara model endpoint |
| `FHIR_URL` | Modal URL | FHIR server base URL |

## API Reference

### POST /api/run

Execute a clinical task with SSE streaming.

**Request:**
```json
{
  "taskId": "task1",
  "prompt": "What's the MRN of patient John Doe?",
  "context": "It's 2023-11-13T10:15:00+00:00 now."
}
```

**Response:** Server-Sent Events stream

```
event: status
data: {"status": "thinking"}

event: tool_call
data: {"id": "call_1", "tool": "GET /fhir/Patient", "args": {"name": "John Doe"}}

event: tool_result
data: {"id": "call_1", "result": {...}, "status": "success"}

event: complete
data: {"response": "The patient's MRN is S1234567."}
```

### GET /api/tasks

List available demo tasks.

**Response:**
```json
{
  "tasks": [
    {
      "id": "task1",
      "name": "Patient Lookup",
      "description": "Find patient by name and DOB"
    },
    ...
  ]
}
```

## The 10 Demo Tasks

| ID | Name | Description |
|----|------|-------------|
| task1 | Patient Lookup | Find MRN by name and DOB |
| task2 | Patient Age | Calculate age from DOB |
| task3 | Record Vitals | Record blood pressure |
| task4 | Lab Results | Check magnesium level |
| task5 | Check & Order | Check Mg, order if low |
| task6 | Average CBG | Calculate 24h glucose average |
| task7 | Recent CBG | Get most recent glucose |
| task8 | Order Referral | Create orthopedic referral |
| task9 | K+ Check & Order | Check potassium, order + lab |
| task10 | HbA1C Check | Check HbA1C, order if old |

## Troubleshooting

### Cold Start Timeouts

Modal services have cold start times:
- **Sara Model (GPU):** 30-60s (model loading)
- **FHIR Server:** 20-30s (Java/Spring Boot)
- **Sara Agent:** 5-10s (Python)

The frontend handles this with:
- 3-minute timeout
- Automatic retry (2 attempts)
- "Warming up" indicator after 5s

### Common Issues

1. **401 on Sara Model:** Check HuggingFace token is set correctly
2. **FHIR 404:** Verify patient MRN exists in synthetic data
3. **Agent timeout:** Increase `AGENT_TIMEOUT` in config

## Related Documentation

- [CLAUDE.md](/CLAUDE.md) - Project overview
- [Frontend README](/src/frontend/README.md) - Frontend documentation
- [Design Document](/docs/plans/2025-02-16-sara-platform-design.md) - Full design
- [MedAgentBench](https://github.com/stanfordmlgroup/MedAgentBench) - Original benchmark
