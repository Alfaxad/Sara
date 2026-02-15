# Sara Design System — SKILL.md

> **Purpose:** This skill defines the visual language, interaction patterns, and design principles for all UI surfaces built for the Sara clinical workflow agent. Every artifact, component, dashboard, and interactive display must follow these guidelines to produce a cohesive, beautiful, and clinically safe experience.

---

## 1. Design Philosophy

Sara's design serves one mission: **physicians should care for patients, not computers.**

Every pixel must earn its place. If a visual element doesn't reduce cognitive load, surface critical information, or guide a clinical decision — remove it.

### The Three Laws

1. **Calm over clever.** Healthcare users are stressed, fatigued, and time-pressured. Never add visual noise for aesthetics alone. Muted palettes, generous whitespace, and restraint are features, not compromises.

2. **Trust through transparency.** Every piece of data must show its source. AI-generated content needs citations. Lab results need reference ranges. Nothing should feel like a black box. If Sara took an action, show _why_ and _from what evidence_.

3. **Speed equals safety.** In clinical settings, slow UI can be dangerous. Target sub-50ms interactions. Use skeleton loaders, optimistic updates, and progressive rendering. A physician waiting on a spinner is a physician not treating a patient.

---

## 2. Typography

Sara uses a **serif + sans-serif pairing** — editorial warmth from the serif, clinical clarity from the sans-serif.

### Font Stack

| Role | Font | Weight Range | Usage |
|------|------|-------------|-------|
| **Display / Hero** | Playfair Display | 400–900 | Page titles, patient names, summary headings, empty states |
| **Body / UI** | DM Sans | 100–1000 | Everything else: labels, body text, navigation, data tables, buttons, cards |

**Rule:** One great font at multiple weights beats five fonts every time. Use weight contrast (e.g., DM Sans 400 vs 700) to create hierarchy within a single typeface. Reserve Playfair Display for moments of emphasis — never for dense UI or data tables.

### Embedding Fonts

Add this to the `<head>` of every HTML artifact:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap" rel="stylesheet">
```

### CSS Classes

```css
/* Primary UI font — used for all interface text */
.sara-body {
  font-family: "DM Sans", sans-serif;
  font-optical-sizing: auto;
  font-weight: 400;
  font-style: normal;
}

/* Bold variant for labels, table headers, card titles */
.sara-label {
  font-family: "DM Sans", sans-serif;
  font-optical-sizing: auto;
  font-weight: 600;
  font-style: normal;
}

/* Display font — hero headings, patient names, summaries */
.sara-display {
  font-family: "Playfair Display", serif;
  font-optical-sizing: auto;
  font-weight: 700;
  font-style: normal;
}

/* Light display — empty states, welcome messages */
.sara-display-light {
  font-family: "Playfair Display", serif;
  font-optical-sizing: auto;
  font-weight: 400;
  font-style: italic;
}
```

### Type Scale

Use this scale consistently. Do not invent intermediate sizes.

| Token | Size | Weight | Font | Use |
|-------|------|--------|------|-----|
| `display-xl` | 36px / 2.25rem | 700 | Playfair Display | Page hero, patient name on detail view |
| `display-lg` | 28px / 1.75rem | 600 | Playfair Display | Section headings, summary titles |
| `heading` | 20px / 1.25rem | 600 | DM Sans | Card titles, panel headers |
| `subheading` | 16px / 1rem | 600 | DM Sans | Table headers, group labels |
| `body` | 15px / 0.9375rem | 400 | DM Sans | Default reading text |
| `body-small` | 13px / 0.8125rem | 400 | DM Sans | Secondary info, timestamps, metadata |
| `caption` | 11px / 0.6875rem | 500 | DM Sans | Badges, status pills, footnotes |

---

## 3. Color System

Sara uses a **low-saturation clinical palette** with high-contrast semantic colors for status and severity. The palette is designed to reduce eye strain during long shifts while making critical information unmissable.

**Why blue and green?** Sara's accent palette uses a **clinical blue** (`#6A9BCC`) as the primary agent color and a **sage green** (`#788C5D`) as the secondary. Blue signals trust, precision, and clinical authority — it's the color of scrubs, medical charts, and institutional confidence. Green signals health, vitality, and positive outcomes. Together they create a palette that feels unmistakably healthcare without falling into the sterile, generic "hospital blue" trap. The muted, desaturated tones keep things calm rather than corporate.

