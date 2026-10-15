# DIA 2.0 Frontend Master Plan & Antigravity Prompt (`frontend_plan.md`)

---

## 🚀 COPY-PASTE MASTER PROMPT FOR ANTIGRAVITY

> **Copy everything inside the code block below and paste it directly to Antigravity:**

```text
You are building the production Web Frontend for the Dataset Integrity Analyzer (DIA 2.0) on the `dia_2.0_antigravity` branch. 

Read `plan.md` and `frontend_plan.md` first. Follow every locked decision below and execute the build systematically using the engineering principles from https://github.com/mattpocock/skills (`grill-with-docs`, `strict-typescript`, `runtime-validation`, `component-architecture`, `tailwind-craft`, `state-resilience`, `to-tickets`, and `verification-loop`).

### 1. CRITICAL RULE: BACKEND-FIRST AUTONOMOUS DISCOVERY
Before writing any frontend code, inspect the existing backend codebase (`src/`, `app/`, `api/`, FastAPI routers, Pydantic schemas, and static/artifact routes):
- **Choose and configure the frontend framework, build tool, routing, API client, and proxy/static-mount setup strictly based on the already-developed FastAPI backend** so it integrates with zero friction (e.g., matching exact route prefixes, auth headers, CORS settings, and payload field names).
- If the backend needs a small helper endpoint for the UI (such as serving raw/thumbnail sample images by sample ID for the visual inspector), add it cleanly to the FastAPI backend without breaking existing tests.
- Never guess API JSON shapes: inspect the backend Pydantic models/responses first and mirror them into runtime validation schemas (Zod).

### 2. LOCKED UX & DESIGN CHOICES (All "Option 1" Selections + 3D Depth)
- **A1 (Layout — Workspace Sidebar + Multi-Tab Studio)**: Collapsible left sidebar for Datasets, Audit Run History, and Run Comparison (`Diff Two Audits`). Main workspace organized into 5 tabs:
  1. `Overview & Readiness` (Executive summary, overall score gauge, hard-gate blocker alerts, top 3 "Do These First" fixes)
  2. `6 Dimensions` (Balance, Fairness, Image Quality, Duplicates/Uniqueness, Visual Diversity, Label Integrity)
  3. `Confounds (C1)` (How issues interact across dimensions — e.g., whether one class has much blurrier images or higher label errors)
  4. `What-If & Impact (C2)` (Interactive sliders to simulate fixing the dataset and seeing the projected accuracy improvement)
  5. `Sample Triage & Exports` (Visual image grid of problem samples, side-by-side duplicate/leakage comparison, and 1-click downloads for CSV, JSON, Model Card Markdown, and Standalone HTML report)
- **B1 (Visual Style — Dark-First Precision Telemetry + Light Mode Toggle)**: Deep dark slate/zinc theme (`zinc-950`/`zinc-900`) with a toggle for Daylight Mode. Clear status colors: Emerald (Ready), Sky (Acceptable), Amber (Needs Fixes), Rose (Critical Blocker). Include a top-bar toggle for **"Simple Mode (ELI5 / Plain English)" vs. "Engineer Mode (Full Stats)"** so non-specialists can understand every metric effortlessly.
- **3D Spatial Effects & Tactile Depth**:
  1. **Interactive 3D Embedding & Outlier Explorer** (in Diversity / Sample Triage): A 3D scatter/cluster visualizer (using Three.js / React Three Fiber / Plotly 3D or lightweight WebGL canvas) where users can rotate, zoom, and hover over dataset image clusters and see Isolation Forest outliers floating in 3D space.
  2. **3D Perspective Tilt & Layered Glass Cards**: Subtle 3D mouse-tracking perspective tilt (`rotateX`/`rotateY` with spring physics), specular highlight borders, and multi-layered Z-depth shadows on the Hero Readiness Gauge and 6-Dimension cards.
  3. **3D Layered Bivariate Matrix Elevation**: In the C1 Confounds Matrix, cells with higher risk physically elevate/extrude in 3D perspective on hover.
- **C1 (Cross-Dimensional Confounds View)**: Interactive 6x2 risk matrix showing both detected cross-dimensional problems and "Verified Safe / Absent" checks. Clicking a cell opens a detail drawer explaining the issue in plain English alongside the stats.
- **D1 (What-If Sandbox & Accuracy Predictor)**: Split-screen simulator wired to the backend's what-if endpoint, with sliders and 1-click "Apply Recommended Fix" buttons that animate the Readiness Score from Baseline -> Projected Score.
- **E1 (Visual Sample Inspector)**: Thumbnail gallery of flagged images with filters (Leakage, Bad Labels, Duplicates, Blurry/Corrupt, Outliers, Demographic Suggestions) and a Side-by-Side Diff modal comparing train/test leaked pairs or duplicate images.
- **F1 (Compare Two Runs)**: Dedicated "Diff Two Audits" view (`Run A` vs. `Run B`) showing before-and-after score improvements after cleaning a dataset.
- **G1 (Frictionless Demo + Password Unlock)**: Visitors can explore existing datasets, 3D visuals, and What-If sliders in read-only mode immediately. Clicking mutating actions (`Upload ZIP`, `Start Audit`, `Delete Dataset`) opens an "Unlock Studio" password modal that stores the shared password defined in the backend environment.

### 3. ENGINEERING QUALITY GATES (Matt Pocock Skills)
- **`strict-typescript`**: Zero `any`, strict null checks, discriminated unions for async run states (`queued | running | completed | failed | cancelled`).
- **`runtime-validation`**: Validate API responses at the boundary so backend/frontend mismatches are caught immediately.
- **`state-resilience`**: Every screen and widget must gracefully handle all 5 UI states: (1) Ideal loaded state, (2) Loading skeletons, (3) Empty state with clear call-to-action, (4) Error state with Retry button, and (5) Partial data state (e.g., when optional fairness metadata was not provided).
- **`to-tickets` & `verification-loop`**: Build incrementally in vertical slices, verifying `tsc --noEmit`, production build (`npm run build`), and backend integration tests (`pytest`) after each slice.
```

