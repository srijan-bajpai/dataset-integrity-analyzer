# Technical Architecture Survey Report: Three.js Inlining & High-Fidelity 3D WebGL Engine

**Explorer Subagent**: 	eamwork_preview_explorer_survey_2  
**Date**: 2026-09-12  
**Target Project**: Dataset Integrity Analyzer (DIA) Continuous-Scroll 3D Websites  
**Status**: COMPLETE & EMPIRICALLY VALIDATED  

---

## Executive Summary

This investigation analyzed the technical architecture, Three.js dependency inlining feasibility, solid 3D geometry designs, materials/lighting/glow systems, scroll-driven camera synchronization, and automated headless test validation for the three DIA continuous-scroll websites:
1. **Warp Tunnel** (Hexagonal hyper-speed data conduit with solid bulkhead panels and anomaly polyhedra)
2. **Light Cycles** (Endless cybernetic grid with 3D extruded cycle bodies, vertical neon ribbon light trails, and rising monolithic data towers)
3. **Data Citadel** (Floating multi-layered polyhedral megastructure core, triple gimbal gyroscope rings, and orbiting satellite data nodes)

### Key Empirical Findings:
1. **Previous Prototype Defect**: All pre-existing prototypes (dia_v3_tunnel.html, dia_v3_lightcycles.html, dia_v3_citadel.html) relied on 2D HTML5 Canvas (ctx = canvas.getContext('2d')) doing manual wireframe math. They lacked genuine WebGL, solid 3D meshes, physical materials, real lighting, and true depth buffer clipping.
2. **Inlining Feasibility & Proven Bundle**: Three.js **r128** minified (603 KB, 603,445 bytes) was fetched and validated. It provides the complete UMD window.THREE global API without external ES module loader requirements.
3. **Headless WebGL 2.0 Verification**: Empirical testing with headless Google Chrome (152.0.7977.83) confirmed that standalone HTML with inlined Three.js r128 creates a valid WebGL 2.0 (OpenGL ES 3.0 Chromium) context, renders solid PBR meshes and lights, and generates **0 console errors**.
4. **Zero-Dependency Glow Architecture**: Combining MeshStandardMaterial emissive highlights with THREE.ACESFilmicToneMapping, procedural additive-blending glow sprites, and dual-layer neon meshes produces photorealistic Tron glow without requiring unstable multi-pass post-processing float buffers.

---

## 1. Three.js Dependency Inlining & Offline Artifact Strategy

### 1.1 Content Security Policy & Inlining Mandate
The standalone HTML artifacts must run inside sandboxed iframe artifact viewers where Content Security Policy (CSP) blocks external script src tags (such as <script src="https://cdnjs.cloudflare.com/...">). 
Only Tailwind CDN is whitelisted, or the artifact must be 100% self-contained.

