# Dataset Integrity Analyzer (DIA)

DIA is a database-backed service for auditing image-classification datasets before model training. It accepts ZIP uploads containing class folders or a CSV/JSONL manifest, stores reproducible analysis runs, and returns machine-readable findings with sample-level evidence. Fairness results are review signals, not proof that a dataset or model is fair.

The v2 backend is the active work on branch `dia_2.0_codex`. The Streamlit app remains a legacy local demo surface; frontend work will follow after the API contract stabilizes.

## What it measures

- Class balance and supplied metadata completeness/schema issues.
- Group representation, optional operator-provided targets, confidence intervals, class associations, intersectional support, and split skew.
- Image blur, Lab brightness and contrast, noise estimate, resolution, aspect ratio, file size, and basic image anomalies.
- Exact and perceptual duplicates, with embedding confirmation when pretrained features are available; reports cross-split leakage and conflicting labels.
- ResNet-based visual diversity and cross-validated label-disagreement review signals when the model weights are available.
- Versioned readiness scoring with dimension coverage, recommendations, provenance, run comparison, CSV export, and cancellation.

The API deliberately reports dedicated face-demographic inference, BRISQUE, and accuracy-impact prediction as unavailable until those models pass documented validation. Opt-in attribute suggestions learn only from metadata already supplied in the dataset, remain separate from user values, and require review. See [SRS traceability and remaining work](docs/SRS_TRACEABILITY.md).

## Run locally

Use Python 3.12. In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-v2.txt
python -m alembic upgrade head
```

Start the API and worker in separate terminals:

```powershell
python -m uvicorn dia.api.main:app --reload
python -m dia.worker
```

The API is available at `http://127.0.0.1:8000`; interactive endpoint docs are at `/docs`. See the [API guide](docs/API_GUIDE.md) for upload formats, options, authentication, report fields, deletion, and deployment.

## Deploy with Docker Compose

Copy `.env.example` to `.env`, set `POSTGRES_PASSWORD` and `DIA_SHARED_PASSWORD`, then run:

```powershell
docker compose up --build
```

Compose uses PostgreSQL and persistent named volumes for the database and uploaded data. The published API port binds to localhost by default. Place an HTTPS reverse proxy in front of any externally reachable deployment.

## Verify

```powershell
python -m pytest -q
python -m alembic upgrade head
```

The current acceptance tests exercise ingestion safety, metadata and fairness summaries, image metrics, duplicate grouping, readiness gates, API authentication, run persistence, cancellation, report export, and dataset deletion. Docker smoke tests require a Docker-capable host.

## Dataset handling

ZIP uploads and extracted images stay in the configured `DIA_STORAGE_DIR` until the dataset is explicitly deleted. The service does not modify the user's source files. Production mode requires `DIA_SHARED_PASSWORD`; set `DIA_DATABASE_URL` and `DIA_STORAGE_DIR` for deployment storage. Upload and extraction size limits, per-image limits, and the sample cap are configurable with environment variables documented in `.env.example`.
