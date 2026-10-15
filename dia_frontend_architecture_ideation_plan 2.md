# DIA 2.0 Frontend Master Plan & Antigravity Prompt (`frontend_plan.md`)

---

## 🚀 COPY-PASTE MASTER PROMPT FOR ANTIGRAVITY

> **Copy everything inside the code block below and paste it directly to Antigravity:**

```text
You are building the production Web Frontend for the Dataset Integrity Analyzer (DIA 2.0) on the `dia_2.0_antigravity` branch.

Read `plan.md` and `frontend_plan.md` first. Follow every locked decision below and execute the build systematically using the engineering principles from https://github.com/mattpocock/skills (`grill-with-docs`, `strict-typescript`, `runtime-validation`, `component-architecture`, `tailwind-craft`, `state-resilience`, `to-tickets`, and `verification-loop`).

---

### 1. CRITICAL RULE: BACKEND-FIRST AUTONOMOUS DISCOVERY
Before writing any frontend code, inspect the existing backend codebase (`src/`, `app/`, `api/`, FastAPI routers, Pydantic schemas, SQLAlchemy models, and static/artifact routes):
- **Choose and configure the frontend framework, build tool, routing, API client, and proxy/static-mount setup strictly based on the already-developed FastAPI backend** so it integrates with zero friction (matching exact route prefixes, shared-password auth headers, CORS settings, and JSON payload field names).
- If the backend needs a small helper endpoint for the UI (such as serving raw/thumbnail sample images by sample ID for the visual photo inspector), add it cleanly to the FastAPI backend without breaking any of the 36 existing tests.
- Never guess API JSON shapes: inspect the backend Pydantic models/responses first and mirror them into runtime validation schemas (Zod).

---

### 2. CORE DESIGN PHILOSOPHY: "CALM CLARITY, WARM PAPER & ZERO INFO OVERLOAD"
The previous dashboard concept was too dark, dense, and crowded. Redesign and build the UI around **Calm Clarity & Progressive Disclosure**:
1. **Warm, Crisp, Lighter Background Palette (Warm Editorial / Tactile Studio)**:
   - **Primary Canvas Background**: Warm Alabaster / Soft Paper (`#FAF8F5` or Tailwind `stone-50` / `orange-50/20`), NEVER harsh pure `#FFFFFF` and NEVER heavy dark mode by default.
   - **Elevated Surface / Card Background**: Crisp Warm White (`#FFFFFF`) with delicate warm borders (`#E7E5E0` / `stone-200/80`) and ultra-soft ambient warm shadows (`0 8px 24px -4px rgba(28, 25, 23, 0.05)`).
   - **Secondary Recessed Wells**: Soft Warm Sand (`#F3F0EA` / `stone-100`) for sliders, code/metric pills, and filter bars.
   - **Typography**: Deep Warm Charcoal (`#1C1917` / `stone-900`) for crisp headings; Muted Warm Slate (`#57534E` / `stone-600`) for body text; clean tabular numerals (`tabular-nums`) for scores.
   - **Status Colors (Soft & Harmonious, Not Neon)**:
     - **Healthy / Ready**: Sage Emerald (`emerald-700` text, `emerald-50` pill background, `emerald-500` accent)
     - **Good / Acceptable**: Warm Teal / Sky (`sky-700` text, `sky-50` pill background)
     - **Needs Attention**: Warm Amber / Ochre (`amber-800` text, `amber-50` pill background, `amber-500` accent)
     - **Critical Issue**: Terracotta Rose (`rose-700` text, `rose-50` pill background, `rose-500` accent)
2. **Strict Anti-Clutter & Progressive Disclosure Rules**:
   - **Maximum 3 Cards Per Row** on desktop (`gap-6` minimum, `p-6` to `p-8` internal card padding). Let at least 30% of the viewport be calm open background space.
   - **Maximum 3 Data Points Per Card**: Each card on the main screen may only show: (1) Title + Status Pill, (2) One Large Number/Score, and (3) One Plain-English Sentence.
   - **Plain-English First ("ELI5 Default")**: Never dump raw statistical jargon (`Kruskal-Wallis epsilon^2`, `Benjamini-Hochberg q-value`, `Isolation Forest score`, `Gini`) on the main surface. Show plain English by default, and tuck exact formulas/p-values inside a clean **"View Technical Details"** drawer or subtle toggle (`Simple View | Technical View`).
   - **No Simultaneous Competing Panels**: Never show tables, matrices, and sliders all at the same time. Keep each tab focused on a single clear job.