### Dark Mode (Primary)

Dark mode is the default. Physicians work in dimly lit environments — ORs, on-call rooms, night shifts. Dark mode is not an afterthought; it is the primary surface.

```css
:root {
  /* Backgrounds — layered depth, not flat black */
  --sara-bg-base:       #0B0F14;   /* deepest layer */
  --sara-bg-surface:    #111820;   /* cards, panels */
  --sara-bg-elevated:   #1A2230;   /* modals, popovers, hover states */
  --sara-bg-subtle:     #222D3D;   /* active rows, selected items */

  /* Text */
  --sara-text-primary:  #E8ECF1;   /* primary content — not pure white */
  --sara-text-secondary:#8899AA;   /* labels, metadata, secondary info */
  --sara-text-muted:    #556677;   /* placeholders, disabled text */

  /* Borders */
  --sara-border:        #1E2A3A;   /* subtle card/panel borders */
  --sara-border-focus:  #3B82F6;   /* focus rings, active states */

  /* Accent — Sara's signature (clinical blue + sage green) */
  --sara-accent:        #6A9BCC;   /* clinical blue — agent actions, branding, primary interactive */
  --sara-accent-hover:  #7DAAD6;   /* lighter blue — hover/active states */
  --sara-accent-soft:   #6A9BCC15; /* blue at 8% — subtle backgrounds */
  --sara-accent-glow:   #6A9BCC40; /* for agent-active pulse animations */
  --sara-secondary:     #788C5D;   /* sage green — secondary accent, positive agent outcomes */
  --sara-secondary-soft:#788C5D20; /* sage green at 12% — subtle backgrounds */

  /* Semantic — Clinical Status */
  --sara-critical:      #EF4444;   /* critical alerts, STAT orders */
  --sara-critical-soft: #EF444420; /* critical background tint */
  --sara-warning:       #F59E0B;   /* warnings, abnormal-high values */
  --sara-warning-soft:  #F59E0B20;
  --sara-success:       #10B981;   /* normal values, completed actions */
  --sara-success-soft:  #10B98120;
  --sara-info:          #3B82F6;   /* informational, links, navigation */
  --sara-info-soft:     #3B82F620;
}
```

### Light Mode (Secondary)

For daytime use, patient-facing screens, and printed summaries.

```css
:root.light {
  --sara-bg-base:       #F8FAFB;
  --sara-bg-surface:    #FFFFFF;
  --sara-bg-elevated:   #FFFFFF;
  --sara-bg-subtle:     #F1F4F8;

  --sara-text-primary:  #111827;
  --sara-text-secondary:#6B7280;
  --sara-text-muted:    #9CA3AF;

  --sara-border:        #E5E7EB;
  --sara-border-focus:  #3B82F6;
}
```

### Severity Scale

Use these consistently for clinical values, alerts, and status indicators:

| Level | Color | Use Case |
|-------|-------|----------|
| **Critical** | `#EF4444` red | Life-threatening, STAT, critical lab values |
| **Abnormal-High** | `#F59E0B` amber | Out of range (high), needs attention |
| **Normal** | `#10B981` green | Within range, completed, resolved |
| **Informational** | `#3B82F6` blue | Neutral status, pending, in-progress |
| **Muted** | `#8899AA` gray | Inactive, historical, low priority |

**Rule:** Never use red for anything other than genuinely critical states. A dashboard where everything is red is a dashboard where nothing is red.

---

## 4. Core Design Principles

### 4.1 Restraint

Show less, not more. Whitespace is a feature.

- Default to hiding secondary information behind expandable sections, tooltips, or drill-down views.
- Cards should contain 3–5 pieces of information maximum at the top level.
- Avoid decorative borders, shadows, gradients, or ornamentation. Let content and spacing do the work.
- If you're adding a visual element "for balance" — remove it instead.

### 4.2 Progressive Disclosure

Never dump raw data. Always layer information:

