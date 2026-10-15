# DIA 2.0 API and local run guide

DIA 2.0 provides an API for image-classification dataset audits. Its first release supports a single operator, ZIP uploads, and datasets of up to 2,000 images. The API is intentionally separate from the future web interface.

## Start locally

Install the dependencies in `requirements-v2.txt`, apply the database migration, and run the API and worker in separate terminals:

```powershell
python -m pip install -r requirements-v2.txt
alembic upgrade head
python -m uvicorn dia.api.main:app --reload
```

In another terminal:

```powershell
python -m dia.worker
```

Open `http://127.0.0.1:8000/docs` for the generated API reference. Local development does not require a password. Set `DIA_SHARED_PASSWORD` to protect local API routes too.

## Dataset layouts

Class-folder ZIP:

```text
images.zip
  train/cat/001.jpg
  train/dog/002.jpg
  test/cat/003.jpg
```

Or put images alongside `manifest.csv` or `manifest.jsonl`. Every manifest row needs `image_path`; `label` and `split` are optional. Every other column is treated as supplied sample metadata.

```csv
image_path,label,split,age_group,region
images/001.jpg,cat,train,adult,north
images/002.jpg,dog,test,unknown,south
```

Supported image extensions are JPEG, PNG, WebP, BMP, and TIFF. ZIP paths must be relative and cannot contain parent-directory traversal. Limits are configurable with `DIA_MAX_UPLOAD_MB`, `DIA_MAX_EXTRACTED_MB`, `DIA_MAX_IMAGE_MB`, and `DIA_MAX_SAMPLES`.

## Run an audit

Upload the ZIP:

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/datasets -F "file=@images.zip"
```

Start an audit with optional target proportions. Targets are proportions from 0 through 1 and must sum to 1 for each attribute. Omitting targets produces descriptive group summaries without an unfairness verdict.

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/datasets/DATASET_ID/runs `
  -H "Content-Type: application/json" `
  -d '{"fairness_targets":{"age_group":{"adult":0.5,"older":0.5}},"class_fairness_targets":{"cat":{"age_group":{"adult":0.6,"older":0.4}}},"metadata_schema":{"age":{"type":"integer"},"region":{"type":"category","allowed_values":["north","south"]}},"estimate_attributes":true}'
```

Poll `GET /v1/runs/{run_id}` until its status is `completed`, `failed`, or `cancelled`. Retrieve `GET /v1/runs/{run_id}/report` for the JSON audit and `GET /v1/runs/{run_id}/samples` for flagged image references. Download per-sample CSV with `GET /v1/runs/{run_id}/samples.csv`; compare two completed runs with `GET /v1/runs/{run_id}/compare/{other_run_id}`. Submit a hypothetical rescore to `POST /v1/runs/{run_id}/what-if` with `{"changes":{"defect_rate_pct":0}}`; it is non-persistent and cannot invent a dimension absent from the baseline report. Cancel queued or running work with `POST /v1/runs/{run_id}/cancel`. Delete a dataset and its runs/files with `DELETE /v1/datasets/{dataset_id}`.

Run requests also accept `sampling_rate` (default `1.0`, range `(0, 1]`) and `sampling_seed` (default `42`). Sampling is deterministic and stratified by class and split; minimum one sample per stratum may make the actual rate exceed a very small requested rate. The report includes requested and actual rates, seed, and dataset fingerprint.

When `DIA_SHARED_PASSWORD` is set, send it in `X-DIA-Password` for protected routes. Production mode refuses protected operations if no shared password is configured. `/health` remains available for deployment health checks.

## Persistence and limits

SQLite is the local default. Set `DIA_DATABASE_URL` for PostgreSQL or another SQLAlchemy-supported database. Set `DIA_STORAGE_DIR` to a persistent writable volume on a hosted deployment. Dataset images, ZIP uploads, and embedding artifacts live there; database rows contain references and audit results. Run the worker as a separate process against the same database and storage volume.

The image-derived embedding checks use pretrained ResNet-18 weights. If those weights cannot be loaded, the remaining analyses still run and embedding-dependent results are marked unavailable. The accuracy-impact predictor is also reported as unavailable until a validated model is included. Label disagreements are review suggestions, never confirmed label errors.

Attribute suggestions are opt-in and trained from the metadata already supplied in the same dataset, using held-out image embeddings. They may repeat patterns or errors in that metadata; suggestions never replace user values and must be reviewed. An attribute needs at least three labeled samples per value before the suggestion model runs.

The readiness score reports its measured dimensions, coverage, weights, formula, and any hard-gate reason. The numeric score is not capped; a measured sub-score below 30 or a cross-split duplicate group forces a `Not Ready` verdict. Missing dimensions do not contribute weight. Fairness gaps are only compared with targets supplied by the operator; without targets, the report is descriptive. Split skew and group associations are signals for review, not causal findings.

The current release does not include a validated face detector or demographic attribute classifier, BRISQUE model, full confident-learning implementation, or validated accuracy-impact predictor. Such values are reported as limited/unavailable rather than filled with zero. Near-duplicate image candidates use perceptual hashes and, when ResNet embeddings are available, cosine confirmation at 0.98. See [SRS_TRACEABILITY.md](SRS_TRACEABILITY.md) for remaining requirements and continuation boundaries.

## Docker deployment

Copy `.env.example` to `.env` and set long random values for both secrets. Then run:

```powershell
docker compose up --build
```

The API is served on port 8000. Compose keeps PostgreSQL data and DIA files in named persistent volumes. Protect the public endpoint with HTTPS at the hosting platform or reverse proxy, and back up both volumes together.
