# DIA 2.0 Demo Cheatsheet

1. Start the API and worker from [API_GUIDE.md](API_GUIDE.md).
2. Upload a two-class image ZIP to `POST /v1/datasets`.
3. Create an audit with `POST /v1/datasets/{dataset_id}/runs`; optionally pass metadata validation rules, fairness targets, and a sampling rate.
4. Poll `GET /v1/runs/{run_id}`. When complete, inspect `GET /v1/runs/{run_id}/report` and export per-image results from `GET /v1/runs/{run_id}/samples.csv`.
5. Explain coverage and uncertainty before interpreting the readiness score. Treat all image-derived or model-based findings as review signals.

Do not quote the older demo's fixed accuracy-drop estimate or fixed score. The impact predictor stays unavailable until controlled, held-out validation supports a quantitative estimate.