```
Level 1 — Glanceable:    Status pill + patient name + chief concern
Level 2 — Scannable:     Key vitals + active meds + recent labs (card view)
Level 3 — Detailed:      Full history, raw FHIR resources, audit trail
```

- Default views show Level 1–2. Level 3 is always one click away but never forced.
- For FHIR data: render human-readable summaries. Raw JSON is available via an expandable "Source" panel, not as the default view.
- For AI reasoning: show the conclusion first, then "Show reasoning" expands Sara's chain of thought.

### 4.3 Status at a Glance

A clinician should be able to scan a patient summary in under 3 seconds and know what needs attention.

- Use **color-coded severity pills/badges** on lab values, vitals, and alerts.
- Use **iconography consistently** — the same icon always means the same resource type.
- Arrange information in **priority order**: critical items first, routine items last.
- Use **bold weight** (DM Sans 600/700) to draw the eye to values; use regular weight (400) for labels.

### 4.4 Keyboard-First

Power users (physicians, nurses) will learn shortcuts. Support them.

- Implement a **command palette** (Cmd+K / Ctrl+K) for global search, patient lookup, and quick actions.
- Navigation cards, lists, and action buttons must be keyboard-navigable with visible focus rings.
- Arrow keys should navigate lists and tables. Enter should confirm. Escape should dismiss.

### 4.5 Micro-Interactions

Subtle motion builds trust and communicates state changes.

- **Hover states:** Slight background tint (`--sara-bg-elevated`) on cards and list items. No dramatic transforms.
- **Loading:** Use skeleton loaders that match the shape of incoming content — never a generic spinner for structured data.
- **Transitions:** 150–200ms ease-out for panel opens, fades, and state changes. No bouncing or spring physics in clinical contexts — motion should feel calm, not playful.
- **Action feedback:** Completed actions (e.g., "Lab ordered") get a brief green checkmark animation, then settle into a static ✓ state.

### 4.6 Agent-at-Work Animations

When Sara is actively working — retrieving FHIR data, running calculations, reasoning — the UI must communicate progress without creating anxiety. The goal: the physician should feel like a capable colleague is working on it, not that the system is frozen.

#### The Agent Pulse

Sara's signature animation is a **warm breathing glow** using `--sara-accent-glow`. This appears on Sara's icon or avatar whenever the agent is actively processing.

```css
@keyframes sara-pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--sara-accent-glow); }
  50%      { box-shadow: 0 0 16px 4px var(--sara-accent-glow); }
}

.sara-working {
  animation: sara-pulse 2s ease-in-out infinite;
}
```

This is a slow, calm pulse (2s cycle) — not a frantic blink. It should feel like breathing.

#### Phase Progress Indicator

For multi-step workflows (data gathering → calculations → reasoning → execution), show a **horizontal step indicator** that fills as Sara progresses through phases:

```
[ ● Gathering data ─── ○ Calculating ─── ○ Reasoning ─── ○ Executing ]
       ━━━━━━━━━━━━▶
```

- Active phase: `--sara-accent` filled dot with label
- Completed phases: `--sara-success` green dot
- Pending phases: `--sara-text-muted` hollow dot
- Progress bar segment animates with a subtle shimmer (not a stripe — too aggressive)

```css
@keyframes sara-shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.sara-progress-active {
  background: linear-gradient(
    90deg,
    var(--sara-accent) 0%,
    var(--sara-accent-hover) 50%,
    var(--sara-accent) 100%
  );
  background-size: 200% 100%;
  animation: sara-shimmer 2.5s ease-in-out infinite;
}
```

#### Streaming Content

When Sara is generating text (summaries, recommendations), stream it in with a **typewriter-style reveal**:

- Text appears word-by-word or line-by-line (not character-by-character — too slow for clinical use)
- A soft blinking cursor (`--sara-accent`, 1s blink cycle) marks the writing position
- Once complete, the cursor fades out over 300ms

```css
@keyframes sara-cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.sara-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: var(--sara-accent);
  animation: sara-cursor-blink 1s step-end infinite;
  margin-left: 2px;
  vertical-align: text-bottom;
}
```

#### Tool Call Visualization

When Sara calls a FHIR API or runs a calculation, briefly show what's happening in a **compact activity log** that auto-scrolls:

