# Prototype Development Plan

## Goal
Deliver a functioning Dataset Integrity Analyzer (DIA) prototype that proves the core novelty (C1 unification, C2 bias impact prediction) works end-to-end, minimizing boilerplate and manual overhead.

## Setup & Scaffolding
1. **Directory Structure**: Create `dia/` (core logic), `app.py` (Streamlit frontend), and `experiments/` (spikes).
2. **Environment**: Install PyTorch (with CUDA support for RTX 3050), torchvision, pandas, scikit-learn, OpenCV, Pillow, Streamlit, and imagehash.

## Milestone 1: C2 Feasibility Spike (Highest Value / Highest Risk)
- **Objective**: Prove we can predict downstream accuracy drop from a dataset defect (class imbalance).
- **Task**: 
  1. Download a tiny subset of CIFAR-10 via torchvision.
  2. Create 3 variants: Balanced, Mild Imbalance (e.g. drop 50% of some classes), Severe Imbalance (e.g. drop 90% of some classes).
  3. Train a lightweight surrogate model (e.g. Simple CNN or ResNet-18 modified for CIFAR) on each variant for 3-5 epochs.
  4. Measure accuracy on a clean, balanced test set.
  5. Log the degradation curve (Accuracy vs. Imbalance Ratio) to ensure a monotone relationship exists.

## Milestone 2: Unified Ingestion & Single-Axis Analyzers
- **Task**: 
  1. Build `ingest.py` to parse a folder-per-class dataset into a Pandas DataFrame.
  2. Build `distribution.py` to compute Imbalance Ratio and entropy.
  3. Build `quality.py` to compute blur (Laplacian variance) and brightness.
  4. Build `duplicates.py` using `imagehash`.

## Milestone 3: C1 Confound Detection & Readiness Score
- **Task**:
  1. Implement Kruskal-Wallis tests across the unified DataFrame to find quality-class confounds.
  2. Implement the 0-100 AI Readiness Score based on the collected metrics.

## Milestone 4: Streamlit Dashboard
- **Task**:
  1. Wire the analyzers into a Streamlit app.
  2. Display the AI Readiness Score, breakdown metrics, and highlight confounds.
  3. Provide a mock or basic recommendation text based on findings.