---

### 3. SIMPLIFIED LAYOUT & STREAMLINED NAVIGATION
Use a clean, collapsible **Left Sidebar (240px)** + **Spacious Main Canvas (max-w-6xl centered)** with **4 Focused Views** (reduced from 5+ crowded tabs):

#### Left Sidebar (Clean & Minimal)
- **Brand Header**: `DIA 2.0` with a subtle warm badge.
- **Primary Action Button**: `+ Upload Dataset ZIP` (opens a clean step-by-step modal).
- **Dataset & Audit Switcher**: Clean list of uploaded datasets and their audit runs with a tiny color dot indicating health.
- **Compare Runs Toggle**: Simple button to compare two runs (`Before vs. After`) when a dataset has multiple runs.
- **Footer**: Read-Only / Password Unlock status indicator (`Unlock Studio`).

#### View 1: `Overview & Action Plan` (The Calm Command Center)
- **Top Alert Banner (Only shown if a critical blocker exists)**: A single, warm terracotta banner in plain English (e.g., *"14 identical photos appear in both your training and test folders. Remove them first so your test accuracy is honest."*).
- **Hero Row (2 Spacious Cards Side-by-Side)**:
  1. **3D Tactile Readiness Card (Left)**:
     - Displays the overall **Dataset Health Score (0–100)** inside a clean circular ring with subtle 3D perspective tilt on mouse hover, soft warm lighting reflection, and a clear verdict badge (`Ready to Train`, `Needs Minor Cleaning`, or `Fix Blockers First`).
     - Shows a single plain-English summary sentence and a small pill for how many dimensions were checked.
  2. **Top 3 "Do These First" Checklist (Right)**:
     - A calm, numbered 3-item action list ranked by highest impact.
     - Each item shows: **What to do in plain English** (e.g., *"Fix 38 likely mislabeled photos"*), **Why it matters**, and a green badge showing the **Projected Score Boost (`+6.5 pts`)**.
     - Includes a primary button: `Simulate Fixes` (jumps to What-If Simulator) and `Download Clean-Up List (CSV)`.
- **Bottom Row: The 6 Health Pillars (Clean 3x2 Grid)**:
  - 6 airy, tactile cards with subtle 3D hover lift:
    1. **Class Balance** (*Are all categories represented evenly?*)
    2. **Fairness & Groups** (*Are demographic groups balanced against your targets?*)
    3. **Photo Quality** (*Are images sharp, well-lit, and readable?*)
    4. **Duplicates & Leaks** (*Are there repeated or leaked test photos?*)
    5. **Visual Variety** (*Do photos cover diverse angles and scenes?*)
    6. **Label Accuracy** (*Are the folder/manifest labels trustworthy?*)
  - Each card shows ONLY: Pillar Name, 0–100 Score Bar, Status Badge, and 1 short sentence.
  - **Click any card** to open a clean **Slide-Over Detail Drawer** containing the deeper charts, class breakdowns, and cross-dimensional interaction findings (C1) relevant to that pillar—keeping the main page completely uncluttered!

#### View 2: `3D Dataset Map & Photo Inspector` (Visual Exploration)
Instead of overwhelming tables, let users *see* their dataset visually in two clean sections:
- **Section A: Interactive 3D Dataset Cluster Map (Top Card)**:
  - A smooth, tactile 3D scatter plot on a warm light canvas where each dot is an image from the dataset, colored by class or issue type.
  - Users can drag to rotate in 3D, scroll to zoom, and click a toggle: `Color by Class` vs. `Highlight Outliers & Duplicates`.
  - Clicking any floating 3D point previews that exact image and its label on the side.
- **Section B: Flagged Photo Gallery & Side-by-Side Comparator (Bottom)**:
  - Simple filter pills at the top: `All Flagged` | `Train/Test Leaks` | `Suspected Wrong Labels` | `Near-Duplicates` | `Blurry / Low Quality` | `Unusual Outliers`.
  - A clean visual photo grid (4 columns) with large thumbnails and a simple tag below each photo.
  - Clicking a duplicate or train/test leak opens a clean **Side-by-Side Comparison Modal** (`Photo A in Train` vs. `Photo B in Test` with similarity % and a one-click flag).

