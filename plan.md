 
# Dataset Integrity Analyzer: Demo to Database-Backed MVP

## Summary

Turn DIA into a Python API that accepts image-classification datasets, stores them and their audit results in a database, and reports measurable signs of dataset risk. Build on the six dimensions named in the project notes: fairness, class balance, image quality, duplicates, visual diversity, and label integrity. Add metadata checks and analysis of how those dimensions relate to each other.

The MVP is for your course project and a personal hosted demo. It supports datasets of up to about 2,000 images, works locally, and can be deployed behind one shared password. Frontend design and implementation come later; the API and report format will be ready for them.

## Decisions and implementation

- Backend and database: Use FastAPI, SQLAlchemy, and Alembic. Use SQLite locally and PostgreSQL for the hosted demo. Keep image files and embedding artifacts in persistent file storage; store their locations and analysis data in the database. Track datasets, samples, attributes, analysis runs, metrics, and findings. Keep uploads until the user deletes the dataset.
- Upload and dataset formats: Accept ZIP uploads containing either class-named folders or a CSV/JSONL manifest. A manifest must identify each image by relative path and can include its class label, split, and additional attributes. Support JPEG, PNG, WebP, BMP, and TIFF images. Enforce configurable compressed and extracted size limits, reject unsafe archive paths and unreadable files, and give clear errors for invalid datasets. Support classification only in v1.
- API and run lifecycle: Provide endpoints to upload and list datasets, start an audit, check run status, retrieve its report and flagged samples, and delete a dataset. Save each run’s configuration, analyzer and model versions, status, and results. Use a database-backed job queue and one worker so long audits run independently of upload requests and can recover cleanly after a restart.
- Audits: Retain analyzers whose results can be checked against known cases. Measure class counts and imbalance; attribute counts and differences from user-supplied targets; missing, invalid, and inconsistent metadata; image quality; exact and near-duplicate images, including duplicates across splits; visual diversity; and suspicious label disagreements. Compare relevant dimensions, such as group representation by class and image quality by group. Include sample counts and uncertainty, and mark comparisons as unavailable or unreliable when data is insufficient.
- Fairness and attribute estimates: Let users set expected group proportions. Without a target, show representation and observed differences without labeling a dataset unfair. Allow opt-in image-based suggestions for attributes named in the SRS, such as age, gender presentation, and skin tone. Keep suggestions separate from supplied metadata, record confidence and model version, and return uncertain or conflicting cases for review. Never overwrite metadata or send images to a third-party inference service.
- Scores and impact estimate: Keep dimension scores and an overall readiness score only with documented, versioned calculations. Start from the weights already in the project notes, redistribute weight only across dimensions that were actually measured, and show how much of the score is covered. Remove the hard cap and never treat missing fairness information as a perfect score. Replace the current hand-written accuracy-drop formula with an estimate validated against actual training and evaluation on controlled dataset variants. Show it only within conditions where the validation supports it; otherwise report that the estimate is unavailable.
- Reports and deployment: Return a machine-readable JSON report containing metrics, findings, affected sample references, recommendations, uncertainty, and run configuration. Use a Docker-based deployment setup that can run with PostgreSQL and persistent file storage. Require one shared password from an environment setting for the hosted demo. Document setup, API use, supported formats, metric meanings, limits, and how to reproduce an audit.

## Delivery order

1. Requirements and baseline: Map every SRS requirement to an acceptance check and note which current code supports it. Treat the project’s six dimensions as the starting checklist. Record which demo claims must be replaced, especially the fairness placeholder and impact heuristic.
2. Data and service foundation: Define the API, database models, migrations, upload validation, persistent file storage, job queue, and run lifecycle.
3. Reliable ingestion and core checks: Implement both dataset layouts and validate each retained analyzer with controlled data. Make small, incomplete, and malformed datasets fail clearly or return explicitly limited results.
4. Metadata and cross-dimension analysis: Add group comparisons, metadata checks, uncertainty, findings, and reviewable opt-in attribute suggestions.
5. Scoring and impact validation: Document and test score behavior. Compare the impact estimate with real training runs on controlled variants; suppress it if validation is not useful.
6. Deployment and handoff: Package the password-protected service, verify persistence and deletion, and finish the API and reproducibility documentation. Begin frontend work only after the API and report format are stable.

