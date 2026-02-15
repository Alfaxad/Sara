# Sara Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-grade clinical workflow agent platform with Modal backend (Sara model + FHIR server + ADK orchestrator) and Vercel frontend (Next.js chat with artifact rendering).

**Architecture:** Hybrid ADK agent wrapping Sara's GET/POST/FINISH text-based tool calling. Modal hosts all Python services (GPU for Sara, CPU for orchestrator and FHIR). Vercel serves Next.js frontend with SSE streaming to Modal backend. Split-screen UI with chat on left, task-specific artifacts on right.

**Tech Stack:** Python 3.12, Modal, FastAPI, Google ADK, OpenAI SDK, Next.js 14, React 18, Tailwind CSS, fhir-react, eventsource-parser

---

## Phase 1: Modal Backend

### Task 1.1: Update Sara Model Deployment

**Files:**
- Create: `modal/__init__.py`
- Create: `modal/config.py`
- Create: `modal/sara_model.py`

**Step 1: Create modal directory structure**

```bash
mkdir -p modal/utils
touch modal/__init__.py modal/utils/__init__.py
```

**Step 2: Create config.py with shared settings**

Create: `modal/config.py`

```python
"""Shared configuration for Sara Modal services."""

MODEL_NAME = "Alfaxad/Sara-1.5-4B-it"
MODEL_REVISION = "main"

MINUTES = 60
GPU_WARM_WINDOW = 15 * MINUTES
REQUEST_TIMEOUT = 10 * MINUTES

SARA_GPU = "A100"
SARA_CONCURRENT_INPUTS = 8

AGENT_CPU = 1.0
AGENT_MEMORY = 2048
AGENT_CONCURRENT_INPUTS = 50

FHIR_CPU = 2.0
FHIR_MEMORY = 4096
FHIR_CONCURRENT_INPUTS = 100
```

**Step 3: Create sara_model.py**

Create: `modal/sara_model.py` - OpenAI-compatible endpoint for Sara model on A100 GPU with HuggingFace secret for private repo access.

**Step 4: Test locally**

Run: `cd ~/Desktop/AI/Sara && modal run modal/sara_model.py`

**Step 5: Deploy**

Run: `modal deploy modal/sara_model.py`

**Step 6: Commit**

```bash
git add modal/
git commit -m "feat(modal): add Sara model deployment with A100 GPU"
```

---

### Task 1.2: FHIR Server Deployment

**Files:**
- Create: `modal/fhir_server.py`

Deploy MedAgentBench Docker image on Modal with CPU only.

**Step 1: Create fhir_server.py**

**Step 2: Test locally**

Run: `modal run modal/fhir_server.py`

**Step 3: Deploy**

Run: `modal deploy modal/fhir_server.py`

**Step 4: Commit**

```bash
git add modal/fhir_server.py
git commit -m "feat(modal): add FHIR server deployment"
```

---

### Task 1.3: Verify Services

**Files:**
- Create: `modal/test_services.py`

Integration test that verifies both services communicate.

---

## Phase 2: Agent Orchestrator

### Task 2.1: Action Parser

**Files:**
- Create: `modal/utils/parser.py`
- Create: `modal/utils/test_parser.py`

Parse Sara's GET/POST/FINISH output format.

### Task 2.2: FHIR Client

**Files:**
- Create: `modal/utils/fhir_client.py`
- Create: `modal/utils/test_fhir_client.py`

Async FHIR client for executing actions.

### Task 2.3: Sara Agent Core

**Files:**
- Create: `modal/agent.py`
- Create: `modal/test_agent.py`

Hybrid ADK agent with event streaming.

### Task 2.4: Agent API Endpoint

**Files:**
- Create: `modal/sara_agent.py`

FastAPI with SSE streaming endpoint.

---

## Phase 3: Frontend Foundation

### Task 3.1: Initialize Next.js

```bash
npx create-next-app@14 sara-frontend --typescript --tailwind --app
cd sara-frontend
npm install fhir-react eventsource-parser lucide-react clsx tailwind-merge
```

### Task 3.2: Design System

**Files:**
- Modify: `sara-frontend/src/app/globals.css` - Design tokens from SKILL.md
- Modify: `sara-frontend/tailwind.config.ts` - Tailwind integration
- Modify: `sara-frontend/src/app/layout.tsx` - Root layout

### Task 3.3: Base UI Components

**Files:**
- Create: `sara-frontend/src/components/ui/Card.tsx`
- Create: `sara-frontend/src/components/ui/Badge.tsx`
- Create: `sara-frontend/src/components/ui/Button.tsx`
- Create: `sara-frontend/src/components/ui/Skeleton.tsx`
- Create: `sara-frontend/src/lib/utils.ts`

### Task 3.4: Landing Page Components