#### View 3: `What-If Simulator` (Interactive Impact Sandbox)
A calm, split-screen interactive calculator wired to `/v1/runs/{id}/what-if`:
- **Left Column (Simple Controls)**:
  - A prominent **"✨ Apply Recommended Fixes"** one-click button at the top.
  - 5 clean, generously spaced sliders in plain English:
    1. *Reduce Duplicate Photos*
    2. *Fix Mislabeled Photos*
    3. *Remove Blurry / Damaged Photos*
    4. *Balance Underrepresented Classes*
    5. *Improve Visual Variety*
- **Right Column (Live 3D Score & Accuracy Preview)**:
  - A large, tactile 3D score card showing **`Current Score (64)` ➔ `Projected Score (86)` (`+22 pts`)** with smooth animated numbers.
  - **Predicted Model Accuracy Impact (C2)**: A clean visual gauge showing how much real-world model test accuracy you stand to recover (e.g., *"Expected +5.2% higher test accuracy after cleaning"*), with a gentle confidence range note if applicable.

#### View 4: `Exports & Reports` (One-Click Handoff)
A clean, spacious page with 4 large download cards (plus the `Before vs. After` run comparison when selected):
1. **Actionable Fix List (`CSV` / `JSON`)**: Exact list of filenames to delete, relabel, or inspect.
2. **Standalone Executive Report (`HTML`)**: Self-contained visual report you can email or open offline.
3. **Dataset Model Card / Datasheet (`Markdown` / `JSON`)**: Standardized Gebru et al. documentation ready for GitHub or compliance.
4. **Full Audit Data (`JSON`)**: Complete lossless metrics for researchers.
*(Also include the clean **Before vs. After Run Comparison** view here or from the sidebar so users can compare `Run A` vs. `Run B` with simple green/red delta badges).*

---

### 4. TACTILE 3D EFFECTS (TASTEFUL, WARM & PURPOSEFUL)
Keep 3D effects smooth, physical, and supportive of clarity—never gimmicky or chaotic:
1. **Tactile Paper-Lift & 3D Perspective Tilt Cards**: The Hero Readiness Card, What-If Preview Card, and the 6 Pillar Cards gently tilt (`±4 deg` max with spring physics) toward the cursor with warm daylight specular highlights and soft multi-layered depth shadows.
2. **Interactive 3D Image Embedding Space**: In View 2, render the dataset's feature embeddings / outliers in a clean 3D rotatable space (Three.js / React Three Fiber or WebGL canvas) set against the warm stone background, allowing intuitive spatial discovery of isolated outliers and tight duplicate clusters.
3. **3D Physical Elevation on Hover**: In the slide-out Cross-Dimensional Interaction (C1) matrix, cells with confirmed interactions physically elevate on the Z-axis with a soft warm shadow when hovered.

---

### 5. SHARED PASSWORD & LIVE AUDIT PROGRESS UX
- **Frictionless Browse + Password Modal (`G1`)**: Anyone can explore existing datasets, rotate the 3D map, and play with the What-If sliders in read-only mode. Clicking `Upload Dataset ZIP`, `Run New Audit`, or `Delete Dataset` opens a clean, friendly **"Unlock Studio"** password prompt that saves the password header for the session.
- **Calm Live Audit Stepper**: When an audit is queued or running, show a centered, reassuring progress card with a smooth progress bar, plain-English step names (*1. Checking files ➔ 2. Scanning image quality & duplicates ➔ 3. Checking label accuracy ➔ 4. Building health score*), and a `Cancel` button.

---

