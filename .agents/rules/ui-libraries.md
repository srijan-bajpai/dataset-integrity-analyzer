# UI Library Workaround

When building generative UI prototypes that require external Javascript libraries (like Three.js) which are blocked by the strict Content Security Policy (CSP) on external CDNs:

1. **Do not** attempt to load them via external `<script src="https://cdn...">` tags.
2. **Download them locally** into the active artifact directory using `Invoke-WebRequest` (on Windows) or `curl` (on macOS/Linux).
   Example: `Invoke-WebRequest -Uri "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js" -OutFile "C:\path\to\artifact\dir\three.min.js"`
3. Include the downloaded library in your HTML using a relative path: `<script src="three.min.js"></script>`.
4. **Do not** use `read_url_content` and `write_to_file` to download minified JS libraries, as it will destroy the formatting and exceed context limits.