---

## 1. Plain-English Overview of What We Are Building

To keep everything crystal clear without heavy statistical or frontend jargon, here is how your frontend works in plain English:

1. **Backend-Driven Stack Selection**: Instead of forcing a rigid frontend setup that might clash with your Python code, the coding agent will first read your FastAPI backend (`dia_2.0_antigravity` branch), check how your endpoints, database models, and passwords work, and automatically configure the cleanest React + TypeScript + Tailwind + 3D setup to match it.
2. **"Explain Like I'm 5" (Plain English) Mode Built Into the App**: Since DIA calculates advanced research metrics (like *Kruskal-Wallis effect sizes* or *Confident Learning noise matrices*), the top bar of your app will have a **[Simple Mode | Engineer Mode]** switch. In **Simple Mode**, every card translates the math into plain English (e.g., *"14 images appear in both your training and test folders, which will fake a high test score"*).
3. **Tactile 3D Visuals**:
   - **3D Readiness Gauge & Tilt Cards**: Your main score gauge and health cards respond to your cursor with smooth 3D perspective tilt, depth shadows, and glass reflections.
   - **3D Image Cluster Explorer**: Users can drag, rotate, and zoom inside a 3D point cloud of their dataset images to visually spot isolated outliers and tightly packed duplicate clusters.
   - **3D Elevated Risk Matrix**: Risk cells in the cross-dimensional matrix visually pop out in 3D space based on severity.

---

## 2. Locked Product Decisions Summary (`A1`–`G1` + `3D`)

| Code | Area | Locked Choice | What It Means in Plain English |
| :--- | :--- | :--- | :--- |
| **STACK** | **Tech Stack & Backend Alignment** | **Auto-Matched to Existing FastAPI Backend** | The agent inspects your Python backend first and sets up React, TypeScript, Tailwind CSS, and 3D WebGL libraries to match your exact API routes and data formats. |
| **A1** | **App Layout** | **Left Sidebar + 5-Tab Studio** | A clean sidebar on the left for switching datasets and runs, and 5 organized tabs in the center so the screen never feels cluttered. |
| **B1** | **Theme & Jargon Control** | **Dark-First Theme + Daylight Toggle + Simple/Engineer Switch** | Sleek dark dashboard by default (with a 1-click light mode button) plus a switch that translates statistical jargon into everyday English. |
| **3D** | **3D Spatial Effects** | **Interactive 3D Cluster Space + 3D Perspective Tilt Cards** | A rotatable 3D scatter plot for image embeddings/outliers, plus interactive 3D tilt and depth lighting on key dashboard cards. |
| **C1** | **Hidden Interactions (Confounds)** | **Interactive 6×2 Grid + Slide-Out Drawer** | A visual grid showing when two problems combine (like one specific class having all the blurry photos). Clicking any box slides out a clear explanation and chart. |
| **D1** | **What-If Simulator** | **Split-Screen Sliders + 1-Click Fix Buttons** | Move sliders or click *"Simulate Fixing Duplicates"* on the left, and watch the predicted AI Readiness Score and model accuracy jump up live on the right. |
| **E1** | **Image Inspector** | **Visual Photo Grid + Side-by-Side Comparison** | Browse flagged photos visually. Click a duplicate or leaked image to see Both Photos Side-by-Side (`Train Image` vs. `Test Image`) and download clean reports. |
| **F1** | **Before vs. After** | **Compare Two Audits (`Run A` vs. `Run B`)** | Pick two runs to see a side-by-side "Before & After" scorecard proving how much healthier the dataset became after cleaning. |
| **G1** | **Password Protection** | **Browse Free + Password Popup for Changes** | Anyone visiting your demo link can click around and test the 3D charts and sliders, while uploading or deleting datasets asks for your shared password. |