### 6. ENGINEERING QUALITY GATES (MATT POCOCK SKILLS)
1. **`strict-typescript`**: Zero `any`, strict null checks, discriminated unions for async states (`queued | running | completed | failed | cancelled`).
2. **`runtime-validation`**: Validate all FastAPI responses with Zod schemas at the API client boundary.
3. **`state-resilience`**: Every view must gracefully handle all 5 states with warm, calm styling: (1) Ideal loaded state, (2) Soft warm pulse skeletons (`bg-stone-200/70 animate-pulse`), (3) Friendly empty state with clear button, (4) Clear error card with `Try Again` button, and (5) Partial data state (e.g., when optional demographic metadata wasn't uploaded, show `"Not Provided"` calmly instead of an error).
4. **`to-tickets` & `verification-loop`**: Build incrementally, verifying `tsc --noEmit`, `npm run build`, and `pytest` after each vertical slice.
```

---

## 1. What We Changed to Make It Simpler & Warmer

Here is a quick summary of how this updated plan eliminates clutter and improves the visual feel:

| Previous Plan (Too Crowded) | New Simplified Plan (Calm, Warm & Crisp) |
| :--- | :--- |
| Heavy dark slate background (`zinc-950`) that felt like a complex cockpit. | **Warm Alabaster & Soft Paper background (`#FAF8F5`)** with crisp white cards (`#FFFFFF`) and soft warm stone borders. |
| 5+ tabs plus separate matrix views competing for attention. | **Only 4 spacious, focused views** (`Overview`, `3D Map & Photos`, `What-If Simulator`, `Exports`). |
| Cards packed with multiple numbers, weights, formulas, and raw stats. | **Strict "3 Things Per Card" Rule**: Only the Title, 1 Score Bar, and 1 Plain-English sentence on the main card. |
| Complex cross-dimensional matrices (`C1`) and charts visible all at once. | **Slide-Out Detail Drawers**: Click any of the 6 Health Pillar cards to slide out its deeper charts and hidden interaction checks only when you want to see them. |
| Statistical jargon everywhere (`Kruskal-Wallis`, `FDR q-value`, `Gini`). | **Plain-English by Default**, with a subtle `"Show Technical Stats"` toggle tucked inside detail drawers for engineers. |

---

## 2. Clean, Uncluttered Visual Wireframe

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ DIA 2.0        Dataset: Industrial-Defects-v2 (Run #04)           [Simple View ▾]  [🔓 Unlocked] │
├───────────────────────┬──────────────────────────────────────────────────────────────────────────────┤
│                       │                                                                              │
│  [+ Upload Dataset]   │   [ 1. Overview ]   [ 2. 3D Map & Photos ]   [ 3. What-If ]   [ 4. Exports ] │
│                       │                                                                              │
│  DATASETS             │   ┌──────────────────────────────────────────────────────────────────────┐   │
│  ● Industrial-Defects │   │ ⚠️ Heads up: 14 photos appear in both Train and Test folders.        │   │
│    ├─ Run #04 (64)    │   └──────────────────────────────────────────────────────────────────────┘   │
│    └─ Run #03 (51)    │                                                                              │
│  ○ MedMNIST-Derma     │   ┌───────────────────────────────┐  ┌───────────────────────────────────┐   │
│  ○ FairFace-Subset    │   │  OVERALL READINESS (3D TILT)  │  │  TOP 3 FIXES TO DO FIRST          │   │
│                       │   │                               │  │                                   │   │
│  ───────────────────  │   │          ╭─────────╮          │  │  1. Remove 14 Train/Test Leaks    │   │
│  ⚖️ Compare Two Runs  │   │         │  64 / 100 │         │  │     Boosts score by +11.2 pts     │   │
│                       │   │          ╰─────────╯          │  │                                   │   │
│                       │   │      Needs Minor Cleaning     │  │  2. Fix 38 Mislabeled Photos      │   │
│                       │   │                               │  │     Boosts score by +6.5 pts      │   │
│                       │   │  "Fixing 3 main issues can    │  │                                   │   │
│                       │   │   recover ~6% test accuracy." │  │  3. Remove 112 Duplicate Photos   │   │
│                       │   │                               │  │     Boosts score by +4.1 pts      │   │
│                       │   │                               │  │                                   │   │
│                       │   │                               │  │  [Simulate Fixes ➔]  [Download]   │   │
│                       │   └───────────────────────────────┘  └───────────────────────────────────┘   │
│                       │                                                                              │
│                       │   6 HEALTH PILLARS (Click any card to slide out detailed charts)             │
│                       │   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐     │
│                       │   │ Class Balance   72 │  │ Fairness        68 │  │ Photo Quality   84 │     │
│                       │   │ ██████████░░░░     │  │ █████████░░░░░     │  │ ████████████░░     │     │
│                       │   │ 2 classes are small│  │ Slight group gap   │  │ Mostly sharp photos│     │
│                       │   └────────────────────┘  └────────────────────┘  └────────────────────┘     │
│                       │   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐     │
│                       │   │ Duplicates      49 │  │ Visual Variety  79 │  │ Label Accuracy  61 │     │
│                       │   │ ███████░░░░░░░     │  │ ███████████░░░     │  │ ████████░░░░░░     │     │
│                       │   │ 14 split leaks!    │  │ Good scene variety │  │ 38 suspect labels  │     │
│                       │   └────────────────────┘  └────────────────────┘  └────────────────────┘     │
└───────────────────────┴──────────────────────────────────────────────────────────────────────────────┘
```