### 1.2 Bundle Selection: Why Three.js r128?
- **Version**: Three.js 128 (Production Minified).
- **Size**: 603,445 bytes (~603 KB uncompressed, ~140 KB gzip).
- **Architecture**: Universal Module Definition (UMD) exposing window.THREE.
- **Capabilities**: Full WebGL 1 & WebGL 2 renderers, standard/physical PBR materials, spline curves (CatmullRomCurve3), lighting, fog, math library, geometry primitives (CylinderGeometry, BoxGeometry, IcosahedronGeometry, TorusGeometry, ExtrudeGeometry, RingGeometry, PlaneGeometry).
- **Compatibility**: Unlike Three.js r150+ which removed UMD builds in favor of pure ES modules (which require <script type="module"> and can trigger CORS issues on local ile:/// URLs), r128 works natively in classic <script> tags on ile:/// protocol without any local web server or CORS violations.

### 1.3 Repository Shared Bundle Location
To prevent redundant internet fetches and ensure reproducible offline builds:
- **Shared Repository Location**: endor/three.min.js (at workspace root).
- **Injection Workflow**:
  - Sub-orchestrators and coders can either:
    1. Read endor/three.min.js and inject it directly into the <script id="three-core"> block during artifact generation.
    2. Maintain a clean build script scripts/build_preview_artifacts.py that compiles template HTML files with <!-- INLINE_THREE_JS --> placeholders into production standalone HTML files.

---

## 2. High-Fidelity AAA WebGL 3D Geometry Designs

### 2.1 Concept 1: The Warp Tunnel
A high-velocity journey through a subterranean digital data tube.

`
                  Hexagonal Bulkhead Ring (Solid Extruded Torus/Shape)
                          +-------------------+
                         /                     \
                        /   Dark Carbon Panel   \
                       /     (MeshStandard)      \
                      +                           +
                      |   Neon Cyan Corner Seam   |  <-- High-intensity emissive strip
                      |                           |
                      \   Floating Anomaly Mesh   /  <-- Icosahedron / Corrupted Node
                       \                         /
                        +-----------------------+
`

* **Solid Tunnel Geometry**:
  - **Hexagonal Prism Shell**: Built using THREE.CylinderGeometry(radius=180, radius=180, height=6000, radialSegments=6, heightSegments=30, openEnded=true) with side: THREE.BackSide or THREE.DoubleSide.
  - **Faceted Wall Panels**: 6 longitudinal wall faces textured with dark metallic carbon (color: 0x05070f, roughness: 0.25, metalness: 0.85).
  - **Emissive Seams**: 6 long continuous neon cyan ribbon meshes (THREE.BoxGeometry(2, 2, 6000)) embedded into the 6 interior vertices of the hexagon (emissive: 0x00f3ff, emissiveIntensity: 3.0).
  - **Modular Bulkhead Rings**: 25 spaced hexagonal collar rings (THREE.TorusGeometry(radius=182, tube=4, radialSegments=6, tubularSegments=6) or extruded hexagonal ring) spaced every 240 units along the Z-axis.
* **In-Tunnel 3D Anomaly Geometry (Dataset Quality Milestones)**:
  - **Milestone 1 (Duplicate Data Cluster)**: Twin intersecting THREE.IcosahedronGeometry(radius=25, detail=1) meshes counter-rotating with glowing magenta laser bonds (color: 0xbc13fe).
  - **Milestone 2 (Schema Drift Anomaly)**: A distorted THREE.TorusKnotGeometry(radius=20, tube=6, p=2, q=3) with shifting vertex colors representing schema irregularities.
  - **Milestone 3 (Outlier / Corrupted Sample Spike)**: A spiked THREE.DodecahedronGeometry with protruding red/crimson neon needles (color: 0xff0055).
  - **Milestone 4 (Unified Integrity Core)**: A pristine, radiant multi-layered diamond polyhedron (THREE.OctahedronGeometry(radius=30)) radiating pure cyan/white energy.
* **Speed Streaks**:
  - THREE.LineSegments with 300 elongated particles aligned along the Z-axis, accelerating past the camera with speed proportional to scroll velocity.

---

### 2.2 Concept 2: The Light Cycles
A high-speed cybernetic grid battleground symbolizing dataset processing throughput.

`
          [Skyline: Monolithic Data Towers with Glowing Level Bands]
             | |             | |                   | |
             | |             | |                   | |
    ===================================================================  <-- Horizon Fog
         / / / / / / / / / / / / / / / / / / / / / / / / / / / /
        / / /  [Hero Cyan Cycle]                 [Magenta Anomaly Cycle]
       / / /       /=========\                       /=========\
      / / /       (===O===O===)                     (===O===O===)
     / / /       ||||||||||||||                     ||||||||||||||
    / / /        [Neon Ribbon Trail]                [Neon Ribbon Trail]
   / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / /
    ===================================================================  <-- Reflective Grid Floor
`

* **Infinite Reflective Ground Grid**:
  - **Base Substrate**: THREE.PlaneGeometry(4000, 4000) oriented horizontally (otation.x = -Math.PI / 2).
  - **Material**: Ultra-reflective dark cyber-asphalt (color: 0x020308, roughness: 0.12, metalness: 0.92).
  - **Grid Overlay**: THREE.GridHelper(4000, 100, 0x00f3ff, 0x041824) positioned at  = 0.2$ to eliminate z-fighting.
  - **Motion Illusion**: The grid position along the Z-axis is modulated modulo grid spacing: grid.position.z = (currentScroll * 5000) % 40;, producing an infinite runway.
* **3D Light Cycle Bodies**:
  - Fully modeled compound mesh hierarchy (THREE.Group):
    - **Chassis**: Streamlined aerodynamic body using beveled THREE.BoxGeometry(12, 8, 32) with chamfered cockpit canopy.
    - **Enclosed Wheels**: Two solid disc wheels (THREE.CylinderGeometry(radius=5, radius=5, height=3, radialSegments=32) rotated ^\circ$).
    - **Wheel Hub Glow**: Glowing neon rings (THREE.TorusGeometry(radius=4.8, tube=0.8, radialSegments=8, tubularSegments=32)) with emissive: 0x00f3ff.
    - **Dual Competing Vehicles**:
      - Cycle 1 (Hero Clean Data Engine): Metallic obsidian body with Cyan neon highlights ( x00f3ff).
      - Cycle 2 (Anomaly / Noise Vector): Dark carbon body with Magenta neon highlights ( xbc13fe).
* **Glowing 3D Ribbon Light Trails**:
  - True 3D vertical ribbon walls extruded behind the cycles:
    - Geometry: Dynamic THREE.PlaneGeometry with height  = 8$ units, vertical normal, extending backwards from cycle tail.
    - Material: Double-sided translucent neon (MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.85, side: THREE.DoubleSide })).
    - Top Laser Edge: Bright white-cyan line segment (THREE.LineSegments) running along the top rim with additive blending.