```
┌─────────────────────────────────────────────────────┐
│  ✦ Sara is working...                    [2.3s]     │
│                                                      │
│  ● Fetched patient demographics           ✓  0.4s   │
│  ● Retrieved HbA1c results                ✓  0.6s   │
│  ● Retrieved creatinine results            ✓  0.3s   │
│  ● Calculating GFR (CKD-EPI)...          ◐  ...     │
│                                                      │
└─────────────────────────────────────────────────────┘
```

- Each line fades in (200ms) as the tool call begins
- Running calls show a spinning indicator `◐` (quarter-circle rotation, 800ms cycle)
- Completed calls show `✓` in `--sara-success` with duration
- Failed calls show `✗` in `--sara-critical`
- The entire log is collapsible — physician can minimize it to just the pulse icon
- Total elapsed time ticks in the header

```css
@keyframes sara-tool-spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.sara-tool-active {
  display: inline-block;
  animation: sara-tool-spin 0.8s linear infinite;
  color: var(--sara-accent);
}
```

#### Animation Rules

| Rule | Why |
|------|-----|
| **All animations must be pausable** | `prefers-reduced-motion: reduce` must disable all motion |
| **No animation on clinical data** | Numbers, values, and results must never animate in (no counting up, no bounce) |
| **Progress, not performance** | Animations communicate state, not decoration. If it doesn't tell the user something, remove it |
| **Slow and calm** | Minimum cycle time: 1.5s. Nothing should pulse faster than a resting heart rate |
| **Accent color only** | Agent animations use `--sara-accent` and `--sara-accent-glow`. Never animate with semantic colors (red, amber) |

```css
@media (prefers-reduced-motion: reduce) {
  .sara-working,
  .sara-progress-active,
  .sara-cursor,
  .sara-tool-active {
    animation: none;
  }
}
```

### 4.7 Accessibility (Non-Negotiable)

- **Contrast:** All text must pass WCAG AA (4.5:1 body text, 3:1 large text). Test with the color tokens defined above.
- **Touch targets:** Minimum 44×44px for all interactive elements.
- **Screen readers:** All icons must have `aria-label`. Status colors must have text equivalents (never color alone).
- **Focus management:** Visible focus rings (`--sara-border-focus`). Logical tab order. Trap focus in modals.
- **Font sizing:** Respect user preferences. Use `rem` units, never `px` for font sizes in production. (The type scale above uses `px` for reference only.)

---

## 5. Component Patterns

### 5.1 Navigation Cards (Quickstart Grid)

Use for landing pages, workflow selection, and feature discovery.

```
┌──────────────────────────────────┐
│  [icon]                          │
│  Title (DM Sans 600, 16px)      │
│  Description (DM Sans 400, 13px,│
│  --sara-text-secondary)          │
└──────────────────────────────────┘
```

- Background: `--sara-bg-surface`
- Border: 1px solid `--sara-border`
- Border-radius: 12px
- Padding: 24px
- Hover: background shifts to `--sara-bg-elevated`, border brightens slightly
- Grid: `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))` with 16px gap
- Icons: Use `--sara-accent` clinical blue, 24×24px, monoline style (Lucide icon set recommended). Use `--sara-secondary` sage green for success/health-related icons.

### 5.2 Patient Summary Card

The most critical component. Follows the progressive disclosure pattern.

```
┌─────────────────────────────────────────────────────────┐
│  Patient Name (Playfair 600, 20px)       [Status pill]  │
│  MRN: 123456 · 68M · DOB: 1957-03-15                   │
│                                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│  │HbA1c │ │ GFR  │ │ BMI  │ │ BP   │   ← Key metrics   │
│  │ 7.8% │ │ 52.3 │ │ 26.8 │ │128/82│      as tiles     │
│  │  ⚠️  │ │  🔴  │ │  ⚡  │ │  ✓   │                   │
│  └──────┘ └──────┘ └──────┘ └──────┘                   │
│                                                          │
│  Active: Metformin 1000mg BID, Lisinopril 20mg,         │
│          Atorvastatin 40mg                               │
│                                                  [More ▸]│
└─────────────────────────────────────────────────────────┘
```

