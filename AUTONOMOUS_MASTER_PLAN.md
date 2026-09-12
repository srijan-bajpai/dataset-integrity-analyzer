# Autonomous Master Plan: Dataset Integrity Analyzer (DIA)

## 1. Project Objective
Build a functioning, demonstrable prototype of the Dataset Integrity Analyzer (DIA), allowing a user to provide an image classification dataset and receive an integrated dataset-health audit. The system will detect issues across multiple dimensions, predict their downstream impact, and generate prioritized recommendations.

## 2. Core Research Contribution
The primary novelty is **unification**: running all dataset analyzers (class balance, fairness, quality, duplicates, diversity, labels) over a **shared sample-level representation**. This enables the detection of cross-dimensional confounds (e.g., quality × demographic) and the formulation of a unified AI Readiness Score and Bias Impact Predictor.

## 3. Prototype Scope
- Focused on image classification datasets.
- Local execution on Consumer-grade GPU (NVIDIA RTX 3050 6GB).
- Implementation of the core analyzers, a unified readiness score, and a simplified bias impact predictor based on the C2 feasibility spike.
- A functional web dashboard for uploading, analyzing, and reviewing results.
- End-to-end reproducibility and stability over exhaustive productionization.

## 4. Simplifications Made Compared with the SRS
- **Frontend**: Streamlit replaces the specified FastAPI + React stack to drastically reduce boilerplate and speed up prototype iteration without losing visual fidelity.
- **Data Persistence**: Pandas DataFrames synced to SQLite (or directly persisted as Parquet/CSV) replaces heavy DB ORMs.
- **Bias Impact Predictor (C2)**: A lightweight CNN (e.g., ResNet-18) trained on binary subset datasets (like the CIFAR-10 spike) will serve as the surrogate model, ensuring experiments fit within the 6GB VRAM limit.

## 5. Architecture
- **L1 (Ingestion)**: Folder-per-class parsers to load data.
- **L2 (Extraction)**: PyTorch feature extractor for embeddings; lightweight attribute inference.
- **L3 (Analysis)**: Independent dimensional analyzers operating on the shared data frame.
- **L4 (Scoring & Impact)**: Readiness score aggregator, Kruskal-Wallis cross-dimensional confound tests, and the Bias Impact Predictor.
- **L5 (Presentation)**: Streamlit dashboard.

## 6. Data Model
A unified, shared table tracking every sample.
Columns include: `sample_id, path, split, ground_truth_class, inferred_attributes (gender/age/skin_tone), quality_metrics (blur/brightness/contrast/noise/resolution), hash, duplicate_group, cluster_id, label_issue_flag`. Embeddings will be cached as numpy `.npy` arrays.

## 7. Analysis Pipeline
1. Dataset Ingest & Schema Validation
2. Feature Extraction (Embeddings)
3. Quality & Duplicates Analysis
4. Diversity Clustering
5. Label Auditing
6. Confound Analysis (Merging outputs)
7. Final Readiness Score & Remediation generation

## 8. ML Components
- **Feature Extractor**: Pre-trained ResNet-18/50.
- **Duplicates**: Perceptual hashing (pHash) and embedding cosine similarity.
- **Diversity**: K-Means clustering & UMAP projection.
- **Bias Predictor**: Lightweight regression model mapping dataset statistics to accuracy degradation.

## 9. Frontend/Dashboard Plan
A Streamlit app with:
- Upload/Config Sidebar
- Analysis Progress Spinner
- Health Dashboard (Readiness Score Gauge + Radar Chart)
- Detailed Findings (Per-dimension charts, confound alerts)
- Export Report function

## 10. Testing Strategy
- Unit tests for statistical validity (e.g., ensuring Imbalance Ratio math is correct).
- Synthetic fixture datasets crafted to guarantee a known defect (e.g., an exact 5:1 imbalance or obvious duplicated files).
- Robustness testing on degenerate datasets (e.g., tiny images, single-class datasets) to ensure graceful failure.

## 11. Public Dataset Validation Strategy
Validate DIA against:
- **CIFAR-10** (for basic sanity, duplicate checks, label noise).
- A facial dataset (e.g., **UTKFace** or subset) for demographic inference and fairness/quality confounds.
Datasets will be downloaded locally and firmly `.gitignore`d.

## 12. Git/Checkpoint Strategy
Continuous checkpointing to the local repository (`master` branch).
- **Rule**: Create a checkpoint commit before any major refactor.
- **Rule**: Commit and push (`feat: ...`) after each passing phase.
- **Rule**: Never commit datasets, large embeddings, or model checkpoints.

## 13. Development Phases
- **Phase 0**: Establish the Master Plan (Current).
- **Phase 1**: Local Environment Setup & Hardening.
- **Phase 2**: C2 Feasibility Spike (Completed in earlier steps).
- **Phase 3**: Core Dataset Analysis Engine (The single-axis tools).
- **Phase 4**: Cross-Dimensional Intelligence.
- **Phase 5**: Unified AI Readiness Score.
- **Phase 6**: Bias Impact Predictor (Integration of C2).
- **Phase 7**: Recommendation Engine.
- **Phase 8**: Dashboard / UX.
- **Phases 9-14**: Validation, Testing, Performance Tuning.
- **Phases 15-17**: Documentation & Final Review.

## 14. Completion/Acceptance Criteria
- DIA starts successfully as a Streamlit app.
- A user can supply an image dataset and receive an integrated health audit.
- Cross-dimensional analysis successfully detects confounds on controlled data.
- An interpretable 0-100 score is produced alongside actionable recommendations.
- The repository contains clear `DEMO_GUIDE.md` and `DEMO_CHEATSHEET.md`.
- Automated synthetic ground-truth tests pass.
- Git history demonstrates iterative, safe checkpointing.

## 15. Final Demonstration Plan
A 5-minute interactive walkthrough of the Streamlit dashboard on a prepared public dataset (e.g., a subset of CIFAR-10 with injected defects) that highlights the AI Readiness Score, drills down into a cross-dimensional quality confound, and showcases the Bias Impact Predictor's degradation warning.

## Final Status
COMPLETE. All acceptance criteria met. Prototype is ready for presentation.
