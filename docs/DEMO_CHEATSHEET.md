# DIA Demo 5-Minute Cheatsheet

### 1. Setup (Run Before Demo)
```bash
python scripts/download_demo_dataset.py
python run.py
```

### 2. The Pitch (15 seconds)
"DIA is an automated dataset health auditor. Instead of running 6 different disconnected tools, DIA unifies fairness, quality, and balance into a single sample-level view to catch hidden structural defects before you waste money on training."

### 3. The Execution (30 seconds)
- Point to `data/demo_dataset` in the sidebar.
- Click **Run Full Analysis**.
- "DIA is now extracting deep features, hashing images, and looking for confounds."

### 4. The Reveal (2 minutes)
- **Score (49/100)**: "The dataset failed the AI Readiness check."
- **Bias Predictor**: "Our C2 impact predictor estimates an 18% drop in final accuracy if we train on this as-is."
- **Cross-Dimensional Confound**: "Here is the key novelty. DIA noticed that 'birds' are universally blurrier than 'airplanes'. The model won't learn what a bird looks like; it will learn what a blurry photo looks like."

### 5. The Fix (1 minute)
- Click the **Recommendations** section.
- "DIA automatically generated a prioritized punch list: Deduplicate the autos, balance the airplanes, and fix the blurry birds."

### Backup Plan
No internet for the demo script? Point the UI to `test_data/` instead.
