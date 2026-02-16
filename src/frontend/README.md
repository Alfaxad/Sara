# Sara Frontend

> Next.js frontend for the Sara Clinical Workflow Agent — "Devin for Healthcare"

## Overview

A modern, dark-mode-first clinical interface built with Next.js 14, featuring real-time SSE streaming, split-screen artifact rendering, and a custom medical design system.

**Live Demo:** https://sara-frontend.vercel.app

## Features

- **Real-time Streaming** — Server-Sent Events (SSE) for live agent responses
- **Split-screen Layout** — Chat on left, FHIR artifacts on right
- **Beautiful FHIR Rendering** — Semantic cards for Patient, Observation, Medication, etc.
- **Dark Mode Primary** — Designed for clinical environments (dim lighting)
- **Responsive Design** — Works on desktop and tablet
- **Auto-retry** — Handles Modal cold starts gracefully

## Screenshots

```
┌────────────────────────────────────────────────────────────────────┐
│  ← HbA1C Check                                    🔄 Reset         │
│  Context: It's 2023-11-13...                                       │
├─────────────────────────────────┬──────────────────────────────────┤
│                                 │                                  │
│  ┌─────────────────────────┐   │   📋 FHIR Resources (2)          │
│  │ What's the last HbA1C   │   │                                  │
│  │ for patient S1311412?   │   │   ┌────────────────────────┐    │
│  └─────────────────────────┘   │   │ 👤 Patient             │    │
│                                 │   │    John Smith          │    │
│  ⚙️ GET /fhir/Observation ✓    │   │    MRN: S1311412       │    │
│                                 │   │    DOB: 1955-03-15     │    │
│  ┌─────────────────────────┐   │   └────────────────────────┘    │
│  │ The last HbA1C was 5.9% │   │                                  │
│  │ recorded on 2023-11-12. │   │   ┌────────────────────────┐    │
│  │ Recent - no new order.  │   │   │ 🧪 Observation         │    │
│  └─────────────────────────┘   │   │    HbA1C: 5.9%         │    │
│                                 │   │    Date: 2023-11-12    │    │
│  [Ask a follow-up...]     ▶️   │   └────────────────────────┘    │
│                                 │                                  │
└─────────────────────────────────┴──────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| UI Components | Custom (shadcn/ui inspired) |
| State | React hooks (useState, useCallback) |
| Streaming | eventsource-parser |
| Fonts | Playfair Display + DM Sans |
| Icons | Lucide React |

## Project Structure

```
src/frontend/
├── README.md                    # This file
├── package.json                 # Dependencies
├── next.config.mjs              # Next.js config
├── tailwind.config.ts           # Tailwind + design tokens
├── tsconfig.json                # TypeScript config
└── src/
    ├── app/
    │   ├── layout.tsx           # Root layout (fonts, metadata)
    │   ├── page.tsx             # Landing page (task grid)
    │   ├── globals.css          # Global styles + CSS variables
    │   └── chat/
    │       └── [taskId]/
    │           └── page.tsx     # Chat page (split-screen)
    ├── components/
    │   ├── ui/                  # Base UI components
    │   │   ├── Button.tsx
    │   │   ├── Card.tsx
    │   │   ├── SplitPane.tsx    # Resizable split view
    │   │   ├── ErrorBoundary.tsx
    │   │   └── index.ts
    │   ├── chat/                # Chat components
    │   │   ├── ChatPanel.tsx    # Main chat interface
    │   │   ├── MessageBubble.tsx
    │   │   ├── ToolCallBubble.tsx
    │   │   ├── ThinkingIndicator.tsx
    │   │   └── index.ts
    │   ├── artifacts/           # FHIR resource cards
    │   │   ├── PatientCard.tsx
    │   │   ├── LabResultsCard.tsx
    │   │   ├── MedicationCard.tsx
    │   │   ├── ConditionCard.tsx
    │   │   └── ProcedureCard.tsx
    │   ├── landing/             # Landing page components
    │   │   ├── TaskGrid.tsx
    │   │   ├── TaskCard.tsx
    │   │   └── Header.tsx
    │   └── FhirResourceRenderer.tsx  # Smart FHIR renderer
    ├── hooks/
    │   ├── useChat.ts           # Chat state management
    │   └── useStreaming.ts      # SSE streaming logic
    └── lib/
        ├── api.ts               # API client + types
        ├── tasks.ts             # Demo task definitions
        └── utils.ts             # Utility functions (cn)
```

## Design System

Based on `ui-design-guidelines/SKILL.md`:

### Colors

```css
/* Primary Palette */
--sara-accent: #6A9BCC;        /* Clinical blue */
--sara-accent-hover: #5A8BBE;
--sara-accent-soft: rgba(106, 155, 204, 0.15);

/* Backgrounds (Dark Mode) */
--sara-bg-base: #0D0F12;       /* Deepest */
--sara-bg-surface: #14171C;    /* Cards */
--sara-bg-elevated: #1A1D24;   /* Modals */
--sara-bg-subtle: #21252D;     /* Hover states */

