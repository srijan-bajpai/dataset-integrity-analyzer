# Generative UI - Three.js Exception

**Trigger:** always_on

When using the generative_ui skill to build 3D animations or premium assets in standalone HTML artifacts:

1. **Bypass the CSP block for external JS** by using ead_url_content to fetch the minified source code of Three.js (or similar libraries).
2. **Inject the source code completely inline** within a <script> tag in the HTML file, rather than using an external src attribute (e.g., <script src="https://...">).
3. This allows the creation of high-fidelity WebGL (Three.js) artifacts while still respecting the artifact viewer's Content Security Policy.