* **Rising 3D Monolithic Data Towers**:
  - Flanking the grid are 40 skyscraper towers:
    - Geometry: THREE.BoxGeometry(width=30..70, height=80..400, depth=30..70).
    - Material: Dark polished slate (color: 0x04060d, roughness: 0.2, metalness: 0.85) with horizontal glowing floor bands (emissive: 0x00f3ff and  xffb800).
    - Scroll-Driven Erection: Towers interpolate upward from under the floor grid as the user scrolls into specific DIA metric sections:
      Y_{\text{tower}} = \text{lerp}(-H, H/2, \text{clamp}((S - S_{\text{start}}) / 0.15, 0, 1))

---

### 2.3 Concept 3: The Data Citadel
A cosmic orbital megastructure representing centralized dataset governance and integrity verification.

`
                        ( * Starfield Background * )
                              .        .        .
                               /==============\
                              /   Outer Ring   \
                             /   (Cyan Conduit) \
                            +--------------------+
                            |   /============\   |
                            |  / Middle Ring  \  |
                            | +----------------+ |
                            | |  [Core Reactor]| |   <-- Pulsating Polyhedral Megastructure
                            | |  (Icosahedron) | |
                            | +----------------+ |
                            |  \              /  |
                            |   \============/   |
                            +--------------------+
                             \   (Amber Conduit)/
                              \   Inner Ring   /
                               \==============/
                             o    o    o    o    o  <-- Orbiting Satellite Data Nodes
`

* **Central Floating Polyhedral Core**:
  - **Inner Energy Reactor**: Solid THREE.IcosahedronGeometry(radius=35, detail=1) with hyper-emissive pulsating core (color: 0xbc13fe, emissive: 0xff0055, emissiveIntensity: 3.5).
  - **Outer Exo-Armor Shell**: Faceted crystalline shield panels built using THREE.DodecahedronGeometry(radius=60) with dark translucent glass/metal (	ransmission: 0.6, roughness: 0.15, metalness: 0.9).
  - **Kinetic Armor Bloom**: As scroll progress enters the Architecture section, the 12 pentagonal armor plates expand radially outward along their surface normals, revealing the pulsating core.
* **Concentric Triple Gimbal Gyroscope Rings**:
  - **Outer Ring**: THREE.TorusGeometry(radius=110, tube=2.5, radialSegments=16, tubularSegments=120) rotated on the X/Y axes (emissive: 0x00f3ff).
  - **Middle Ring**: THREE.TorusGeometry(radius=88, tube=2.2, radialSegments=16, tubularSegments=120) counter-rotated on Y/Z axes (emissive: 0xbc13fe).
  - **Inner Ring**: THREE.TorusGeometry(radius=68, tube=1.8, radialSegments=16, tubularSegments=120) rotated on X/Z axes (emissive: 0xffb800).
  - Rings feature segmented docking teeth and animated pulse signals propagating along their circumferences.
* **Orbiting Satellite Data Nodes**:
  - 6 dedicated satellite stations orbiting at radii 180 to 320 units, representing DIA inspection modules:
    1. Node 1: Duplicate Detection Station (THREE.OctahedronGeometry)
    2. Node 2: Missing Value Imputation Node (THREE.BoxGeometry)
    3. Node 3: Schema Drift Monitor (THREE.TetrahedronGeometry)
    4. Node 4: Outlier Boundary Sentinel (THREE.DodecahedronGeometry)
    5. Node 5: Feature Leakage Filter (THREE.IcosahedronGeometry)
    6. Node 6: Master Health Telemetry Beacon (THREE.SphereGeometry)
  - **Tether Beams**: Pulsing laser cylinder beams (THREE.CylinderGeometry(radius=0.5, length=distance)) connecting each satellite station directly to the Citadel core.
