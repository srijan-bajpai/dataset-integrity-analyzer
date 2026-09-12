# UI Library Workaround

When building generative UI prototypes that require external Javascript libraries (like Three.js) which are blocked by the strict Content Security Policy (CSP) on external CDNs, you MUST inline them to bypass preview sandbox restrictions:

1. **Do not** attempt to load them via external <script src="https://cdn..."> tags.
2. **Download them locally** into the active artifact directory using Invoke-WebRequest (on Windows) or curl (on macOS/Linux).
3. **Inline the library** directly into the generated HTML artifact. Do NOT use a relative path like <script src="three.min.js"></script>, as the preview iframe sandbox will block local file loading.
4. Because the file will be massive, write a short Node.js script via the terminal to read the downloaded JS file and inject it into your HTML file, replacing a placeholder script tag.
5. **Do not** use ead_url_content and write_to_file to download minified JS libraries, as it will destroy the formatting and exceed context limits. Use native terminal commands.
