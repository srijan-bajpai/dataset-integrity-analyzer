# Project: Dataset Integrity Analyzer — AAA WebGL 3D Frontends

## Architecture
This project delivers three distinct, continuous-scroll, production-grade 3D frontend websites for the Dataset Integrity Analyzer (DIA) built with Three.js.
All Three.js dependencies are minified and inlined inside `<script>` tags, making each HTML file fully standalone, portable, and compliant with strict Content Security Policies (CSP).
A dedicated Chrome DevTools Protocol (CDP) headless test harness validates zero console errors, active WebGL 2.0 context, solid PBR meshes, and scroll-synchronized animations.

### Data Flow & System Topology
1. **Empirical DIA Data Source**: Real metrics extracted from `dia_run.db` (310 samples across airplane/automobile/bird, 45 blurred images, 4 confounds, 49.0/100 readiness score, -31.89% downstream accuracy loss).
2. **Three.js Core & Assets**: Minified standalone Three.js r128 bundle (from `.agents/teamwork_preview_explorer_survey_2/three.min.js`), PBR materials, ACES Filmic tone mapping, additive glow sprites.
3. **Scroll Synchronization**: Window scroll progress (0.0 to 1.0) drives 3D camera CatmullRom spline travel, mesh rotations, and synchronized HTML UI section transitions.
4. **Automated Verification**: Headless Chrome runner (`tests/test_3d_frontends.js`) executing 5 verification tiers: C1 (Zero JS Errors), C2 (WebGL 2.0 Context), C3 (Inline Dependencies), C4 (Solid 3D Geometry), and C5 (Scroll Synchronization).

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Automated Headless Test Runner | Zero-dependency Node.js CDP test runner verifying WebGL 2.0, zero console errors, inlining, solid geometry, and scroll | M0 (E2E Test) | Survey 3 |
| 2 | Pytest Integration Hook | Python wrapper integrating headless frontend validation into DIA's pytest suite | M0 (E2E Test) | Survey 3 |
| 3 | Three.js Dependency Inlining | Standalone minified Three.js r128 injected directly into `<script>` tags with zero external script src tags | M1, M2, M3 | Survey 2 |
| 4 | Test Diagnostics Bridge | Exposing `window.__DIA_SCENE__`, `__DIA_CAMERA__`, and `__DIA_RENDERER__` for automated inspection | M1, M2, M3 | Survey 3 |
| 5 | Warp Tunnel: Solid Hexagonal Geometry | 3D procedural hexagonal prism tunnel conduit with depth, segmented rings, and solid panel facets | M1 | Survey 2 |
| 6 | Warp Tunnel: 6-Stage Narrative Scroll | Scroll travel through Ingestion -> Quality Anomaly -> Duplicates -> Confound Vortex -> Health Chamber -> Remediation | M1 | Survey 1 |
| 7 | Warp Tunnel: Empirical Telemetry HUD | Floating cyber HUD displaying 310 samples, 45 blurred images, -31.89% bias impact, 4 confounds | M1 | Survey 1 |
| 8 | Light Cycles: Infinite Grid & Horizon | Continuous glowing neon grid floor with dynamic horizon fog and ACES Filmic lighting | M2 | Survey 2 |
| 9 | Light Cycles: 3D Cycles & Light Trails | Solid 3D cycle models racing across grid leaving glowing extruded ribbon energy trails | M2 | Survey 2 |
| 10 | Light Cycles: Rising Monolithic Data Towers | Dynamic 3D data towers rising from grid representing class imbalance (airplane:200, automobile:60, bird:50) and cluster entropy | M2 | Survey 1 |
| 11 | Light Cycles: 6-Stage Narrative Scroll | Telemetry Horizon -> Diversity Trails -> Imbalance Towers -> Redundancy Shockwave -> Consensus Obelisk -> Remediation | M2 | Survey 1 |
| 12 | Data Citadel: Massive Floating Fortress | Central floating polyhedral megastructure core with rotating outer defense rings and floating satellite data nodes | M3 | Survey 2 |
| 13 | Data Citadel: 6 Orbiting Bastions | 6 modular 3D bastions representing the 6 DIA dimensions: Balance, Fairness, Quality, Uniqueness, Diversity, Label Integrity | M3 | Survey 1 |
| 14 | Data Citadel: Deep Core Reactor Vault | Orbiting camera zooming into reactor core displaying 49.0 Safety Hard-Gate and Kruskal-Wallis confounds | M3 | Survey 1 |
| 15 | Data Citadel: 6-Stage Narrative Scroll | Perimeter Approach -> Bastion Inspection -> Confound Scan -> Reactor Vault -> Oracle Simulation -> Fortification Protocol | M3 | Survey 1 |
| 16 | E2E Regression & Adversarial Hardening | 100% pass across all 3 HTML files under headless browser test suite + adversarial stress testing | M4 | Survey 3 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | E2E Testing Track | Headless CDP test runner (`tests/test_3d_frontends.js`), pytest integration (`tests/test_webgl_frontends.py`), TEST_INFRA.md, TEST_READY.md | none | IN_PROGRESS |
| M1 | Warp Tunnel 3D Website | Full implementation of `dia_v3_tunnel.html` with solid hexagonal tunnel, Three.js inlining, scroll camera lerp, and DIA HUD | M0 (interface defined) | PLANNED |
| M2 | Light Cycles 3D Website | Full implementation of `dia_v3_lightcycles.html` with infinite neon grid, racing cycles, rising data towers, inlining, and scroll HUD | M0 (interface defined) | PLANNED |
| M3 | Data Citadel 3D Website | Full implementation of `dia_v3_citadel.html` with floating fortress, 6 bastions, deep core zoom, inlining, and scroll HUD | M0 (interface defined) | PLANNED |
| M4 | Final Milestone: 100% E2E Pass & Coverage Hardening | Execute full test suite across all 3 sites, verify 5/5 criteria pass, run adversarial challenger, and deliver final artifacts | M1, M2, M3 | PLANNED |

