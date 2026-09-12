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
**Phase 2: Single-Axis Analyzers**. The critical risk-retirement spike for the Bias Impact Predictor (C2) has successfully completed, proving the core hypothesis. We are now building the unified data ingestion pipeline and individual dimension analyzers.

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
