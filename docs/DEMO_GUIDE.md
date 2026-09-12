# Dataset Integrity Analyzer - Demo Guide

This guide explains how to present the DIA prototype from scratch in 5 minutes.

## 1. Installation & Environment setup
Ensure you have cloned the repository and have Python 3.10+ (and ideally an NVIDIA GPU, though CPU fallback works).
```bash
pip install -r requirements.txt
```

## 2. Generating the Demo Dataset
We have built a script to dynamically download a subset of CIFAR-10 and inject deliberate structural defects (imbalance, duplicates, and a cross-dimensional quality confound).

Run the generator:
```bash
python scripts/download_demo_dataset.py
```
*Expected Output: A folder `data/demo_dataset` containing ~300 images across `airplane`, `automobile`, and `bird`. The `bird` class is deliberately blurred.*

## 3. Starting the Application
Start the Streamlit dashboard:
```bash
python run.py
```
This will open `http://localhost:8501` in your browser.

## 4. Running the Analysis
1. In the sidebar, ensure the dataset path is set to `data/demo_dataset`.
2. Click **Run Full Analysis**.
3. Point out the spinner to the audience: *“DIA is now dynamically extracting embeddings, computing quality metrics, hashing for duplicates, and looking for label anomalies.”*

## 5. Interpreting the Score
Once complete, direct attention to the top of the dashboard.
- **The Score**: Should be ~49 (Needs Remediation) because of the injected defects triggering the hard-gate rule.
- **The Radar Chart**: Shows the specific breakdown. Notice how Quality, Uniqueness, and Balance are dragged down.

## 6. Demonstrating the ML Impact Predictor
Scroll to **Bias Impact Predictor (C2)**.
- **What to say**: *“Standard tools just tell you 'class 2 is imbalanced'. DIA translates that into actionable business risk. Using a surrogate model calibrated via our C2 feasibility spikes, DIA predicts that training a model on this specific broken dataset will drop test accuracy by ~18% compared to a healthy baseline.”*

## 7. Demonstrating Cross-Dimensional Findings
Scroll to **Cross-Dimensional Confounds**.
- **What to say**: *“This is DIA’s core novelty. By analyzing all dimensions over a shared sample representation, DIA caught a structural confound: The `bird` class is fundamentally blurrier than the other classes. If you just tracked 'average dataset blur', you'd miss that the model will likely learn to associate blurriness with birds.”*
- You should see a red alert: **Quality-Class Confound: Image quality_blur varies significantly across classes.**

## 8. Drilling Down & Recommendations
Scroll through the tabs to show the specific charts:
- **Balance Tab**: Shows the 200 vs 50 vs 50 imbalance.
- **Quality Tab**: Shows the box plot where `bird` blur variance is entirely disjoint from the others.
- **Recommendations**: Read the generated recommendations. *“DIA doesn’t just complain; it generates a prioritized punch list for the MLOps engineer.”*

## Backup Datasets
If internet access fails during the demo, use the fallback synthetic dataset created by the automated tests in `test_data/`. Change the UI path to `test_data/`.