---

## Interface Contracts
### Implementer Contract (All 3 Websites)
1. **DOM & Global Exposure**:
   - `window.__DIA_SCENE__`: Reference to the active `THREE.Scene` instance.
   - `window.__DIA_CAMERA__`: Reference to the active `THREE.PerspectiveCamera` instance.
   - `window.__DIA_RENDERER__`: Reference to the active `THREE.WebGLRenderer` instance.
2. **Three.js Inlining**:
   - Injected directly into `<script>` inside `<head>` or `<body>`.
   - Source: `.agents/teamwork_preview_explorer_survey_2/three.min.js`.
   - Strict rule: ZERO external `<script src="...">` tags for Three.js. (Tailwind CDN is allowed for styling).
3. **Scroll Synchronization**:
   - Camera position and lookAt target interpolate smoothly based on normalized scroll progress: `const progress = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);`
4. **Rendering Quality**:
   - Renderer configured with `antialias: true`, `powerPreference: 'high-performance'`.
   - Output encoding: `THREE.sRGBEncoding`, Tone mapping: `THREE.ACESFilmicToneMapping`.
   - Meshes built using `THREE.BufferGeometry` and `THREE.MeshStandardMaterial` or `THREE.MeshPhysicalMaterial` with proper directional and point lights.

### Test Harness Contract
- Test runner invocation: `node tests/test_3d_frontends.js --target=<html_file_path>`
- Pytest invocation: `pytest tests/test_webgl_frontends.py`
- Pass criteria:
  - C1: 0 uncaught exceptions and 0 console.error logs.
  - C2: Active WebGL 2.0 / WebGL context (non-null, context not lost).
  - C3: No external Three.js script src tags; Three.js symbols defined.
  - C4: Active scene contains >= 3 solid `THREE.Mesh` objects with `BufferGeometry` and solid materials.
  - C5: Simulated scroll (50% page height) produces camera position/rotation displacement `delta > 0.001`.

---

## Code Layout
- Test Suite:
  - `tests/test_3d_frontends.js`: Node.js CDP test runner
  - `tests/test_webgl_frontends.py`: Pytest integration test
- Frontend Artifacts:
  - `C:\Users\SRIJAN BAJPAI\.gemini\antigravity\brain\7fa9d356-547c-450d-bf4a-e7b9aefd5206\dia_v3_tunnel.html`
  - `C:\Users\SRIJAN BAJPAI\.gemini\antigravity\brain\7fa9d356-547c-450d-bf4a-e7b9aefd5206\dia_v3_lightcycles.html`
  - `C:\Users\SRIJAN BAJPAI\.gemini\antigravity\brain\7fa9d356-547c-450d-bf4a-e7b9aefd5206\dia_v3_citadel.html`
  - Workspace copies in `frontends/` directory for repository persistence.
- Vendor Assets:
  - `.agents/teamwork_preview_explorer_survey_2/three.min.js`: Minified standalone Three.js r128 library for inlining.
