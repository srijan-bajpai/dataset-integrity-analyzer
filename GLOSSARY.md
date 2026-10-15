# DIA Domain Glossary (`GLOSSARY.md`)

This ubiquitous vocabulary establishes the shared mental model for Dataset Integrity Analyzer (DIA) across both human engineers and AI coding agents, following the `domain-modeling` discipline from [mattpocock/skills](https://github.com/mattpocock/skills).

---

## 1. Core Health & Scoring Concepts

### AI Readiness Score
A unified scalar metric from **0 to 100** evaluating whether a dataset is suitable for training a machine learning model.
- **Formula**: Dynamically redistributes weights across assessed dimensions based on sample coverage.
- **Verdict Scale**:
  - `Production Ready` ($\ge 85$)
  - `Acceptable` ($70 - 84$)
  - `Needs Remediation` ($50 - 69$)
  - `Critical / Not Usable` ($< 50$)
  - `Not Ready` (Hard-gate override triggered)
  - `Insufficient Coverage` (Fewer than required dimensions measured)

### Hard Gate
A critical failure threshold that immediately overrides the numerical score and forces the verdict to `Not Ready`.
- **Triggers**:
  1. Cross-split duplicate leakage ($\ge 1$ duplicate between train and test/val splits).
  2. Severe label noise ($\ge 25\%$ estimated corrupted labels).
  3. Extreme dimension collapse (any core dimension score $< 20$).

### 6 Audit Dimensions (Reconciled C1 Scale)
1. **Balance**: Class distribution parity, measured via Imbalance Ratio (IR), Shannon Entropy ($H$), and Gini coefficient.
2. **Fairness**: Demographic representation gaps against user-supplied target distributions (Worst Absolute Target Gap).
3. **Quality**: Visual signal fidelity (Laplacian blur variance, Lab brightness/contrast, noise Median Absolute Deviation).
4. **Uniqueness**: Exact and near-duplicate detection via perceptual hashing (pHash) and cosine embedding similarity ($\ge 0.98$).
5. **Diversity**: Semantic feature space coverage, measured by embedding cluster entropy and Isolation Forest outlier rates.
6. **Label Integrity**: Out-of-fold label correctness, estimated via Confident Learning joint noise matrices and per-class reliability scores.

---

## 2. Advanced Diagnostic Concepts

### Cross-Dimensional Confounds ($C_1$)
Bivariate statistical interactions where a defect in one dimension correlates with another dimension, creating deceptive shortcuts for ML models.
- **Examples**:
  - `Quality × Class`: One class is systematically blurrier or darker than others.
  - `Quality × Attribute`: Demographic subgroups suffer worse image resolution.
  - `Redundancy × Class`: Over-representation of identical images in specific classes.
  - `Label Noise × Class`: Disproportionate annotation errors in rare categories.
  - `Leakage × Split`: Identical samples spanning train and validation splits.
- **Statistical Rigor**: Evaluated using Kruskal-Wallis effect sizes ($\epsilon^2$) and Benjamini-Hochberg False Discovery Rate ($q < 0.05$) correction.

### Bias Impact Predictor ($C_2$)
An empirical prediction system utilizing a 16-D bias descriptor vector to forecast the downstream classification accuracy degradation ($\Delta \text{Acc}$) on held-out test data without running a full training loop.

### What-If Rescoring
An interactive simulation capability (`POST /v1/runs/{id}/what-if`) allowing engineers to hypothesize metric interventions (e.g. reducing noise from $14\% \to 2\%$) and instantly project readiness gains without modifying stored datasets.

### Remediation Manifest
A machine-actionable, per-sample list of prescribed corrective actions:
- `REMOVE_DUPLICATE`: Purge perceptual or exact copies.
- `RELABEL_SAMPLE`: Fix annotations flagged by Confident Learning.
- `INSPECT_DEFECT`: Review severe blur, exposure, or corrupt files.
- `BALANCE_MINORITY`: Targeted oversampling or acquisition prompt.

---

## 3. Frontend & UX Paradigms

### Dual-Audience Lens
- **Stakeholder Mode (ELI5)**: Non-technical executive view translating statistical jargon into plain-language analogies and traffic-light indicators.
- **Engineer Mode (Deep Dive)**: High-density telemetry showing raw distributions, confusion matrices, p-values, and per-sample file hashes.

### The 5 Core UI States
Every component strictly conforms to Matt Pocock's state-resilience protocol:
1. `Ideal`: Complete data loaded and rendered cleanly.
2. `Loading`: Geometric pulse skeletons (`animate-pulse`) preventing layout shifts.
3. `Empty`: Informative iconography, helpful copy, and a direct Call-To-Action (CTA).
4. `Error`: Actionable error message with an inline `[Retry]` trigger.
5. `Partial`: Handling missing optional metadata, truncated strings, or unassessed dimensions.