**Files:**
- Create: `sara-frontend/src/lib/tasks.ts` - Task definitions
- Create: `sara-frontend/src/components/landing/Hero.tsx`
- Create: `sara-frontend/src/components/landing/TaskCard.tsx`
- Create: `sara-frontend/src/components/landing/TaskGrid.tsx`
- Create: `sara-frontend/src/components/landing/Disclaimer.tsx`

### Task 3.5: Wire Up Landing Page

**Files:**
- Modify: `sara-frontend/src/app/page.tsx`

---

## Phase 4: Chat Experience

### Task 4.1: Streaming Hook

**Files:**
- Create: `sara-frontend/src/hooks/useStreaming.ts`

SSE parsing using eventsource-parser.

### Task 4.2: Chat State Hook

**Files:**
- Create: `sara-frontend/src/hooks/useChat.ts`

State management for messages and artifacts.

### Task 4.3: Chat Components

**Files:**
- Create: `sara-frontend/src/components/chat/ChatPanel.tsx`
- Create: `sara-frontend/src/components/chat/MessageList.tsx`
- Create: `sara-frontend/src/components/chat/UserMessage.tsx`
- Create: `sara-frontend/src/components/chat/AssistantMessage.tsx`
- Create: `sara-frontend/src/components/chat/ToolCallStatus.tsx`
- Create: `sara-frontend/src/components/chat/ThinkingIndicator.tsx`
- Create: `sara-frontend/src/components/chat/ChatInput.tsx`

### Task 4.4: Split Pane

**Files:**
- Create: `sara-frontend/src/components/ui/SplitPane.tsx`

### Task 4.5: Chat Page

**Files:**
- Create: `sara-frontend/src/app/chat/[taskId]/page.tsx`

---

## Phase 5: Artifact Rendering

### Task 5.1: Artifact Panel

**Files:**
- Create: `sara-frontend/src/components/artifacts/ArtifactPanel.tsx`

### Task 5.2: FHIR Components

**Files:**
- Create: `sara-frontend/src/components/artifacts/PatientCard.tsx` - fhir-react wrapper
- Create: `sara-frontend/src/components/artifacts/LabResultsCard.tsx` - Semantic colors
- Create: `sara-frontend/src/components/artifacts/MedicationCard.tsx`
- Create: `sara-frontend/src/components/artifacts/ConditionCard.tsx`
- Create: `sara-frontend/src/components/artifacts/ProcedureCard.tsx`

### Task 5.3: Summary Components

**Files:**
- Create: `sara-frontend/src/components/artifacts/FindingsCard.tsx`
- Create: `sara-frontend/src/components/artifacts/ActionsCard.tsx`

### Task 5.4: Source Viewer

**Files:**
- Create: `sara-frontend/src/components/artifacts/SourceViewer.tsx` - JSON Crack integration

### Task 5.5: Reasoning Panel

**Files:**
- Create: `sara-frontend/src/components/artifacts/ReasoningPanel.tsx`

---

## Phase 6: Polish & Deploy

### Task 6.1: Error States

Add error handling and retry buttons.

### Task 6.2: Loading States

Add skeleton loaders matching content shape.

### Task 6.3: Accessibility

Test prefers-reduced-motion, focus states.

### Task 6.4: Meta & Assets

Add favicon, OG image, meta tags.

### Task 6.5: Vercel Config

**Files:**
- Create: `sara-frontend/.env.local`
- Create: `sara-frontend/vercel.json`

### Task 6.6: Deploy

```bash
cd sara-frontend
vercel
```

### Task 6.7: E2E Testing

Test all 10 tasks end-to-end.

---

## Environment Variables

### Modal Secrets (Required)

```bash
modal secret create huggingface HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

### Vercel Environment

```bash
NEXT_PUBLIC_MODAL_URL=https://xxx--sara-agent-api.modal.run
```

---

## Success Criteria

1. Modal backend deployed (Sara + FHIR + Agent)
2. Frontend deployed to Vercel
3. All 10 tasks execute successfully
4. SSE streaming works smoothly
5. Artifacts render correctly per task type
6. Design matches SKILL.md exactly
7. No ugly JSON visible to users
8. Graceful error handling

---

## File Checklist

**Modal Backend (10 files)**
```
modal/
├── __init__.py
├── config.py
├── sara_model.py
├── sara_agent.py
├── fhir_server.py
├── agent.py
├── test_agent.py
├── test_services.py
└── utils/
    ├── __init__.py
    ├── parser.py
    ├── test_parser.py
    ├── fhir_client.py
    └── test_fhir_client.py
```

**Frontend (40+ files)**
```
sara-frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   └── chat/[taskId]/page.tsx
│   ├── components/
│   │   ├── landing/ (4 files)
│   │   ├── chat/ (7 files)
│   │   ├── artifacts/ (10 files)
│   │   └── ui/ (6 files)
│   ├── hooks/ (3 files)
│   └── lib/ (3 files)
├── tailwind.config.ts
└── .env.local
```