---

## 3. Visual Layout Wireframe

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [⚡ DIA 2.0]  Dataset: Industrial-Defects-v2 / Run #04          [💬 Simple | 🔬 Technical] [🔓] [🌙/☀️] │
├────────────────────────┬─────────────────────────────────────────────────────────────────────────────────┤
│ WORKSPACE SIDEBAR      │ STUDIO TABS: [1. Overview] [2. 6 Dimensions] [3. Hidden Interactions]          │
│                        │              [4. What-If Simulator] [5. Image Inspector & Exports]             │
│ [+ Upload Dataset ZIP] ├─────────────────────────────────────────────────────────────────────────────────┤
│                        │ 🚨 BLOCKER ALERT: 14 identical images found in both Train and Test splits!      │
│ 📂 Datasets            │ ┌───────────────────────────────┐ ┌───────────────────────────────────────────┐ │
│ ▾ Industrial-Defects   │ │ 3D TILT READINESS GAUGE       │ │  PREDICTED MODEL ACCURACY IMPACT          │ │
│   • Run #04 [64/100] ● │ │         ╭───────────╮         │ │  Estimated Test Accuracy Loss:            │ │
│   • Run #03 [51/100]   │ │        ╱   64 / 100  ╲        │ │  -6.4% (±1.4% uncertainty)                │ │
│ ▸ MedMNIST-Derma       │ │       │ Needs Fixes   │       │ │  "Fixing dataset issues can recover ~6%"  │ │
│ ▸ FairFace-Subset      │ │        ╲  3D Layered ╱        │ └───────────────────────────────────────────┘ │
│                        │ └───────────────────────────────┘ ┌───────────────────────────────────────────┐ │
│ ⚖️ [Compare Two Runs]  │                                   │  TOP 3 "DO THESE FIRST" FIXES             │ │
│   Run A vs Run B       │ 6 HEALTH SCORES (3D TILT CARDS)   │  1. Remove 14 Train/Test Leaks  [+11.2 pt]│ │
│                        │ [Balance: 72] [Fairness: 68]      │  2. Fix 38 Mislabelled Photos   [+6.5 pt] │ │
│ 🔑 Mode: Read-Only     │ [Quality: 84] [Duplicates: 49]    │  3. Remove 112 Near-Duplicates  [+4.1 pt] │ │
│   [Unlock w/ Password] │ [Diversity:79] [Labels: 61]       │  [Test Fixes in Simulator ➔] [Export CSV] │ │
│                        │                                   └───────────────────────────────────────────┘ │
└────────────────────────┴─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Step-by-Step Build Roadmap (For Antigravity Execution)

1. **Step 1 — Backend Inspection & Project Setup**: Read the FastAPI routes, Pydantic models, and environment config in the repo; scaffold the frontend and add a lightweight image-preview route to FastAPI if needed.
2. **Step 2 — Sidebar, Password Modal & ZIP Upload Wizard**: Build the collapsible left sidebar, the read-only/password-unlock flow (`G1`), and the drag-and-drop dataset upload modal.
3. **Step 3 — Live Audit Progress Tracker**: Show a smooth real-time progress bar while an audit is queued or running in the background, with a cancel button.
4. **Step 4 — Tab 1 (Overview, 3D Tilt Readiness Gauge & Top 3 Fixes)**: Build the main command center with the Simple/Technical language switch, 3D perspective gauge, accuracy impact card, and top 3 prioritized fixes.
5. **Step 5 — Tab 2 (6 Health Dimensions & Interactive 3D Cluster Explorer)**: Build the 6 dimension cards, the label-error heatmap, demographic fairness review table, and the rotatable **3D Embedding & Outlier Explorer**.
6. **Step 6 — Tab 3 (3D Elevated Cross-Dimensional Interaction Grid)**: Build the 6×2 interaction matrix with 3D hover elevation and slide-out plain-English explanation drawers.
7. **Step 7 — Tab 4 (Split-Screen What-If Simulator)**: Wire interactive sliders and 1-click fix buttons to `/what-if` so users can preview their new score in real time.
8. **Step 8 — Tab 5 & Run Diff (Side-by-Side Photo Inspector, Exports & Before/After Comparison)**: Build the visual photo grid, side-by-side duplicate/leakage comparator, 1-click export buttons (`CSV`, `JSON`, `Model Card`, `HTML`), and the `Run A vs. Run B` comparison view.