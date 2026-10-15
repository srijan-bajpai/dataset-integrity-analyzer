# Project State: Dataset Integrity Analyzer (DIA)

## Project Objective
Develop a unified AI dataset health assessment framework that evaluates datasets across six dimensions (fairness, class balance, image quality, duplication, diversity, label integrity) on a shared sample index. The system detects cross-dimensional confounds, computes an AI Readiness Score, and predicts downstream bias impact (accuracy/fairness degradation), delivering prioritised recommendations before model training.

## Proposed Architecture
- **Data Model**: A shared SQLite database tracking a unified `Sample` record (path, class, inferred attributes, quality metrics, duplicate group, cluster ID) and a separate `.npy` file for high-dimensional embeddings (D1 and D2 in SRS).
- **Stack (Simplified for Prototype)**: 
  - **Core/Backend**: Python 3.10+, PyTorch (feature extraction, demographic inference), OpenCV/Pillow (quality), imagehash (duplicates), scikit-learn (diversity/clustering, confound tests).
  - **Frontend/UI**: Streamlit (replaces the complex FastAPI + React stack for faster iteration while meeting all visualization requirements).
  - **Persistence**: SQLite (metadata) + local file system (embeddings).

## Current Phase
**COMPLETE**: The Dataset Integrity Analyzer prototype is fully functional, tested, documented, and ready for demonstration. All phases (1-17) have been successfully autonomously executed.

## Planned Phases (Risk-Driven Incremental)
1. **Increment 1 (COMPLETED)**: C2 Feasibility Spike. 
   - *Result*: Monotone degradation curve successfully observed (IR 1.0 -> 89.5%, IR 5.0 -> 77.2%, IR 20.0 -> 50.0%). The C2 hypothesis is viable.
2. **Increment 2 (Current)**: Skeleton + Shared Representation + Ingestion + 1-2 Dimensions (e.g., Quality & Imbalance). Validate that the shared DataFrame/SQLite approach works.
3. **Increment 3**: Remaining single dimensions (Duplicates, Diversity, Labels, Attribute Inference).
4. **Increment 4**: Cross-Dimensional Confound Analysis (C1) & AI Readiness Scoring.
5. **Increment 5**: Full Bias Impact Prediction (C2) & Recommendation Engine.
6. **Increment 6**: Streamlit UI & Final Reporting.

## Important Decisions
- **Streamlit over React/FastAPI**: Reduces boilerplate and accelerates prototype delivery while maintaining interactive charts and tables.
- **Pandas/SQLite for Shared Record**: All analyzers will append columns to a central Pandas DataFrame, which is synced to SQLite.
- **Local GPU Utilization**: The RTX 3050 6GB will be used for embedding extraction and surrogate model training. Batch sizes will be kept small to fit in 6GB VRAM.

## Risks
- **C2 Feasibility (High)**: Predicting downstream impact from dataset statistics might yield noisy or non-monotonic results. The feasibility spike is designed to test this immediately.
- **Compute Constraints (Medium)**: 6GB VRAM limits surrogate training speed and batch sizes.
- **Attribute Inference Accuracy (Medium)**: Relying on pre-trained models for demographics might introduce its own biases.

## Next Actions
1. Set up the Python project structure and `requirements.txt`.
2. Implement the C2 Feasibility Spike (`experiments/c2_spike.py`) to validate the core research contribution.

## DIA 2.0 Frontend Milestone (COMPLETED)
- Implemented full production Web Studio in `frontend/` matching `dia_frontend_architecture_ideation_plan.md` and Pocock skills (`strict-typescript`, `runtime-validation`, `state-resilience`, `component-architecture`, `tailwind-craft`).
- Architecture: React 18, TypeScript (strict, zero errors), Tailwind CSS, Three.js 3D WebGL, Zod runtime validation, and Vite static bundler.
- Features:
  - Multi-tab studio: Overview & Readiness, 6 Dimensions, Confounds (C1), What-If Simulator (C2), Sample Triage & Exports.
  - Interactive 3D Embedding & Outlier Cluster Explorer in Three.js with raycast sample thumbnails, orbit drag, zoom, and outlier halos.
  - 3D perspective tilt cards with spring physics and dynamic specular glare.
  - 6x2 C1 Bivariate interaction risk matrix with 3D elevation on hover and slide-out plain English drawers.
  - Real-time What-If sandbox sliders with score delta animations and 1-click fix presets.
  - Dual audience toggle (Plain English / ELI5 vs. Technical / Stats).
  - G1 Frictionless demo mode with password unlock modal.
  - Direct 1-click downloads for standalone HTML report, Model Card Datasheet (MD/JSON), and Remediation Manifest CSV.
  - Automated integration test suite: 39 pytest tests passing (including 3D embeddings endpoint and static SPA mount).

## DIA 2.0 Full-Stack Integration & AWS Readiness Milestone (COMPLETED)
- **Seamless Full-Stack Integration**: Integrated Vite frontend bundle into FastAPI backend with SPA fallback routing, CORS compliance, and unified static serving on port 8000.
- **Image & Telemetry API Bridging**: Added run-based and thumbnail sample image routes, wired up live image rendering across 3D Map and photo triage views, and enabled 1-click lossless diagnostic metric downloads.
- **Multi-Stage Docker Architecture**: Built multi-stage `Dockerfile` (Node 20 builder + Python 3.12 runtime) with container healthchecks, and created `entrypoint.sh` supporting `api`, `worker`, and `all-in-one` execution modes.
- **AWS Deployment Assets**:
  - `aws/cloudformation.yaml`: Complete production infrastructure stack (ALB + ECS Fargate + RDS PostgreSQL 16 + Amazon EFS encrypted shared storage).
  - `aws/deploy-ec2.sh`: 1-command automated deployment script for Amazon Linux 2023 / Ubuntu with systemd auto-restart service and health check verification.
  - `aws/apprunner.yaml`: Configuration for serverless container execution on AWS App Runner.
  - `aws/s3-sync.sh`: S3 backup and restore utility for `/data` storage.
  - `docs/AWS_DEPLOYMENT_GUIDE.md`: Comprehensive end-to-end cloud deployment manual.
- **Quality Assurance**: Frontend builds with 0 TypeScript errors (`npm run build`), all 39 pytest tests pass with 100% success rate, and live endpoint verification confirms seamless HTML and API serving.


