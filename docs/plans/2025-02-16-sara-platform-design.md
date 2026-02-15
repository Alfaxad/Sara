# Sara Platform Design Document

> **Date:** 2025-02-16
> **Status:** Approved
> **Author:** Claude + Alfaxad

---

## Executive Summary

Sara is a clinical workflow agent platform — "Devin for Healthcare/Physicians." It combines a fine-tuned 4B parameter medical LLM (Sara 1.5) with a FHIR-based EHR backend, wrapped in a beautiful, production-grade interface that inspires physicians about the future of clinical AI.

### Key Decisions

| Decision | Choice |
|----------|--------|
| **Agent Harness** | Hybrid (ADK framework + custom BaseAgent for Sara's GET/POST/FINISH format) |
| **Frontend** | Custom Next.js + Lightweight Chat with artifacts (learning from Open WebUI patterns) |
| **Backend Deployment** | Modal (Sara model + FHIR server + ADK agent) |
| **Frontend Deployment** | Vercel |
| **Task Interaction** | Click card → Chat opens → Auto-runs → Streams results → Split-screen artifact |
| **Patient Selection** | Default curated case per task (different patients across tasks) |
| **Artifact Panel** | Task-specific stacked cards, content intelligently split between chat and artifact |
| **Data Visualization** | JSON Crack (graphs) + fhir-react (FHIR resources) + SKILL.md design system |
| **Design System** | SKILL.md (Playfair + DM Sans, clinical blue + sage green, dark mode primary) |

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MODAL                                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         sara-platform (GPU App)                       │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌─────────────────────────────┐    │   │
│  │  │ Sara Model  │  │    Agent Orchestrator       │    │   │
│  │  │   A100 40GB │  │    (FastAPI + ADK)          │    │   │
│  │  │   GPU       │  │         CPU only            │    │   │
│  │  └─────────────┘  └─────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         fhir-server (CPU App)                         │   │
│  │         Docker: jyxsu6/medagentbench                  │   │
│  │         CPU only, no GPU                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTPS (SSE streaming)
┌─────────────────────────────────────────────────────────────┐
│                    VERCEL (Next.js)                          │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │     Chat Panel      │    │      Artifact Panel         │ │
│  │  • Task cards       │    │  • fhir-react components    │ │
│  │  • Streaming msgs   │    │  • JSON Crack graphs        │ │
│  │  • Tool call status │    │  • Stacked result cards     │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. System Components

### 2.1 Modal Backend Services

| Service | Runtime | Resources | Endpoint | Purpose |
|---------|---------|-----------|----------|---------|
| **sara-model** | Modal Function | A100 40GB, 15min warm | `/v1/chat/completions` | OpenAI-compatible Sara inference |
| **sara-agent** | Modal Function | CPU, 2GB RAM | `/api/run` (SSE) | ADK orchestrator, streams results |
| **fhir-server** | Modal Function | CPU, 4GB RAM, Docker | Internal `:8080/fhir` | HAPI FHIR R4 with 100 patients |

**Note:** Sara model requires HuggingFace secret (`modal secret create huggingface HF_TOKEN=hf_xxx`) for private repo access.

### 2.2 Vercel Frontend

| Component | Tech | Purpose |
|-----------|------|---------|
| **Landing Page** | Next.js + Tailwind | 10 task cards, Sara branding, disclaimer |
| **Chat Panel** | React + SSE | Streaming messages, tool call status |
| **Artifact Panel** | React + fhir-react + JSON Crack | Task-specific rendered results |
| **Design System** | CSS Variables | SKILL.md tokens (colors, typography, spacing) |

### 2.3 Agent Architecture (ADK Hybrid)

```python
class SaraAgent(BaseAgent):
    """Custom ADK agent that handles Sara's text-based tool calling"""

    def __init__(self):
        self.sara_client = OpenAI(base_url=SARA_MODAL_URL)
        self.fhir_client = FHIRClient(base_url=FHIR_MODAL_URL)

    async def run(self, task: str) -> AsyncGenerator[Event]:
        messages = [{"role": "user", "content": task}]

        for round in range(MAX_ROUNDS):  # max 8 rounds
            # 1. Call Sara
            response = await self.sara_client.chat(messages)
            yield AgentEvent(type="thinking", content=response)

            # 2. Parse output (GET/POST/FINISH)
            action = self.parse_action(response)

            if action.type == "FINISH":
                yield AgentEvent(type="complete", result=action.answer)
                break

            # 3. Execute FHIR call
            fhir_result = await self.fhir_client.execute(action)
            yield AgentEvent(type="tool_call", tool=action.type, result=fhir_result)

            # 4. Inject result into context
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Result: {fhir_result}"})
```

---

## 3. Frontend Design

### 3.1 Page Structure

```
LANDING (/)
┌─────────────────────────────────────────────────────────────┐
│  ✦ Sara - Clinical Workflow Agent                           │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Task 1 │ │ Task 2 │ │ Task 3 │ │ Task 4 │ │ Task 5 │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Task 6 │ │ Task 7 │ │ Task 8 │ │ Task 9 │ │Task 10 │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                              │
│  ⚠️ Disclaimer: For demonstration purposes only...          │
└─────────────────────────────────────────────────────────────┘

CHAT VIEW (/chat/:taskId) - Split Screen
┌────────────────────────────┬────────────────────────────────┐
│       CHAT PANEL           │        ARTIFACT PANEL          │
│                            │                                │
│  👤 User query             │  KEY FINDINGS                  │
│                            │  ┌────────────────────────┐    │
│  ✦ Sara                    │  │ Patient card / Labs /  │    │
│  ● Fetching data... ✓      │  │ Medications / etc.     │    │
│                            │  └────────────────────────┘    │
│  Response streams here     │                                │
│                            │  [View Source ▾]               │
│  💬 Follow-up input        │  [Show Reasoning ▾]            │
└────────────────────────────┴────────────────────────────────┘
```

### 3.2 Component Hierarchy

```
app/
├── layout.tsx
├── page.tsx                    # Landing
├── chat/[taskId]/page.tsx      # Chat view

components/
├── landing/
│   ├── Hero.tsx
│   ├── TaskCard.tsx
│   ├── TaskGrid.tsx
│   └── Disclaimer.tsx
├── chat/
│   ├── ChatPanel.tsx
│   ├── MessageList.tsx
│   ├── UserMessage.tsx
│   ├── AssistantMessage.tsx
│   ├── ToolCallStatus.tsx
│   ├── ThinkingIndicator.tsx
│   └── ChatInput.tsx
├── artifacts/
│   ├── ArtifactPanel.tsx
│   ├── PatientCard.tsx
│   ├── LabResultsCard.tsx
│   ├── MedicationCard.tsx
│   ├── ConditionCard.tsx
│   ├── ProcedureCard.tsx
│   ├── FindingsCard.tsx
│   ├── ActionsCard.tsx
│   ├── SourceViewer.tsx
│   └── ReasoningPanel.tsx
├── ui/
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Badge.tsx
│   ├── Skeleton.tsx
│   ├── Collapsible.tsx
│   └── SplitPane.tsx
└── icons/
    ├── SaraIcon.tsx
    ├── TaskIcons.tsx
    └── StatusIcons.tsx
```

### 3.3 Design Tokens (from SKILL.md)

```css
:root {
  /* Backgrounds */
  --sara-bg-base: #0B0F14;
  --sara-bg-surface: #111820;
  --sara-bg-elevated: #1A2230;
  --sara-bg-subtle: #222D3D;

  /* Text */
  --sara-text-primary: #E8ECF1;
  --sara-text-secondary: #8899AA;
  --sara-text-muted: #556677;

  /* Accent */
  --sara-accent: #6A9BCC;         /* Clinical blue */
  --sara-accent-hover: #7DAAD6;
  --sara-secondary: #788C5D;       /* Sage green */

  /* Semantic */
  --sara-critical: #EF4444;
  --sara-warning: #F59E0B;
  --sara-success: #10B981;
  --sara-info: #3B82F6;

  /* Typography */
  --font-display: 'Playfair Display', serif;
  --font-body: 'DM Sans', sans-serif;
}
```

---

## 4. Data Flow & API Design

### 4.1 Request Flow

```
Frontend                    sara-agent              sara-model           fhir-server
    │                           │                       │                     │
    │  POST /api/run            │                       │                     │
    │  {taskId, prompt}         │                       │                     │
    │──────────────────────────>│                       │                     │
    │                           │                       │                     │
    │  SSE: event: status       │                       │                     │
    │<──────────────────────────│                       │                     │
    │                           │  POST /v1/chat        │                     │
    │                           │──────────────────────>│                     │
    │  SSE: event: thinking     │<──────────────────────│                     │
    │<──────────────────────────│  "GET /Patient?..."   │                     │
    │                           │                       │                     │
    │  SSE: event: tool_call    │  GET /fhir/Patient    │                     │
    │<──────────────────────────│─────────────────────────────────────────────>│
    │                           │<─────────────────────────────────────────────│
    │  SSE: event: tool_result  │  {Bundle...}          │                     │
    │<──────────────────────────│                       │                     │
    │                           │                       │                     │
    │  SSE: event: complete     │                       │                     │
    │  {result, artifacts}      │                       │                     │
    │<──────────────────────────│                       │                     │
```

### 4.2 SSE Event Types

| Event | Purpose | Frontend Action |
|-------|---------|-----------------|
| `status` | Agent lifecycle | Show status indicator |
| `thinking` | Sara's internal reasoning | Display in chat (italic, muted) |
| `tool_call` | FHIR operation started | Show spinner in ToolCallStatus |
| `tool_result` | FHIR operation complete | Update ToolCallStatus with ✓ |
| `assistant` | Sara's user-facing message | Display in chat bubble |
| `complete` | Task finished | Render artifact panel, enable input |
| `error` | Something failed | Show error state, retry option |

### 4.3 API Endpoint

```typescript
// POST /api/run
{
  "taskId": "task1",
  "prompt": "Find the MRN..."
}

// SSE Response
event: status
data: {"phase": "starting", "message": "Connecting to Sara..."}

event: tool_call
data: {"id": "tc_001", "tool": "GET", "endpoint": "/Patient", "status": "running"}

event: tool_result
data: {"id": "tc_001", "status": "success", "duration_ms": 342}

event: assistant
data: {"content": "Found patient John Smith with MRN S6200102."}

event: complete
data: {
  "success": true,
  "answer": "S6200102",
  "artifacts": [{"type": "patient_summary", "data": {...}}],
  "usage": {"rounds": 1, "total_tokens": 1247, "duration_ms": 1893}
}
```

---

## 5. Task Definitions

### 5.1 The 10 Demo Tasks

| ID | Task | Icon | Sample Prompt | Artifacts |
|----|------|------|---------------|-----------|
| `task1` | Patient Lookup | 🔍 | "What's the MRN of the patient with name John Smith and DOB of 1985-03-15?" | patient_summary |
| `task2` | Medication Refill | 💊 | "Refill the current Metformin prescription for patient S6200102" | medication_card |
| `task3` | Lab Order | 🧪 | "Order a lipid panel for patient S1032702" | service_request_card |
| `task4` | Allergy Check | 📋 | "Check if patient S2874590 has any documented allergies before prescribing penicillin" | allergy_list |
| `task5` | Dosing Calculation | 💉 | "Calculate the appropriate Metformin dose for patient S9203482 based on their renal function" | dosing_card |
| `task6` | Disease Summary | 📊 | "Provide a diabetes management summary for patient S6200102" | condition_timeline |
| `task7` | Vitals Recording | 🩺 | "Record blood pressure 128/82 mmHg for patient S7194920" | vitals_card |
| `task8` | Lab Interpretation | 📝 | "Interpret the most recent metabolic panel for patient S4820395" | lab_results_card |
| `task9` | Condition Lookup | ⚕️ | "What active conditions does patient S3029402 have documented?" | condition_card |
| `task10` | Procedure History | 🔬 | "List all procedures patient S8827743 has undergone in the past 2 years" | procedure_list |

### 5.2 Artifact Types by Task

| Content | Where it Shows |
|---------|----------------|
| Sara's conversational response | Chat panel |
| Tool call progress (● Fetching... ✓) | Chat panel |
| Final answer summary | Chat panel |
| Structured patient data | Artifact panel |
| Lab values with colors | Artifact panel |
| Created resources (Rx, orders) | Artifact panel |
| JSON source data | Artifact panel (collapsed) |
| Reasoning chain | Artifact panel (collapsed) |

---

## 6. Modal Deployment

### 6.1 File Structure

```
sara/
├── modal/
│   ├── __init__.py
│   ├── config.py
│   ├── sara_model.py      # A100 GPU
│   ├── sara_agent.py      # CPU, FastAPI
│   ├── fhir_server.py     # CPU, Docker
│   ├── agent.py           # SaraAgent class
│   └── utils/
│       ├── fhir_client.py
│       └── parser.py
```

### 6.2 Deployment Commands

```bash
# Create HuggingFace secret (required for private Sara model)
modal secret create huggingface HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx

# Deploy all services
modal deploy modal/sara_model.py
modal deploy modal/fhir_server.py
modal deploy modal/sara_agent.py

# Get URLs
modal app list
```

---

## 7. Vercel Frontend

### 7.1 Project Structure

```
sara-frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── chat/[taskId]/page.tsx
├── components/
│   ├── landing/
│   ├── chat/
│   ├── artifacts/
│   ├── ui/
│   └── icons/
├── lib/
│   ├── tasks.ts
│   ├── api.ts
│   ├── streaming.ts
│   └── fhir.ts
├── hooks/
│   ├── useChat.ts
│   ├── useStreaming.ts
│   └── useArtifacts.ts
└── tailwind.config.ts
```

### 7.2 Key Dependencies

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "fhir-react": "^1.0.0",
    "eventsource-parser": "^1.1.0",
    "lucide-react": "^0.300.0",
    "tailwindcss": "^3.4.0"
  }
}
```

### 7.3 Environment Variables

```bash
NEXT_PUBLIC_MODAL_URL=https://xxx--sara-agent-api.modal.run
```

---

## 8. Implementation Phases

| Phase | Focus | Est. Time |
|-------|-------|-----------|
| **Phase 1** | Modal Backend (Sara model + FHIR server) | 1-2 days |
| **Phase 2** | Agent Orchestrator (ADK hybrid + SSE) | 2-3 days |
| **Phase 3** | Frontend Foundation (Next.js + design system) | 2-3 days |
| **Phase 4** | Chat Experience (streaming + split screen) | 2-3 days |
| **Phase 5** | Artifact Rendering (fhir-react + JSON Crack) | 3-4 days |
| **Phase 6** | Polish & Deploy (animations + Vercel) | 1-2 days |

**Total Estimated Time: 12-17 days**

---

## 9. Success Criteria

1. **Demo Flow:** Click task card → auto-runs → streams results → renders artifacts
2. **Performance:** < 5s for simple tasks, < 15s for complex multi-step tasks
3. **Design:** Matches SKILL.md exactly (dark mode, colors, typography, animations)
4. **Reliability:** Graceful error handling, retry capability
5. **Inspiration:** Physicians say "wow" when they see it

---

## Appendix A: Reference Documents

- `sara-overview.md` — Agent architecture and task types
- `sara_clinical_workflow_agent_plan_v2.md` — Original project plan
- `ui-design-guidelines/SKILL.md` — Complete design system
- `adk-docs/` — Google ADK documentation
- `modal-docs/` — Modal deployment guides
- `open-webui/` — Reference implementation for streaming/artifacts
- `fhir-react/` — FHIR resource rendering library
- `jsoncrack.com/` — JSON visualization

---

*Sara's interface should feel like a calm, competent colleague — always prepared, never overwhelming, and transparent about every decision it makes.*