- Metric tiles use semantic colors for status
- "More ▸" expands to Level 3 detail
- The card headline (patient name) is the one place Playfair Display appears in dense UI

### 5.3 Sara Action Summary

When Sara completes a workflow, present results in this format:

```
┌──────────────────────────────────────────────────────────┐
│  ✦ Sara: Diabetes Follow-Up              [Show reasoning]│
│  Patient S6200102 · 68M · 2 min ago                      │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  KEY FINDINGS                                            │
│  HbA1c 7.8% — above target (<7%)            [⚠ Warning] │
│  GFR 52 mL/min — Stage 3a CKD               [🔴 Alert]  │
│  ASCVD Risk 18.2% — High                    [⚠ Warning] │
│                                                           │
│  ACTIONS TAKEN                                           │
│  ✓ Lipid panel ordered (overdue 8 months)                │
│  ✓ Urine ACR ordered (nephropathy screening)             │
│  ✓ Ophthalmology referral created                        │
│                                                           │
│  RECOMMENDATIONS                                         │
│  → Consider GLP-1 agonist (semaglutide/tirzepatide)     │
│  → Metformin safe to continue at current GFR             │
│  → Schedule 3-month follow-up with repeat HbA1c          │
│                                                           │
│           [ ✓ Sign ]   [ ✎ Modify ]   [ ✕ Reject ]      │
└──────────────────────────────────────────────────────────┘
```

- `✦` icon uses `--sara-accent` clinical blue — Sara's signature
- "Show reasoning" expands the full chain-of-thought + FHIR calls made
- Action buttons: Sign = `--sara-success`, Modify = `--sara-info`, Reject = `--sara-critical`
- Each finding links to its source data (lab result, calculation, reference)

### 5.4 FHIR Resource Display

When showing FHIR data to clinicians, **never** render raw JSON by default.

**Default view:** Human-readable summary using progressive disclosure.
**Developer/audit view:** Collapsible JSON panel with syntax highlighting.

For interactive FHIR display, use the **fhir-react** library:

```jsx
import { FhirResource, fhirVersions } from 'fhir-react';

<FhirResource
  fhirResource={patientJson}
  fhirVersion={fhirVersions.R4}
/>
```

For raw JSON inspection, use **JSON Hero** (jsonhero.io) patterns — auto-detect URLs, dates, coded values, and render them with meaningful previews rather than plain text.

For graph visualization of complex FHIR bundles (relationships between resources), use **JSON Crack** (jsoncrack.com) style interactive node graphs.

---

## 6. Available Tools & Libraries

The agent has access to powerful tools for building interactive, beautiful interfaces. Use them.

### UI Frameworks & Rendering

| Tool | Use For |
|------|---------|
| **Open WebUI** (openwebui.com) | Chat-based artifact display, markdown/LaTeX rendering, live code preview, SVG rendering. Use as the agent harness for displaying artifacts and interactive UI. |
| **fhir-react** (npm: `fhir-react`) | Rendering FHIR R4/STU3/DSTU2 resources as human-readable, accordion-style UI. Use `<FhirResource>` component for any FHIR data display. |
| **Artifacts** | The agent can create and display HTML, React (.jsx), Markdown, SVG, Mermaid diagrams, and PDF files as interactive artifacts. Always follow this design system when generating artifacts. |

### Data Visualization & Inspection

| Tool | Use For |
|------|---------|
| **JSON Hero** (jsonhero.io) | Human-friendly JSON viewing. Auto-detects URLs, dates, colors, and coded values. Use its patterns for FHIR resource inspection panels. |
| **JSON Crack** (jsoncrack.com) | Graph visualization of JSON/YAML/XML structures. Use for visualizing relationships in FHIR Bundles — patient → conditions → medications → labs as an interactive node graph. |
| **Recharts / D3.js** | Clinical data charts — vital sign trends, lab value timelines, risk score distributions. Keep them clean: no 3D, no excessive gridlines, use the Sara color tokens. |

### Component Libraries