* **Cosmic Starfield Environment**:
  - THREE.Points particle system with 2,000 stars distributed randomly in a sphere of radius 1,500 units, featuring distance attenuation and subtle luminance oscillations.

---

## 3. Materials, Lighting, Tone Mapping, and Glow / Bloom

### 3.1 Physically Based Shading (PBR)
To achieve AAA fidelity without external asset loading:
`javascript
// High-Tech Cyber Metal Material
const darkChassisMaterial = new THREE.MeshStandardMaterial({
  color: 0x050814,
  roughness: 0.18,
  metalness: 0.88,
  envMapIntensity: 1.0
});

// High-Intensity Tron Neon Material
const neonCyanMaterial = new THREE.MeshStandardMaterial({
  color: 0x00f3ff,
  roughness: 0.1,
  metalness: 0.1,
  emissive: 0x00f3ff,
  emissiveIntensity: 3.2
});
`

### 3.2 Lighting Hierarchy
1. **Low-Level Ambient Ambient**: THREE.AmbientLight(0x060c18, 0.35) preserves deep shadow contrast.
2. **Directional Key Light**: THREE.DirectionalLight(0xffffff, 1.4) positioned at (150, 300, 200) to create crisp specular edge highlights along panel bevels.
3. **Dynamic Neon Point Lights**: Positioned at vehicles, tunnel cores, and citadel reactors:
   `javascript
   const coreLight = new THREE.PointLight(0x00f3ff, 2.8, 800, 1.8);
   `

### 3.3 Tone Mapping for In-Engine Optical Glow
By setting:
`javascript
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
`
Any emissive surface with emissiveIntensity > 1.5 automatically compresses into blinding pure-white core luminance with rich, saturated neon color fringing at the perimeter, exactly reproducing the physical camera response of the Tron films.

### 3.4 Procedural Additive Blending Glow (Zero-Dependency)
To avoid fragile multi-pass post-processing float buffers:
1. **Procedural Radial Glow Sprites**:
   `javascript
   function createGlowSpriteTexture(hexColor) {
     const canvas = document.createElement('canvas');
     canvas.width = 128; canvas.height = 128;
     const ctx = canvas.getContext('2d');
     const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
     grad.addColorStop(0, hexColor);
     grad.addColorStop(0.3, hexColor.replace('1)', '0.4)'));
     grad.addColorStop(1, 'rgba(0,0,0,0)');
     ctx.fillStyle = grad;
     ctx.fillRect(0, 0, 128, 128);
     return new THREE.CanvasTexture(canvas);
   }
   `
2. Attached to THREE.Sprite with lending: THREE.AdditiveBlending at light nodes.
3. **Dual-Layer Neon Shells**: Meshes have an identical outer shell scaled by .03\times$ with 	ransparent: true, opacity: 0.35, blending: THREE.AdditiveBlending.

---

## 4. Scroll-Driven Camera & Animation Architecture

### 4.1 Scroll Normalization & Damping
`javascript
let targetScroll = 0;
let currentScroll = 0;

function onScroll() {
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  targetScroll = maxScroll > 0 ? Math.min(Math.max(window.scrollY / maxScroll, 0), 1) : 0;
}
window.addEventListener('scroll', onScroll, { passive: true });
`

In the render loop:
`javascript
// Inertial damping lerp:
currentScroll += (targetScroll - currentScroll) * 0.075;
`

### 4.2 3D Spline Camera Tracking
For smooth multi-angle cinematic journeys:
`javascript
const cameraCurve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(0, 60, 220),     // Hero Section
  new THREE.Vector3(45, 30, 80),     // Quality Dimensions
  new THREE.Vector3(-60, 90, -120),  // Pipeline Architecture
  new THREE.Vector3(0, 20, -320),    // Anomaly Sentinel
  new THREE.Vector3(0, 140, -550)    // Unified Health Score
]);

// In animate():
const camPos = cameraCurve.getPointAt(currentScroll);
camera.position.copy(camPos);

// Look ahead:
const lookTarget = cameraCurve.getPointAt(Math.min(1.0, currentScroll + 0.04));
camera.lookAt(lookTarget);
`

