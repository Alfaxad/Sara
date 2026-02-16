# Enhanced Sara Demo UI Design

**Date**: 2025-02-16
**Status**: Approved
**Approach**: Enhanced Cards (build on existing artifact card system)

---

## Overview

Enhance the Sara clinical workflow agent demo UI with:
1. Workflow timeline showing human-readable action summaries during execution
2. Interactive FHIR cards with inline expansion for clinical exploration
3. Task-specific final answer rendering
4. Demo mode restrictions (no follow-up input)
5. Updated disclaimer text on landing page

---

## Section 1: Workflow Timeline

### Concept
Replace generic "Calling tool..." messages with a visual timeline showing Sara's steps in human-readable form.

### Visual Design
```
┌─────────────────────────────────────────────────┐
│ Sara's Progress                                 │
├─────────────────────────────────────────────────┤
│  ✓  Searching patient records                   │
│  │                                              │
│  ●  Retrieving lab results              ← pulse │
│  │                                              │
│  ○  Analyzing findings                          │
└─────────────────────────────────────────────────┘
```

### States
- `○` Pending (muted)
- `●` In progress (pulsing animation)
- `✓` Complete (accent color)

### Action Parsing Rules
| Raw Action | Human-Readable |
|------------|----------------|
| `GET /Patient?name=...` | "Searching patient records" |
| `GET /Observation?...` | "Retrieving lab results" |
| `POST /Observation` | "Recording measurement" |
| `POST /MedicationRequest` | "Ordering medication" |
| `POST /ServiceRequest` | "Creating referral" |
| `FINISH(...)` | "Completing task" |

### Component
- New `WorkflowTimeline.tsx` component
- Displayed in chat area during execution
- Replaces current tool_call messages with timeline view

---

## Section 2: Enhanced FHIR Cards with Inline Expansion

### Concept
Each FHIR resource type gets a beautifully rendered card that summarizes key clinical data, with expandable sections for deeper exploration—all without showing raw JSON.

### Card Structure
```
┌─────────────────────────────────────────────────┐
│ ● Patient                          [▼ Expand]  │
├─────────────────────────────────────────────────┤
│  Name        Peter Stafford                     │
│  MRN         S2874099                          │
│  DOB         Dec 29, 1932 (91 years)           │
│  Gender      Male                              │
├─────────────────────────────────────────────────┤
│  ▸ Contact Information                         │
│  ▸ Identifiers (3)                             │
│  ▸ Communication Preferences                   │
└─────────────────────────────────────────────────┘
```

### Expansion Behavior
- Collapsed sections show count badges (e.g., "Identifiers (3)")
- Clicking expands inline with smooth animation
- Nested data renders as styled key-value pairs or mini-cards
- Arrays render as numbered lists with consistent styling
- No JSON braces, brackets, or quotes visible to user

### Card Types by Task

| Task | Primary Card | Expandable Sections |
|------|--------------|---------------------|
| Patient Lookup | PatientCard | Contact, Identifiers |
| Patient Age | PatientCard | (minimal, just age calc) |
| Record Vitals | ObservationCard | Components, Reference Ranges |
| Lab Results | LabResultsCard | Interpretation, Method |
| Check & Order | LabResultsCard + MedicationCard | Dosing, Status |
| Average/Recent CBG | LabResultsCard | Time Series (if multiple) |
| Order Referral | ServiceRequestCard | Reason, Notes |
| K+ Check & Order | LabResultsCard + MedicationCard + LabOrderCard | Follow-up timing |
| HbA1C Check | LabResultsCard | Historical comparison |

### Styling
- Monochromatic with subtle `--sara-border` separators
- Section headers use `text-body-small` with muted color
- Values use `text-body` with primary color
- Expand icons are subtle chevrons that rotate on open

---

## Section 3: Task-Specific Final Answer Card

### Concept
When Sara completes a task, the FINISH() result is parsed and rendered as a contextual summary card tailored to the task type.

### Card Structure
```
┌─────────────────────────────────────────────────┐
│ ✓ Result                                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  Magnesium Level                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  2.1 mg/dL                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✓ Within normal range (1.7-2.2 mg/dL)         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Task-Specific Renderings

| Task | Final Answer Format |
|------|---------------------|
| Patient Lookup | **MRN**: `S2874099` with patient name confirmation |
| Patient Age | **Age**: `91 years` with DOB context |
| Record Vitals | **Recorded**: BP reading with timestamp confirmation |
| Lab Results | **Value**: with units and normal range indicator |
| Check & Order | **Status**: Lab value + order confirmation with dosage |
| Average/Recent CBG | **Value**: with calculation note (avg of N readings) |
| Order Referral | **Referral Created**: Service type + reason summary |
| K+ Check & Order | **Multi-step**: Lab value + medication order + follow-up lab scheduled |
| HbA1C Check | **Value + Date**: with "new test ordered" if applicable |

### Visual Indicators
- `✓` checkmark for successful/normal results
- `!` for values requiring attention
- Large, prominent value display with clear units
- Subtle context line below (normal ranges, timestamps, etc.)

### Styling
- Card uses `--sara-bg-elevated` background
- Primary value uses larger `text-heading` style
- Status indicator uses `--sara-accent` for success states
- Consistent with monochromatic theme

---

## Section 4: UI Behavior Changes

### Demo Mode Restrictions

1. **Disable Follow-up Input**: After task completion, the ChatInput component will be disabled
   - Input field becomes read-only with placeholder: "Demo complete"
   - Send button hidden or disabled
   - No keyboard submit allowed
   - User can only view results and explore artifacts

2. **Reset Button**: The existing "Reset" button in header remains functional
   - Clicking reset clears all state and re-runs the task from scratch

### Landing Page Disclaimer Update

Replace the current "Research Demo Only" disclaimer with:

> **Disclaimer**: This demonstration is for illustrative purposes only and does not represent a finished or approved product. It is not representative of compliance to any regulations or standards for quality, safety or efficacy. Any real-world application would require additional development, training, and adaptation. The experience highlighted in this demo shows MedGemma's baseline capability for the displayed task and is intended to help developers and users explore possible applications and inspire further development.

**Placement**: At the bottom of the landing page, styled as subtle `text-caption` with `text-sara-text-muted`, maintaining the monochromatic aesthetic.

---

## Technical Notes

### Files to Modify
- `src/frontend/src/components/chat/ChatInput.tsx` - Disable after completion
- `src/frontend/src/components/chat/MessageList.tsx` - Integrate WorkflowTimeline
- `src/frontend/src/hooks/useChat.ts` - Track workflow steps
- `src/frontend/src/app/page.tsx` - Update disclaimer text

### New Components to Create
- `src/frontend/src/components/workflow/WorkflowTimeline.tsx`
- `src/frontend/src/components/artifacts/FinalAnswerCard.tsx`
- `src/frontend/src/components/artifacts/ExpandableSection.tsx`
- Enhanced versions of existing cards with expansion support

### Existing Components to Enhance
- `PatientCard.tsx` - Add expandable sections
- `LabResultsCard.tsx` - Add expandable sections
- `MedicationCard.tsx` - Add expandable sections
- `ArtifactPanel.tsx` - Integrate FinalAnswerCard

### Design System
- All new components follow existing monochromatic theme
- Use existing CSS variables (`--sara-*`)
- Animations use existing `animate-sara-*` classes
- Typography uses existing text classes