| Library | Use For |
|---------|---------|
| **shadcn/ui** | Base component primitives (Alert, Dialog, Card, Badge, Tabs). Customize with Sara's color tokens and typography. |
| **Lucide React** | Icon system. Monoline, 24×24, consistent with Sara's visual language. Use `--sara-accent` for interactive icons, `--sara-text-secondary` for decorative ones. |
| **Tailwind CSS** | Utility-first styling. Map Sara's design tokens to Tailwind's config. Use core utility classes only in artifact contexts. |

### Integration Pattern

When building UI, the agent should:

1. **Choose the right artifact type** — React (.jsx) for interactive components, HTML for static layouts, Markdown for text-heavy summaries, Mermaid for clinical flow diagrams.
2. **Embed Sara's fonts** in every HTML/React artifact using the `<link>` tags from Section 2.
3. **Apply Sara's color tokens** as CSS custom properties.
4. **Use fhir-react** for any FHIR resource rendering rather than building custom display logic.
5. **Use JSON Hero patterns** for any raw data inspection views.
6. **Follow progressive disclosure** — summary first, detail on demand.

---

## 7. Layout Principles

### Spacing Scale

Use a consistent 4px base unit:

| Token | Value | Use |
|-------|-------|-----|
| `space-1` | 4px | Tight: icon-to-label gap |
| `space-2` | 8px | Compact: between related items |
| `space-3` | 12px | Default: padding inside small components |
| `space-4` | 16px | Standard: card padding, list gaps |
| `space-6` | 24px | Comfortable: section spacing |
| `space-8` | 32px | Generous: between major sections |
| `space-12` | 48px | Expansive: page-level section breaks |

### Border Radius

| Token | Value | Use |
|-------|-------|-----|
| `radius-sm` | 6px | Buttons, pills, badges |
| `radius-md` | 8px | Input fields, small cards |
| `radius-lg` | 12px | Cards, panels, modals |
| `radius-xl` | 16px | Large containers, hero sections |

### Grid System

- Use CSS Grid for page layouts and card grids.
- Use Flexbox for inline layouts and component internals.
- Max content width: `1280px`, centered.
- Standard card grid: `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`.
- Sidebar + main layout: `grid-template-columns: 280px 1fr` (sidebar collapses on mobile).

---

## 8. Do's and Don'ts

### DO

- ✓ Use whitespace generously — it reduces cognitive load
- ✓ Show data provenance (source, timestamp, who recorded it)
- ✓ Use skeleton loaders shaped like the incoming content
- ✓ Color-code clinical severity consistently across all views
- ✓ Make Sara's actions auditable — every AI decision should have a "why" link
- ✓ Test on dark backgrounds first (the primary mode)
- ✓ Use `--sara-accent` clinical blue sparingly — it marks Sara's AI contributions. Use `--sara-secondary` sage green for completed/positive outcomes.

### DON'T

- ✗ Don't use pure black (`#000`) or pure white (`#FFF`) — they cause eye strain
- ✗ Don't render raw FHIR JSON as the default view for clinicians
- ✗ Don't use red for non-critical states (warnings are amber, not red)
- ✗ Don't animate clinical data — numbers should never bounce or count up
- ✗ Don't use more than 2 font families in any single view
- ✗ Don't rely on color alone to communicate status — always pair with text or icons
- ✗ Don't add decorative illustrations to clinical workflows — keep it functional
- ✗ Don't use generic loading spinners for structured data — use skeleton shapes

---

## 9. Reference Implementations

Study these for inspiration. Do not copy — synthesize their best qualities into Sara's own voice.

| Product | What to Study |
|---------|---------------|
| **Linear** (linear.app) | Speed, keyboard-first, command palette, dark mode depth |
| **Stripe Dashboard** | Typography hierarchy, data density, color system |
| **Vercel** | Dark mode contrast layers, real-time status, information density |
| **Medplum** (medplum.com) | FHIR-native components, clinical workflow patterns, Storybook |
| **Abridge** (abridge.com) | AI-generated clinical content with source linking ("Linked Evidence") |
| **Headspace** | Calming color palette, anxiety-reducing UI, patient-facing design |
| **Koru UX** (koruux.com/50-examples-of-healthcare-UI) | 50 healthcare UI patterns: patient lookup, scheduling, dashboards, care plans |

---

*Sara's interface should feel like a calm, competent colleague — always prepared, never overwhelming, and transparent about every decision it makes.*