/* Text */
--sara-text-primary: #F5F5F7;
--sara-text-secondary: #A1A1A6;
--sara-text-muted: #6E6E73;

/* Semantic */
--sara-success: #34C759;
--sara-warning: #FF9F0A;
--sara-error: #FF453A;
```

### Typography

```css
/* Font Families */
--font-display: 'Playfair Display', serif;  /* Headlines */
--font-sans: 'DM Sans', sans-serif;         /* Body text */

/* Sizes */
--text-display-lg: 2.25rem;   /* 36px */
--text-display: 1.875rem;     /* 30px */
--text-heading: 1.25rem;      /* 20px */
--text-body: 0.9375rem;       /* 15px */
--text-caption: 0.8125rem;    /* 13px */
```

### Spacing & Radius

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */

--radius-sm: 0.375rem;   /* 6px - buttons */
--radius-md: 0.5rem;     /* 8px - cards */
--radius-lg: 0.75rem;    /* 12px - modals */
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd src/frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm run start
```

### Lint

```bash
npm run lint
```

## Environment Variables

Create `.env.local` for local development:

```bash
# Backend API URL (default: Modal production)
NEXT_PUBLIC_API_URL=https://nadhari--sara-agent-api.modal.run

# For local backend development:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd src/frontend
vercel

# Production deploy
vercel --prod
```

### Environment Variables on Vercel

Set in Vercel dashboard or via CLI:
```bash
vercel env add NEXT_PUBLIC_API_URL
```

## Key Components

### useStreaming Hook

Handles SSE connection with timeout, retry, and warmup detection:

```typescript
const { isLoading, error, startStream, stopStream, isWarmingUp } = useStreaming({
  onEvent: (event) => { /* handle SSE event */ },
  onComplete: () => { /* stream finished */ },
  onError: (error) => { /* handle error */ },
  onWarmingUp: () => { /* show warmup indicator */ },
});

// Configuration
const REQUEST_TIMEOUT_MS = 180000;  // 3 minutes
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 2000;
```

### useChat Hook

Manages chat state and auto-runs tasks:

```typescript
const {
  task,           // Current task definition
  messages,       // Chat message history
  artifacts,      // FHIR resources retrieved
  isLoading,      // Request in progress
  isComplete,     // Task finished
  isWarmingUp,    // Server cold start
  sendMessage,    // Send follow-up
  reset,          // Reset chat
} = useChat(taskId);
```

### FhirResourceRenderer

Automatically renders FHIR resources as semantic cards:

```typescript
<FhirResourceRenderer resource={fhirData} />

// Supported types:
// - Patient → PatientCard
// - Observation → LabResultsCard
// - MedicationRequest → MedicationCard
// - Condition → ConditionCard
// - Procedure → ProcedureCard
// - Bundle → Renders each entry
// - Others → GenericResourceCard
```

## The 10 Demo Tasks

| Task | Icon | Description |
|------|------|-------------|
| Patient Lookup | 🔍 | Find MRN by name and DOB |
| Patient Age | 📊 | Calculate age from DOB |
| Record Vitals | 🩺 | Record blood pressure |
| Lab Results | 🧪 | Check magnesium level |
| Check & Order | 💉 | Check Mg, order replacement |
| Average CBG | 📈 | Calculate 24h glucose average |
| Recent CBG | 📊 | Get most recent glucose |
| Order Referral | 📝 | Create orthopedic referral |
| K+ Check & Order | 💊 | Potassium check + order |
| HbA1C Check | 🔬 | Check HbA1C, order if needed |

## SSE Event Flow

```
Frontend                    Backend (Modal)
   │                              │
   ├─── POST /api/run ──────────►│
   │    { taskId, prompt }        │
   │                              │
   │◄──── event: status ──────────┤ "thinking"
   │                              │
   │◄──── event: tool_call ───────┤ GET /fhir/Patient
   │                              │
   │◄──── event: tool_result ─────┤ { Patient data }
   │                              │
   │◄──── event: complete ────────┤ Final answer
   │                              │
```

## Accessibility

- Semantic HTML (`<main>`, `<header>`, `<nav>`)
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Performance

- Static page generation where possible
- Dynamic imports for heavy components
- Optimized fonts via `next/font`
- Minimal JavaScript bundle
- SSE for real-time updates (no polling)

## Troubleshooting

### "Server is warming up" message

Modal services have cold starts. The frontend:
1. Shows warmup indicator after 5s
2. Retries automatically (2 attempts)
3. Has 3-minute total timeout

### Empty FHIR Resources panel

Artifacts only show for successful queries with data:
- Error responses are filtered out
- Empty bundles (total: 0) are filtered out

### Chat not auto-starting

Check browser console for errors. Common issues:
- API URL misconfigured
- CORS issues (shouldn't happen with Modal)
- Network connectivity

## Related Documentation

- [CLAUDE.md](/CLAUDE.md) - Project overview
- [Backend README](/src/backend/README.md) - Backend documentation
- [Design System](/ui-design-guidelines/SKILL.md) - Design tokens
- [Design Document](/docs/plans/2025-02-16-sara-platform-design.md) - Full design

## License

Private - All rights reserved
