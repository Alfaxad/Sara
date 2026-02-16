# Sara Project Context

> **Purpose:** Context file for Claude Code sessions. Read this first when resuming work.

## Project Overview

Sara is a clinical workflow agent platform — "Devin for Healthcare/Physicians."

- **Model:** Sara 1.5 4B (fine-tuned MedGemma on MedAgentBench) — private HF repo: `Alfaxad/Sara-1.5-4B-it`
- **Backend:** Modal (Sara model on A100 + FHIR server + Agent orchestrator)
- **Frontend:** Vercel (Next.js with custom design system)
- **Design System:** `ui-design-guidelines/SKILL.md`

## Current Status

- [x] Fine-tuning complete (Sara 1.5 4B)
- [x] Benchmarking complete (66.7% accuracy, SOTA on 3 tasks)
- [x] Design document approved
- [x] Phase 1: Modal Backend
- [x] Phase 2: Agent Orchestrator
- [x] Phase 3: Frontend Foundation
- [x] Phase 4: Chat Experience
- [x] Phase 5: Artifact Rendering
- [x] Phase 6: Polish & Deploy

## Project Structure

```
sara/
├── CLAUDE.md                              # This file
├── docs/plans/
│   ├── 2025-02-16-sara-platform-design.md # Full design doc
│   └── 2025-02-16-sara-platform-implementation.md
├── ui-design-guidelines/
│   └── SKILL.md                           # Design system (MUST follow)
├── src/
│   ├── backend/                           # Modal services
│   │   ├── config.py                      # Shared config
│   │   ├── sara_model.py                  # A100 GPU model endpoint
│   │   ├── sara_agent.py                  # FastAPI + SSE streaming
│   │   ├── fhir_server.py                 # FHIR R4 Docker
│   │   ├── agent.py                       # Agent orchestrator
│   │   └── utils/
│   │       ├── parser.py                  # GET/POST/FINISH parser
│   │       └── fhir_client.py             # Async FHIR client
│   └── frontend/                          # Next.js app
│       ├── src/app/                       # Pages (/, /chat/[taskId])
│       ├── src/components/                # UI, Chat, Landing, Artifacts
│       ├── src/hooks/                     # useStreaming, useChat
│       └── src/lib/                       # Utils, API, Tasks
└── MedAgentBench/                         # Original benchmark (reference)
```

## Key Decisions

| Decision | Choice |
|----------|--------|
| Agent Framework | Custom agent with Sara's GET/POST/FINISH format |
| Frontend | Custom Next.js (not Open WebUI fork) |
| Backend | Modal (all Python services) |
| Frontend Hosting | Vercel |
| Task UX | Click card → auto-run → stream → split-screen artifact |
| Design | SKILL.md (Playfair + DM Sans, clinical blue #6A9BCC, dark mode) |

## Architecture

```
Modal:
  sara-model (A100 GPU) ──► /v1/chat/completions
  sara-agent (CPU)      ──► /api/run (SSE streaming)
  fhir-server (CPU)     ──► /fhir/* (HAPI FHIR R4)

Vercel:
  Next.js frontend ──► Split-screen chat + artifacts
```

## Commands

```bash
# Backend deployment (Modal)
modal deploy src/backend/sara_model.py
modal deploy src/backend/fhir_server.py
modal deploy src/backend/sara_agent.py

# Frontend development
cd src/frontend && npm run dev

# Frontend deployment (Vercel)
cd src/frontend && vercel

# Run tests
pytest src/backend/ -v
```

## HuggingFace Secret

Sara model is in a private repo. Requires:
```bash
modal secret create huggingface HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

## Design Principles (from SKILL.md)

1. **Calm over clever** — Muted palettes, generous whitespace
2. **Trust through transparency** — Show data provenance, AI reasoning
3. **Speed equals safety** — Sub-50ms interactions, skeleton loaders
4. **Dark mode primary** — Physicians work in dim environments
5. **No ugly JSON** — Parse and render beautifully, raw data collapsed

## The 10 Demo Tasks

1. 🔍 Patient Lookup
2. 💊 Medication Refill
3. 🧪 Lab Order
4. 📋 Allergy Check
5. 💉 Dosing Calculation
6. 📊 Disease Summary
7. 🩺 Vitals Recording
8. 📝 Lab Interpretation
9. ⚕️ Condition Lookup
10. 🔬 Procedure History

---

*When in doubt, read `docs/plans/2025-02-16-sara-platform-design.md` and `ui-design-guidelines/SKILL.md`.*
