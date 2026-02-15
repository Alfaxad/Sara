# Sara Project Context

> **Purpose:** Context file for Claude Code sessions. Read this first when resuming work.

## Project Overview

Sara is a clinical workflow agent platform — "Devin for Healthcare/Physicians."

- **Model:** Sara 1.5 4B (fine-tuned MedGemma on MedAgentBench) — private HF repo: `Alfaxad/Sara-1.5-4B-it`
- **Backend:** Modal (Sara model on A100 + FHIR server + ADK orchestrator)
- **Frontend:** Vercel (Next.js with custom design system)
- **Design System:** `ui-design-guidelines/SKILL.md`

## Current Status

- [x] Fine-tuning complete (Sara 1.5 4B)
- [x] Benchmarking complete (66.7% accuracy, SOTA on 3 tasks)
- [x] Design document approved
- [ ] Phase 1: Modal Backend
- [ ] Phase 2: Agent Orchestrator
- [ ] Phase 3: Frontend Foundation
- [ ] Phase 4: Chat Experience
- [ ] Phase 5: Artifact Rendering
- [ ] Phase 6: Polish & Deploy

## Key Decisions

| Decision | Choice |
|----------|--------|
| Agent Framework | ADK Hybrid (ADK + custom BaseAgent for GET/POST/FINISH) |
| Frontend | Custom Next.js (not Open WebUI fork) |
| Backend | Modal (all Python services) |
| Frontend Hosting | Vercel |
| Task UX | Click card → auto-run → stream → split-screen artifact |
| Design | SKILL.md (Playfair + DM Sans, clinical blue #6A9BCC, dark mode) |

## Important Files

```
sara/
├── CLAUDE.md                              # This file
├── docs/plans/
│   └── 2025-02-16-sara-platform-design.md # Full design doc
├── ui-design-guidelines/
│   └── SKILL.md                           # Design system (MUST follow)
├── sara-overview.md                       # Agent architecture
├── sara_modal.py                          # Existing Modal deploy script
├── modal/                                 # Backend (to be built)
└── sara-frontend/                         # Frontend (to be built)
```

## Architecture

```
Modal:
  sara-model (A100 GPU) ──► /v1/chat/completions
  sara-agent (CPU)      ──► /api/run (SSE streaming)
  fhir-server (CPU)     ──► /fhir/* (HAPI FHIR R4)

Vercel:
  Next.js frontend ──► Split-screen chat + artifacts
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

## Commands

```bash
# Modal deployment
modal deploy modal/sara_model.py
modal deploy modal/fhir_server.py
modal deploy modal/sara_agent.py

# Frontend
cd sara-frontend && npm run dev
vercel deploy
```

## Next Steps

Start with **Phase 1: Modal Backend**:
1. Update sara_modal.py for A100 (currently H100)
2. Create fhir_server.py with Docker image
3. Test both services

Then proceed through Phases 2-6 as outlined in the design doc.

---

*When in doubt, read `docs/plans/2025-02-16-sara-platform-design.md` and `ui-design-guidelines/SKILL.md`.*
