# DIA 2.0 API and Local Run Guide

DIA 2.0 provides an API and batch CLI for image-classification dataset health audits. Its release supports a single operator, ZIP uploads, class-folder or manifest layouts, and datasets of up to 2,000 images per run. The API and core engine are intentionally decoupled from the web interface.

## Start Locally

Install the dependencies in `requirements-v2.txt`, apply database migrations, and run the API and worker in separate terminals:

```powershell
python -m pip install -r requirements-v2.txt
alembic upgrade head
python -m uvicorn dia.api.main:app --reload
```

In another terminal, start the queue worker:

```powershell
python -m dia.worker
```

Open `http://127.0.0.1:8000/docs` for the interactive OpenAPI/Swagger specification. Set `DIA_SHARED_PASSWORD` to protect API routes with shared-password authentication.

## Headless / Batch CLI

Run audits directly from the terminal without starting the web server (REQ-UI-10, OR-8):

```powershell
python -m dia analyze --path ./my_dataset.zip `
  --out ./reports/report.json `
  --html ./reports/report.html `
  --datasheet ./reports/datasheet.md `
  --manifest ./reports/remediation_manifest.csv `
  --predict-impact
```

## Dataset Layouts

### 1. Class-folder ZIP
```text
images.zip
  train/cat/001.jpg
  train/dog/002.jpg
  test/cat/003.jpg
```

### 2. Manifest-based ZIP (CSV or JSONL)
Put images alongside `manifest.csv` or `manifest.jsonl`. Every manifest row requires `image_path`; `label` and `split` are optional. All other columns are treated as supplied sample metadata:

```csv
image_path,label,split,age_group,region
images/001.jpg,cat,train,adult,north
images/002.jpg,dog,test,unknown,south
```

Supported image extensions: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`. ZIP paths must be relative and cannot contain parent-directory traversal (`..`).

## Run an Audit via API

### 1. Upload Dataset ZIP
```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/datasets -F "file=@images.zip"
```

### 2. Queue an Analysis Run
Start an audit with optional fairness targets, metadata schemas, and validated impact prediction:

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/datasets/DATASET_ID/runs `
  -H "Content-Type: application/json" `
  -d '{
    "fairness_targets": {"age_group": {"adult": 0.5, "older": 0.5}},
    "class_fairness_targets": {"cat": {"age_group": {"adult": 0.6, "older": 0.4}}},
    "metadata_schema": {"age": {"type": "integer"}, "region": {"type": "category", "allowed_values": ["north", "south"]}},
    "estimate_attributes": true,
    "predict_impact": true,
    "sampling_rate": 1.0,
    "sampling_seed": 42
  }'
```

### 3. Monitor Status & Retrieve Deliverables
Poll `GET /v1/runs/{run_id}` until `status` is `completed`:

- **Complete Audit JSON**: `GET /v1/runs/{run_id}/report`
- **Standalone HTML Report** (zero external dependencies): `GET /v1/runs/{run_id}/report.html`
- **Model Card / Datasheet JSON** (Gebru et al. format): `GET /v1/runs/{run_id}/model-card.json`
- **Model Card / Datasheet Markdown**: `GET /v1/runs/{run_id}/model-card.md`
- **Actionable Remediation Manifest CSV**: `GET /v1/runs/{run_id}/remediation-manifest.csv`
- **Actionable Remediation Manifest JSON**: `GET /v1/runs/{run_id}/remediation-manifest.json`
- **Per-Sample Metrics CSV**: `GET /v1/runs/{run_id}/samples.csv`
- **Flagged Samples Inspection**: `GET /v1/runs/{run_id}/samples?limit=100`
- **Run Comparison**: `GET /v1/runs/{run_id}/compare/{other_run_id}`
- **Non-Persistent What-If Rescore**: `POST /v1/runs/{run_id}/what-if` with `{"changes": {"defect_rate_pct": 0}}`
- **Cancel Run**: `POST /v1/runs/{run_id}/cancel`
- **Delete Dataset**: `DELETE /v1/datasets/{dataset_id}`

## Core Features & Methodology

- **Confident Learning & Outlier Detection**: Stratified out-of-fold logistic regression estimates class-specific self-confidence thresholds $t_j$ and joint noise matrices to identify mislabeled samples with confidence margins. Isolation Forest computes embedding outlier scores per sample.
- **Cross-Dimensional Confounds (C1)**: Evaluates interactions across quality, class, representation, diversity, and leakage with Benjamini-Hochberg FDR correction ($\alpha = 0.05$) and Kruskal $\epsilon^2$ effect sizes.
- **Bias Impact Predictor (C2)**: Assembles a 16-D bias descriptor vector to estimate downstream model accuracy degradation ($\Delta \text{acc}$) and sub-group performance gap ($\Delta \text{gap}$) with prediction intervals and feature attributions, validated via empirical synthetic perturbation benchmark studies ($R^2 \approx 0.89$).
- **AI Readiness Scoring**: Weighted combination of six auditable dimensions with confound penalties and hard gates (cross-split leakage or sub-score $< 30$ caps readiness at 49 and forces `Not Ready`).
- **Remediation Manifests**: Translates defects into ranked recommendations prioritized by gain per unit effort, with top-3 "Do these first" badges, confound-aware suppression of naive oversampling, and sample-level action instructions.
- **Derived-Result Caching**: Fast re-runs on unchanged datasets load cached embeddings without re-running neural network inference.

## Docker Deployment

Copy `.env.example` to `.env` and set random secrets:

```powershell
docker compose up --build
```
