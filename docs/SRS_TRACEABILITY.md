# SRS traceability for DIA 2.0 backend MVP

This matrix is the handoff boundary for the current backend branch. “Implemented” means there is a corresponding API/analyzer path and automated coverage where feasible. “Partial” means the MVP emits bounded evidence but does not meet the full research, validation, or reporting requirement. Frontend work remains deferred by the project decision.

| SRS area | Status | Implementation / acceptance evidence |
| --- | --- | --- |
| REQ-1…9: formats, metadata, fingerprint, corrupt images, class checks, sampling | Implemented | `dia/core/ingestion.py`, upload API, stratified deterministic sample selection and report provenance; ingestion/API tests. |
| REQ-10…16: face-derived attributes, detection coverage, validated FairFace inference | Deferred | Filename-parsed UTKFace fields are tagged by provenance; opt-in suggestions learn from this dataset's own supplied metadata. No face detector/classifier is shipped, so no claim of validated demographic inference or FairFace accuracy is made. |
| REQ-17…24: class/group representation, target gaps, uncertainty, split skew | Implemented / partial | Counts, IR, normalized entropy, Gini, Wilson intervals, optional target gaps, class association statistics, intersectional low-support counts and split Jensen-Shannon divergence. Do not interpret association as causation. |
| REQ-25…30: image quality and anomaly checks | Implemented / partial | Blur, Lab brightness/contrast, high-pass residual MAD noise, resolution, aspect ratio, file size, lighting category, thresholds, corrupt/all-black/all-white/zero-variance flags. BRISQUE has an explicit unavailable status because no validated BRISQUE model is configured. |
| REQ-32…38: duplicates and leakage | Implemented / partial | SHA-256 exact duplicates; BK-tree pHash candidate search; when ResNet features are available, pHash candidates require cosine similarity ≥0.98; conflicting labels and cross-split groups are reported and gate readiness. Without embeddings, near-duplicate evidence is marked perceptual-hash-only. |
| REQ-40…46: visual diversity | Implemented / partial | Local ResNet-18 embeddings, silhouette-selected KMeans, DBSCAN, cluster entropy, per-class cosine diversity and low-coverage flags. UMAP visualization is deferred to frontend. |
| REQ-47…52: label issues and model reliability | Partial | Stratified out-of-fold logistic regression identifies label disagreement candidates and documents limitations. It is not a full confident-learning implementation, benchmark reliability study, or validated class-noise estimator; low-support cases are unavailable, never reported as zero error. |
| REQ-53…63: unified sample findings, interactions, recommendations | Partial | Run-versioned sample JSON metrics, class/attribute quality comparisons, duplicate and label associations, evidence-linked recommendations, report provenance. Full anomaly/outlier benchmark validation and every requested interaction are not complete. |
| REQ-64…73: accuracy impact predictor | Deferred | Returns `unavailable`; enable only after training/evaluation on controlled variants and passing a documented held-out error threshold. |
| REQ-74…80: readiness formula and scoring | Implemented / partial | Versioned SRS dimension weights; only measured dimensions contribute and coverage is shown. Effect-size-based confound penalty is documented. Leakage or a measured sub-score below 30 forces `Not Ready`; the numeric score is not capped. A non-persistent API what-if rescore accepts only dimensions present in the baseline report. |
| REQ-81…88: remediation and manifests | Partial | Ranked recommendations and per-sample CSV export exist. Automated recommended-change manifests and full action-impact simulation remain future work. |
| REQ-89…96: reports, rerun, compare, model card, reproducibility | Partial | Persisted versioned JSON reports, CSV export, rerun as a new run, run comparison, migration history, fingerprint/config/model provenance. PDF/HTML reports and generated model-card/datasheet exports are deferred. |
| NFR-P*: scale, batch progress, cancellation, caching | Partial | MVP cap is configurable and defaults to 2,000 samples; ResNet runs in batches with progress; queued/running work can be cancelled; abandoned jobs are requeued. No derived-result cache is implemented yet. |
| NFR-S* / SEC*: storage and service security | Implemented / partial | Source ZIP and extracted files stay in persistent local storage until explicit deletion; traversal, symlink, size, decode and decompression-bomb checks; shared-password option and production enforcement; SQLite local / PostgreSQL hosted. TLS must be terminated by the hosting proxy. Dedicated model-signature inventory and independent security review remain open. |
| OR-5…10: licenses, data handling, imports, perturbation harness, i18n | Partial | Pipeline is importable outside the web service; no benchmark data is redistributed; no telemetry or third-party image inference is used. Full license inventory, perturbation harness, and localization remain future work. |

## Portable continuation rules

Use the SRS as the source of named requirements and this file as the current implementation boundary. Keep each analyzer's status explicit (`available`, `limited`, or `unavailable`), preserve user metadata, record provenance and versions, and never turn missing evidence into a zero-risk result. Add controlled fixtures with known outcomes before changing a metric threshold. Do not enable image-derived demographic inference or an accuracy-impact estimate without documented validation data and held-out evaluation. Frontend implementation starts only after the API contract and report schema are accepted.

## Remaining backend work before calling the SRS fully satisfied

1. Add full NFR performance/security benchmarks at the 2,000-image ceiling and verify container persistence on a Docker-capable host.
2. Validate duplicate and diversity thresholds on controlled image transformations; capture quality metric fixtures across formats and resolutions.
3. Complete confident-learning and outlier checks, benchmark per-class reliability, and add false-discovery/effect-size treatment to every inferential comparison.
4. Complete recommendation manifests and interaction coverage, and derived-result caching.
5. Add PDF/HTML and model-card/datasheet report artifacts if they remain required after frontend scope is defined.
6. Run the controlled C2 training study; keep the predictor unavailable until its acceptance threshold is met.
