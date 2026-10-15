# DIA Frontend Master Architecture & Design Plan (`frontend_plan.md`)

## 1. Vision & Objectives

The goal is to build a modern, high-craft, and production-grade Web Frontend for the **Dataset Integrity Analyzer (DIA 2.0)**. 

Currently, DIA has an enterprise-grade FastAPI REST API with full persistence, confident learning, cross-dimensional confound analysis (C1), bias impact prediction (C2), and prioritized remediation manifests. The frontend will transform these analytical capabilities into a clean, intuitive, and responsive **Dataset Health & Diagnostic Studio**.

### Core Audiences & Personas
1. **ML & Data Engineers**: Require high-density telemetry, confusion matrices, out-of-fold noise flags, embedding outlier visualizers, effect sizes (Kruskal $\epsilon^2$), and machine-actionable export manifests.
2. **AI Auditors & Product Leaders**: Require clear executive summaries, overall AI Readiness scores, compliance/governance badges, ELI5 ("Explain Like I'm 5") plain-language toggles, and Gebru et al. Datasheets.

---

## 2. Incorporation of Matt Pocock’s Engineering Skills

Following [mattpocock/skills](https://github.com/mattpocock/skills), we incorporate the key engineering disciplines:

| Skill | Practice & Protocol | Application in DIA Frontend |
| :--- | :--- | :--- |
| **`grilling` / `grill-with-docs`** | Relentlessly interview the user along the design tree frontier before writing code; record decisions into living architectural documentation. | Aligning UX layout, tech stack, data fetching, and visualization choices. |
| **`strict-typescript`** | Strict typing: zero `any`, zero unsafe type assertions (`as unknown as T`), explicit discriminated unions for state. | All API response models and UI component states modeled with discriminated unions. |
| **`runtime-validation`** | Validate external data boundaries with Zod; infer TypeScript types from schemas. | Colocated Zod schemas for all FastAPI endpoints (`/v1/runs/{id}/report`, `/v1/datasets`, etc.). |
| **`component-architecture`** | Compound components, slot pattern, accessible unstyled primitives (Radix UI / Headless UI), styling via CVA. | Composable cards, tabs, modals, accordions, and metric widgets with strict slot separation. |
| **`tailwind-craft`** | Token-driven utility design, semantic color variables, dark-mode first-class, standardized responsive rhythm (`sm:`, `md:`, `lg:`), rich micro-interactions (`hover:`, `focus-visible:`, `active:`). | Clean, modern theme (slate/zinc neutral foundation, emerald/amber/rose semantic status colors). |
| **`state-resilience`** | Mandatory coverage of the 5 Core UI States: Ideal, Loading skeleton (`animate-pulse`), Empty with CTA, Actionable Error with retry, Partial/Edge. | No blank screens, no raw unhandled errors, no layout shifts (CLS). |
| **`prototype` & `to-tickets`** | Incremental tracer-bullet execution, building functional vertical slices that can be validated at each milestone. | Step-by-step deliverable milestones from project setup to production build. |

---

## 3. Technology Stack Options

### Option 1 (Recommended): Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query + Lucide Icons + Recharts
- **Pros**: 
  - Standard enterprise stack for AI data platforms.
  - SSR / SSG capability and robust client routing.
  - Native TypeScript 5.5+ support.
  - shadcn/ui provides copy-pasteable, customizable Radix UI primitives adhering to Pocock's `component-architecture`.
  - Built-in API proxying / rewrite support to eliminate CORS issues with FastAPI on `http://127.0.0.1:8000`.
- **Cons**: Slightly heavier node dependencies compared to pure client-side Vite.

### Option 2: Vite + React 19 + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query
- **Pros**: Ultra-fast hot module reloading, lightweight, can be compiled to pure static files served directly by FastAPI via `StaticFiles`.
- **Cons**: Client-only routing requires configuring client SPA fallback.

### Option 3: Modern Alpine.js / Tailwind + Jinja2 Templates (Monolithic FastAPI)
- **Pros**: Zero node runtime in production; bundled directly with Python.
- **Cons**: Limited component composability, harder to build rich interactive charts, what-if sliders, and virtualized sample data tables.

**Recommendation**: **Option 1 (Next.js 15 App Router)** in a `frontend/` directory, with an easy build script to generate static exports if ever needed, or proxy directly to the FastAPI backend during development.

---

## 4. Design System & Theming Tokens

### Color Palette (Tailwind CSS Tokens)
- **Neutral Base**: Slate / Zinc palette (`bg-slate-50 dark:bg-slate-950`, `text-slate-900 dark:text-slate-100`, `border-slate-200 dark:border-slate-800`).
- **Brand / Accent**: Indigo / Violet (`indigo-600` / `indigo-500` for primary actions and active tabs).
- **Readiness Semantics**:
  - `Production Ready`: Emerald (`emerald-500` / `emerald-600`)
  - `Acceptable`: Blue / Cyan (`sky-500` / `sky-600`)
  - `Needs Remediation`: Amber / Orange (`amber-500` / `amber-600`)
  - `Critical / Not Ready`: Rose / Red (`rose-500` / `rose-600`)
  - `Insufficient Coverage`: Slate / Gray (`slate-400`)

### Mode Switcher
- **Dual Audience Switch**: A prominent toggle on top: **"Stakeholder (ELI5)"** vs **"Engineer (Detailed)"**.
  - In *Stakeholder Mode*: complex statistical metrics (entropy, Gini, Kruskal $\epsilon^2$, FDR $q$-value) are annotated with conversational explanations and intuitive indicators.
  - In *Engineer Mode*: full equations, distributions, sample references, and exact p-values are shown.
- **Theme**: Dark / Light mode toggle.

---

## 5. Architectural Feature Modules

```
                    ┌──────────────────────────────────────────────┐
                    │            DIA Navigation & Header           │
                    │  [Datasets] [Audits] [What-If] [Settings]    │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                                                   ▼
┌───────────────────────────────┐                   ┌───────────────────────────────────────────────┐
│     Dataset Management        │                   │             Audit Run Workspace               │
│ • Drag-&-drop ZIP Uploader    │                   │ • Real-time audit progress bar & status       │
│ • Layout & split inspector    │                   │ • Executive readiness gauge (0-100)           │
│ • Config builder (Fairness,   │                   │ • 6-Dimension Health Cards (C1 Normalised)    │
│   Metadata schema, Sampling)  │                   │ • Cross-Dimensional Confounds Matrix          │
└───────────────────────────────┘                   │ • Bias Impact Downstream Simulator (C2)       │
                                                    │ • What-If Scenario Rescoring Studio           │
                                                    │ • Prioritized Remediation "Do This First"     │
                                                    │ • Flagged Sample Visual Gallery & Manifests   │
                                                    │ • Multi-format Export (HTML, CSV, Datasheet)  │
                                                    └───────────────────────────────────────────────┘
```

### Module 1: Ingestion & Upload Experience (`/datasets`)
- **Drag-and-Drop Zone**: Accepts ZIP archives up to configured limit (200MB default).
- **Pre-upload Validation**: Clear client-side size check and file extension filter.
- **Audit Launch Drawer**:
  - Configure target group proportions (e.g. demographic balance targets).
  - Define custom metadata validation schemas.
  - Toggle synthetic bias impact prediction (C2) and attribute estimation.
  - Sampling rate slider (0.1 to 1.0) with seed input.

### Module 2: Live Audit Progress & Lifecycle (`/runs/[runId]`)
- Polling via TanStack Query every 1.5s while status is `queued` or `running`.
- Stepper indicator reflecting backend pipeline phases:
  1. Unpacking & validation
  2. Embeddings extraction (ResNet-18)
  3. Core metric computation (Imbalance, Duplicates, Quality)
  4. Confident Learning & Label Noise estimation
  5. Cross-dimensional confounds (C1)
  6. Bias impact prediction (C2) & Readiness synthesis
- **Cancel Button** to gracefully abort running audits.

### Module 3: Executive Readiness Command Center
- **Hero KPI Gauge**: Large animated SVG gauge showing overall AI Readiness Score (0-100), verdict chip, and score coverage percentage.
- **Hard Gate Alert Banners**: If a hard gate tripped (e.g. cross-split duplicate leakage or critical label noise), an alert displays the exact blocking reason.
- **Unified 6-Dimension Health Grid**:
  - Balance, Fairness, Quality, Uniqueness, Diversity, Label Integrity.
  - Normalized 0-100 health bars, assigned weight, raw primary metric, and status badge.

### Module 4: Cross-Dimensional Confounds Matrix (Novel C1)
- Interactive visual matrix of the 6 cross-dimensional interactions:
  - Quality $\times$ Class
  - Quality $\times$ Demographic Attribute
  - Redundancy $\times$ Class
  - Diversity $\times$ Class
  - Label Noise $\times$ Class
  - Leakage $\times$ Split
- Shows statistically significant confounds (with FDR correction $q < 0.05$) and lists verified absent confounds.

### Module 5: What-If Scenario Rescoring Studio & Bias Impact (C2)
- Interactive sliders bound to `/v1/runs/{id}/what-if`:
  - Sliders for Imbalance Ratio, Defect Rate %, Redundancy Ratio, Cluster Entropy, Label Noise %.
  - Live recalculation of the Readiness Score without touching the database or running heavy model passes.
  - Side-by-side Delta card: "Score changes from 64 $\to$ 82 (+18 pts)".
  - Predicted test accuracy impact curve.

### Module 6: Prioritized Remediation Action Center & Manifest Explorer
- **Top 3 "Do These First" Cards**: Ranked by projected score gain / estimated effort.
- **Manifest Table**: Searchable, filterable table of specific sample-level actions (`RELABEL_SAMPLE`, `REMOVE_DUPLICATE`, `INSPECT_DEFECT`).
- **Export Toolbar**:
  - Download Remediation CSV / JSON
  - Download Gebru et al. Datasheet (Markdown / JSON)
  - Download Standalone Zero-Dependency HTML Report

---

## 7. Implementation Milestones

- **Milestone 1**: Project Initialization & Pocock Discipline Setup (`frontend/` workspace, Next.js/Tailwind/shadcn, Zod API client, strict TypeScript configuration).
- **Milestone 2**: Ingestion & Dataset Management UI (Dataset list, upload modal, configuration drawer).
- **Milestone 3**: Audit Monitoring & Real-time Job Stepper (Queued, Running with animated progress, Error handling).
- **Milestone 4**: Readiness Score & 6-Dimension Health Dashboard (Hero gauge, dimension cards, ELI5 toggle).
- **Milestone 5**: Advanced Analytics (C1 Confound Matrix, C2 Impact Simulator, What-If live rescoring).
- **Milestone 6**: Remediation Manifest, Flagged Sample Explorer & Export Hub (Action cards, filterable table, download triggers).
- **Milestone 7**: End-to-End Integration, Resilience & Visual Polish (Dark mode, keyboard navigation, empty/loading skeletons, Cypress/Playwright or vitest testing).