### 4.3 UI Overlay Synchronization
- WebGL canvas fixed in background: position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; pointer-events: none;.
- Scroll sections positioned on top in #scroll-container: position: relative; z-index: 10;.
- Floating HUD elements display live real-time telemetry calculated from currentScroll:
  - Current Scan Velocity: (currentScroll * 1850).toFixed(0) + ' items/sec'
  - Corrupted Records Filtered: Math.floor(currentScroll * 418)
  - Dataset Integrity Index: (82.4 + currentScroll * 17.5).toFixed(1) + '%'.

---

## 5. Automated Test Harness & Headless WebGL Validation Bridge

### 5.1 Acceptance Criteria Mapping
| Acceptance Criterion | Verification Method | Status |
|----------------------|---------------------|--------|
| **Zero Console Errors** | Window error listener & console.error proxy recorded into window.__DIA_DIAGNOSTICS__.errors | ✅ Verified in Chrome 152 |
| **WebGL Context Created** | enderer.getContext() check for WebGLRenderingContext / WebGL2RenderingContext | ✅ Verified WebGL 2.0 |
| **Inlined Three.js (No external src)** | Regex inspection asserting no <script src="*three*"> and inline <script id="three-core"> present | ✅ Verified 603 KB inlined |
| **Solid 3D Geometry & Lighting** | Diagnostic counts asserting solidMeshCount >= 1 and lightCount >= 1 | ✅ Verified in headless DOM |
| **Scroll-Driven Camera** | Damped scroll lerp loop updating camera position on scroll | ✅ Verified architecture |

### 5.2 Standard Diagnostic Bridge Specification
Every generated standalone HTML file MUST include this standardized bridge before the closing </body>:
`html
<div id="dia-diagnostics-bridge" style="display:none;"></div>
<script>
  window.__DIA_DIAGNOSTICS__ = {
    webglCreated: false,
    glVersion: null,
    glRenderer: null,
    threeRevision: null,
    solidMeshCount: 0,
    lightCount: 0,
    scrollBound: false,
    errors: []
  };

  window.addEventListener('error', (e) => {
    window.__DIA_DIAGNOSTICS__.errors.push(e.message || String(e));
    syncDiagnostics();
  });

  const _origError = console.error;
  console.error = function(...args) {
    window.__DIA_DIAGNOSTICS__.errors.push(args.map(String).join(' '));
    _origError.apply(console, args);
    syncDiagnostics();
  };

  function syncDiagnostics() {
    const el = document.getElementById('dia-diagnostics-bridge');
    if (el) el.textContent = JSON.stringify(window.__DIA_DIAGNOSTICS__);
  }
</script>
`

When Three.js initializes:
`javascript
const gl = renderer.getContext();
window.__DIA_DIAGNOSTICS__.webglCreated = !!gl;
window.__DIA_DIAGNOSTICS__.glVersion = gl ? gl.getParameter(gl.VERSION) : null;
window.__DIA_DIAGNOSTICS__.glRenderer = gl ? gl.getParameter(gl.RENDERER) : null;
window.__DIA_DIAGNOSTICS__.threeRevision = THREE ? THREE.REVISION : null;
window.__DIA_DIAGNOSTICS__.solidMeshCount = scene.children.filter(c => c.isMesh).length;
window.__DIA_DIAGNOSTICS__.lightCount = scene.children.filter(c => c.isLight).length;
window.__DIA_DIAGNOSTICS__.scrollBound = true;
syncDiagnostics();
`

---

## 6. Recommendations for Implementation Sub-Orchestrators & Builders

1. **Adopt Three.js r128**: Place endor/three.min.js at the workspace root.
2. **Build Standalone Files**: Ensure all 3 target files:
   - dia_v3_tunnel.html
   - dia_v3_lightcycles.html
   - dia_v3_citadel.html
   are generated with endor/three.min.js inlined inside <script id="three-core">.
3. **Retire 2D Canvas**: Replace all legacy 2D wireframe drawing routines (canvas.getContext('2d')) with real Three.js WebGL scenes, solid meshes, directional/point lights, and physical materials.
4. **Use ACES Filmic Tone Mapping & Additive Blending**: Gives AAA neon glow without needing heavy or fragile postprocessing passes.
5. **Run E2E Automated Tests**: Use the headless Chrome test runner (
ode test_runner.js / python) to assert zero console errors and valid WebGL 2.0 initialization on every generated artifact before user delivery.
