# DIA 2.0 API Demo Guide

The reliable demo path is the database-backed API described in [API_GUIDE.md](API_GUIDE.md). It supports ZIP uploads, persistent dataset and run records, progress tracking, reproducible JSON reports, and sample-level CSV export. The Streamlit screen is still the earlier local prototype; use it only for a visual sketch until the frontend is rebuilt against the v2 API.

## What to demonstrate

1. Start the API and worker using the API guide.
2. Upload a ZIP with at least two class folders or a manifest.
3. Start a run with optional metadata schema, representation targets, and sampling settings.
4. Poll the run status, then inspect the report's class distribution, metadata quality, fairness representation, image quality, duplicates, diversity, label review suggestions, cross-dimension findings, and readiness coverage.
5. Download sample metrics as CSV, compare runs, or cancel a queued/running run.

Describe fairness measurements as evidence for review. A target gap is only meaningful when the target matches the intended use. The impact estimate remains unavailable until a model passes held-out validation. Image-derived attribute suggestions are optional and never replace supplied metadata.