## Test plan and acceptance

- Test folder and manifest ingestion, optional splits and attributes, stable sample references, supported image formats, unsafe ZIP paths, size limits, corrupt files, missing labels, and single-class datasets.
- Use small fixtures with known class ratios, group proportions, missing and invalid metadata, duplicates, label disagreements, and image-quality differences. Verify reported counts, affected samples, and uncertainty against those known cases.
- Confirm that attribute suggestions remain separate from supplied values, include confidence and model version, and never fill in fields automatically.
- Train and evaluate a baseline model on controlled dataset variants. Compare the impact estimate with measured changes on held-out variants; show the estimate only if its error meets the documented acceptance threshold.
- Confirm that runs can be started, monitored, retrieved after a service restart, and deleted with their stored files. Verify that hosted uploads require the shared password.
- Confirm a clean local setup and hosted deployment using the documented instructions.

## Assumptions and defaults

- The project notes and code references name the six audit dimensions; the first delivery step maps the complete SRS to checks before implementation begins.
- The MVP is single-user, classification-focused, and limited to about 2,000 images per dataset.
- ZIP is the API upload container; class folders and CSV/JSONL manifests are the supported layouts.
- Audit results are evidence and review signals. The project will not claim to prove that a dataset or model is fair.
- Frontend work is deferred until the backend contract and report format are stable.

## Current implementation status and agent handoff

This plan is fully implemented on the `dia_2.0_antigravity` branch:

1. **Database & API Lifecycle**: FastAPI REST API, SQLAlchemy models, Alembic migrations, database-backed job queue, and background worker with lease recovery, cancellation, run comparison, what-if rescoring, and dataset deletion.
2. **Safe Ingestion**: Folder-per-class, split-nested, and CSV/JSONL manifest layouts with zip-slip/bomb protection, SHA-256 fingerprinting, corrupt file tolerance, and deterministic stratified sampling.
3. **Core Audits & Confident Learning (REQ-1..52)**: Imbalance ratios, normalized entropy, Gini coefficient, target gaps, image blur, Lab brightness/contrast, noise MAD, exact and perceptual duplicate detection (pHash + cosine sim >= 0.98), cluster redundancy & prunable sample count estimation, full out-of-fold confident learning with joint noise matrix and per-class reliability scores, and Isolation Forest embedding outlier detection.
4. **Cross-Dimensional Confounds (C1, REQ-54..63)**: Battery of 6 cross-dimensional tests (Quality x Class, Quality x Attribute, Redundancy x Class with effective counts, Diversity x Class correlation, Label Noise x Class, and Leakage x Class) with Benjamini-Hochberg FDR correction, Kruskal epsilon-squared effect sizes, and explicit absent confounds reporting.
5. **Bias Impact Predictor & Benchmark Harness (C2, REQ-64..73, OR-9)**: 16-D bias descriptor vector, reusable synthetic-perturbation harness, and empirical validation study (`experiments/c2_validation_study.py`) achieving $R^2 \approx 0.89$ and MAE $\approx 1.43$, with feature ablation proving the marginal necessity of cross-dimensional confounds (C1).
6. **Prioritised Remediation & Actionable Manifests (REQ-81..88)**: Readiness score gain simulation, gain-per-effort ranking with top-3 "Do these first" badges, confound-aware suppression of naive oversampling, trade-off warnings, and machine-actionable per-sample CSV/JSON manifests (`/remediation-manifest.csv`, `/remediation-manifest.json`).
7. **Report Artifacts & Exports (REQ-89..95)**: Standalone zero-dependency HTML report (`/report.html`), Gebru et al. Model Card / Datasheet JSON and Markdown export (`/model-card.json`, `/model-card.md`), lossless JSON audit report, and per-sample CSV export.
8. **Performance, Security & Headless CLI (NFR-*, REQ-UI-10, OR-8)**: Fast re-run embedding caching, CLI interface (`dia analyze` / `python -m dia analyze`), read-only dataset protection, and shared-password authentication.
9. **Automated Test Suite**: 36 automated unit, integration, transformation, and security tests in `tests/` passing on Python 3.12.

See [docs/SRS_TRACEABILITY.md](docs/SRS_TRACEABILITY.md) for the complete requirement-by-requirement verification matrix.
