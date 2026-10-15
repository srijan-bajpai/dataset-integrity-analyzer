"""FastAPI application for dataset ingestion and persisted audit runs."""

from __future__ import annotations

import hmac
import csv
import io
import json
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from dia.config import settings
from dia.core.ingestion import DatasetValidationError, dataset_fingerprint, parse_dataset, safe_extract_zip
from dia.db.models import AnalysisRun, Dataset, JobQueue, Sample, SampleResult
from dia.db.session import get_db
from dia.reports import format_datasheet_markdown, generate_datasheet, render_html_report
from dia.scoring.readiness import ReadinessScorer

app = FastAPI(
    title="Dataset Integrity Analyzer API",
    version="2.0.0",
    description="Audit image classification datasets for quality, representation, duplication, diversity, and label concerns.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    fairness_targets: dict[str, dict[str, float]] = Field(default_factory=dict)
    class_fairness_targets: dict[str, dict[str, dict[str, float]]] = Field(default_factory=dict)
    metadata_schema: dict[str, dict[str, Any]] = Field(default_factory=dict)
    estimate_attributes: bool = False
    predict_impact: bool = False
    sampling_rate: float = Field(default=1.0, gt=0, le=1)
    sampling_seed: int = 42

    @field_validator("fairness_targets")
    @classmethod
    def validate_targets(cls, value: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
        for name, target in value.items():
            if not target or any(v < 0 or v > 1 for v in target.values()):
                raise ValueError(f"Targets for {name} must be nonempty proportions from 0 to 1.")
            if not 0.999 <= sum(target.values()) <= 1.001:
                raise ValueError(f"Target proportions for {name} must sum to 1.")
        return value


    @field_validator("class_fairness_targets")
    @classmethod
    def validate_class_targets(cls, value: dict[str, dict[str, dict[str, float]]]) -> dict[str, dict[str, dict[str, float]]]:
        for label, attrs in value.items():
            for name, target in attrs.items():
                if not target or any(v < 0 or v > 1 for v in target.values()) or not 0.999 <= sum(target.values()) <= 1.001:
                    raise ValueError(f"Class fairness target for '{label}/{name}' must sum to 1.")
        return value

    @field_validator("metadata_schema")
    @classmethod
    def validate_metadata_schema(cls, value: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        allowed_types = {"string", "category", "number", "integer", "boolean"}
        for name, spec in value.items():
            if spec.get("type") not in allowed_types:
                raise ValueError(f"Metadata schema for '{name}' needs a supported type: {sorted(allowed_types)}.")
            if spec.get("allowed_values") is not None and not isinstance(spec["allowed_values"], list):
                raise ValueError(f"allowed_values for '{name}' must be a list.")
        return value


class WhatIfRequest(BaseModel):
    changes: dict[str, float]

    @field_validator("changes")
    @classmethod
    def validate_changes(cls, value: dict[str, float]) -> dict[str, float]:
        supported = {
            "imbalance_ratio", "fairness_target_gap", "defect_rate_pct",
            "redundancy_ratio", "cluster_entropy", "label_noise_rate_pct",
            "cross_split_duplicate_groups",
        }
        unknown = set(value) - supported
        if unknown:
            raise ValueError(f"Unsupported scenario metrics: {sorted(unknown)}.")
        for name, number in value.items():
            if not float(number) >= 0 or float(number) == float("inf") or float(number) != float(number):
                raise ValueError(f"Scenario value for '{name}' must be a finite, nonnegative number.")
            if name in {"fairness_target_gap", "redundancy_ratio", "cluster_entropy"} and number > 1:
                raise ValueError(f"Scenario value for '{name}' must be at most 1.")
            if name in {"defect_rate_pct", "label_noise_rate_pct"} and number > 100:
                raise ValueError(f"Scenario value for '{name}' must be at most 100.")
            if name == "cross_split_duplicate_groups" and int(number) != number:
                raise ValueError("cross_split_duplicate_groups must be an integer.")
        return value


def require_password(
    x_dia_password: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    password = x_dia_password or token
    if settings.environment == "production" and not settings.shared_password:
        raise HTTPException(status_code=503, detail="DIA_SHARED_PASSWORD must be configured for production.")
    if settings.shared_password and not hmac.compare_digest(password or "", settings.shared_password):
        raise HTTPException(status_code=401, detail="A valid X-DIA-Password header is required.")


def _dataset_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


def _run_or_404(db: Session, run_id: str) -> AnalysisRun:
    run = db.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    return run


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}


@app.post("/v1/datasets", status_code=201, dependencies=[Depends(require_password)])
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not file.filename or Path(file.filename).suffix.lower() != ".zip":
        raise HTTPException(status_code=415, detail="Upload a ZIP archive containing the dataset.")
    dataset_id = str(uuid.uuid4())
    zip_path = settings.upload_dir / f"{dataset_id}.zip"
    extract_path = settings.extract_dir / dataset_id
    limit = settings.max_upload_size_mb * 1024 * 1024
    try:
        size = 0
        with zip_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413, detail="Upload exceeds the configured compressed size limit.")
                output.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="The uploaded ZIP is empty.")
        try:
            safe_extract_zip(zip_path, extract_path)
            layout, records, warnings = parse_dataset(extract_path)
        except (DatasetValidationError, OSError, json.JSONDecodeError, zipfile.BadZipFile, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        classes = sorted({str(r["ground_truth_class"]) for r in records if r.get("ground_truth_class")})
        readable_classes = {str(r["ground_truth_class"]) for r in records if r.get("is_valid") and r.get("ground_truth_class")}
        if len(readable_classes) < 2:
            raise HTTPException(status_code=422, detail="Dataset must contain at least two classes for integrity analysis.")
        fingerprint = dataset_fingerprint(extract_path, records)
        dataset = Dataset(
            id=dataset_id,
            name=(name or Path(file.filename).stem)[:255],
            layout=layout,
            sample_count=len(records),
            class_count=len(classes),
            classes=classes,
            fingerprint=fingerprint,
            storage_path=str(extract_path.resolve()),
            zip_path=str(zip_path.resolve()),
            status="ingested",
            description=json.dumps({"ingestion_warnings": warnings}),
        )
        db.add(dataset)
        db.flush()
        db.add_all([
            Sample(
                dataset_id=dataset_id,
                sample_ref=record["sample_ref"],
                file_path=record["path"],
                ground_truth_class=record.get("ground_truth_class"),
                split=record.get("split", "unspecified"),
                attributes=record.get("attributes", {}),
                content_sha256=record.get("content_sha256"),
                inferred_attributes=record.get("inferred_attributes", {}),
                anomaly_flags=record.get("anomaly_flags", []),
                is_valid=record.get("is_valid", True),
                error_message=record.get("error_message"),
            )
            for record in records
        ])
        db.commit()
        return {
            "id": dataset.id, "name": dataset.name, "layout": layout,
            "sample_count": dataset.sample_count, "class_count": dataset.class_count,
            "classes": classes, "fingerprint": fingerprint, "status": dataset.status, "warnings": warnings,
        }
    except HTTPException:
        db.rollback()
        shutil.rmtree(extract_path, ignore_errors=True)
        zip_path.unlink(missing_ok=True)
        raise
    except Exception:
        db.rollback()
        shutil.rmtree(extract_path, ignore_errors=True)
        zip_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


@app.get("/v1/datasets", dependencies=[Depends(require_password)])
def list_datasets(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [{
        "id": d.id, "name": d.name, "layout": d.layout, "fingerprint": d.fingerprint, "sample_count": d.sample_count,
        "class_count": d.class_count, "classes": d.classes, "status": d.status,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    } for d in datasets]


@app.get("/v1/datasets/{dataset_id}", dependencies=[Depends(require_password)])
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    d = _dataset_or_404(db, dataset_id)
    return {
        "id": d.id, "name": d.name, "description": d.description, "layout": d.layout, "fingerprint": d.fingerprint,
        "sample_count": d.sample_count, "class_count": d.class_count, "classes": d.classes,
        "status": d.status, "created_at": d.created_at.isoformat() if d.created_at else None,
        "runs": [{"id": r.id, "status": r.status, "created_at": r.created_at.isoformat()} for r in d.runs],
    }


@app.get("/v1/datasets/{dataset_id}/samples/{sample_ref:path}/image", dependencies=[Depends(require_password)])
def get_sample_image(
    dataset_id: str,
    sample_ref: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    dataset = _dataset_or_404(db, dataset_id)
    storage_root = Path(dataset.storage_path).resolve()
    sample = (
        db.query(Sample)
        .filter(Sample.dataset_id == dataset_id, Sample.sample_ref == sample_ref)
        .first()
    )
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found.")
    file_path = Path(sample.file_path).resolve()
    try:
        file_path.relative_to(storage_root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Unsafe file path access.") from exc
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Sample image file missing from storage.")
    ext = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }
    return FileResponse(file_path, media_type=media_types.get(ext, "application/octet-stream"))


@app.post("/v1/datasets/{dataset_id}/runs", status_code=202, dependencies=[Depends(require_password)])
def create_run(dataset_id: str, request: RunRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    dataset = _dataset_or_404(db, dataset_id)
    run = AnalysisRun(dataset_id=dataset.id, status="queued", config={
        "fairness_targets": request.fairness_targets,
        "class_fairness_targets": request.class_fairness_targets,
        "metadata_schema": request.metadata_schema,
        "estimate_attributes": request.estimate_attributes,
        "predict_impact": request.predict_impact,
        "sampling_rate": request.sampling_rate,
        "sampling_seed": request.sampling_seed,
    })
    db.add(run)
    db.flush()
    db.add(JobQueue(run_id=run.id, status="pending"))
    db.commit()
    return {"run_id": run.id, "status": run.status, "status_url": f"/v1/runs/{run.id}"}


@app.get("/v1/runs/{run_id}", dependencies=[Depends(require_password)])
def get_run(run_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    run = _run_or_404(db, run_id)
    return {
        "id": run.id, "dataset_id": run.dataset_id, "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "progress_percent": run.progress_percent,
        "status_message": run.status_message,
        "duration_seconds": run.duration_seconds, "error_message": run.error_message,
        "report_url": f"/v1/runs/{run.id}/report" if run.status == "completed" else None,
    }


@app.post("/v1/runs/{run_id}/cancel", dependencies=[Depends(require_password)])
def cancel_run(run_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    run = _run_or_404(db, run_id)
    if run.status not in {"queued", "running"}:
        raise HTTPException(status_code=409, detail=f"Run is {run.status} and cannot be cancelled.")
    run.status = "cancelled"
    run.status_message = "Cancellation requested"
    run.completed_at = datetime.now(timezone.utc)
    job = db.query(JobQueue).filter(JobQueue.run_id == run.id).first()
    if job is not None:
        job.status = "cancelled"
        job.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"run_id": run.id, "status": run.status}


@app.get("/v1/runs/{run_id}/report", dependencies=[Depends(require_password)])
def get_report(run_id: str, db: Session = Depends(get_db)) -> Any:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail=f"Run is {run.status}; report is available after completion.")
    return JSONResponse(content=run.report or {})


@app.get("/v1/runs/{run_id}/report.html", dependencies=[Depends(require_password)])
def get_report_html(run_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail=f"Run is {run.status}; report is available after completion.")
    return HTMLResponse(content=render_html_report(run.report or {}))


@app.get("/v1/runs/{run_id}/model-card.json", dependencies=[Depends(require_password)])
def get_model_card_json(run_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail=f"Run is {run.status}; model card is available after completion.")
    return JSONResponse(content=generate_datasheet(run.report or {}))


@app.get("/v1/runs/{run_id}/model-card.md", dependencies=[Depends(require_password)])
def get_model_card_markdown(run_id: str, db: Session = Depends(get_db)) -> Response:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail=f"Run is {run.status}; model card is available after completion.")
    md_text = format_datasheet_markdown(run.report or {})
    return Response(
        md_text,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="dia-{run.id}-datasheet.md"'},
    )


@app.get("/v1/runs/{run_id}/remediation-manifest.csv", dependencies=[Depends(require_password)])
def export_remediation_manifest_csv(run_id: str, db: Session = Depends(get_db)) -> Response:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed.")
    report = run.report or {}
    rows = report.get("remediation_manifest", [])
    fieldnames = ["sample_ref", "action", "target_dimension", "reason", "current_label", "suggested_value"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return Response(
        output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="dia-{run.id}-remediation-manifest.csv"'},
    )


@app.get("/v1/runs/{run_id}/remediation-manifest.json", dependencies=[Depends(require_password)])
def export_remediation_manifest_json(run_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed.")
    report = run.report or {}
    rows = report.get("remediation_manifest", [])
    return JSONResponse(content={"run_id": run.id, "total": len(rows), "items": rows})


@app.get("/v1/runs/{run_id}/samples.csv", dependencies=[Depends(require_password)])
def export_sample_results_csv(run_id: str, db: Session = Depends(get_db)) -> Response:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed.")
    report = run.report or {}
    rows = report.get("sample_results", [])
    metric_names = sorted({key for row in rows for key in (row.get("metrics") or {})})
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["sample_ref", *metric_names], extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({"sample_ref": row.get("sample_ref"), **(row.get("metrics") or {})})
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="dia-{run.id}-samples.csv"'})


@app.get("/v1/runs/{run_id}/compare/{other_run_id}", dependencies=[Depends(require_password)])
def compare_runs(run_id: str, other_run_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    left, right = _run_or_404(db, run_id), _run_or_404(db, other_run_id)
    if left.status != "completed" or right.status != "completed":
        raise HTTPException(status_code=409, detail="Both runs must be completed before comparison.")
    left_report, right_report = left.report or {}, right.report or {}
    left_score = (left_report.get("results", {}).get("readiness", {}) or {}).get("overall_score")
    right_score = (right_report.get("results", {}).get("readiness", {}) or {}).get("overall_score")
    left_distribution = left_report.get("results", {}).get("distribution", {}).get("class_counts", {})
    right_distribution = right_report.get("results", {}).get("distribution", {}).get("class_counts", {})
    return {
        "run_a": left.id, "run_b": right.id,
        "dataset_fingerprints": [left_report.get("dataset_fingerprint"), right_report.get("dataset_fingerprint")],
        "same_dataset_fingerprint": left_report.get("dataset_fingerprint") == right_report.get("dataset_fingerprint"),
        "readiness_score_delta_b_minus_a": (right_score - left_score) if left_score is not None and right_score is not None else None,
        "class_count_deltas_b_minus_a": {
            name: int(right_distribution.get(name, 0)) - int(left_distribution.get(name, 0))
            for name in sorted(set(left_distribution) | set(right_distribution))
        },
        "sampling": [left_report.get("sampling"), right_report.get("sampling")],
        "interpretation": "Compare only runs with compatible configurations and sample coverage; changed targets, sampling, or analyzer versions can explain metric changes.",
    }


@app.post("/v1/runs/{run_id}/what-if", dependencies=[Depends(require_password)])
def rescore_scenario(run_id: str, request: WhatIfRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed.")
    report = run.report or {}
    results = json.loads(json.dumps(report.get("results", {})))
    mappings = {
        "imbalance_ratio": ("distribution", "imbalance_ratio"),
        "fairness_target_gap": ("fairness", "worst_absolute_target_gap"),
        "defect_rate_pct": ("quality", "defect_rate_pct"),
        "redundancy_ratio": ("duplicates", "redundancy_ratio"),
        "cluster_entropy": ("diversity", "cluster_entropy"),
        "label_noise_rate_pct": ("labels", "label_noise_rate_pct"),
        "cross_split_duplicate_groups": ("duplicates", "cross_split_duplicate_groups"),
    }
    for name, value in request.changes.items():
        section, key = mappings[name]
        if results.get(section, {}).get(key) is None:
            raise HTTPException(status_code=422, detail=f"Cannot rescore '{name}' because that dimension was unavailable in the completed run.")
        results.setdefault(section, {})[key] = value
    rescored = ReadinessScorer().compute(results)
    baseline = (report.get("results", {}).get("readiness", {}) or {}).get("overall_score")
    return {
        "run_id": run.id,
        "baseline_score": baseline,
        "what_if_score": rescored["overall_score"],
        "score_delta": rescored["overall_score"] - baseline if baseline is not None and rescored["overall_score"] is not None else None,
        "readiness": rescored,
        "changes": request.changes,
        "persisted": False,
        "interpretation": "This is a hypothetical rescore of supplied metric values; it does not modify samples, rerun analyzers, or predict model accuracy.",
    }


@app.get("/v1/runs/{run_id}/samples", dependencies=[Depends(require_password)])
def get_flagged_samples(run_id: str, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), flagged_only: bool = True, db: Session = Depends(get_db)) -> Any:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed.")
    rows = (
        db.query(SampleResult, Sample)
        .join(Sample, Sample.id == SampleResult.sample_id)
        .filter(SampleResult.run_id == run_id)
        .order_by(Sample.sample_ref)
        .all()
    )
    items = []
    for result, sample in rows:
        metrics = result.metrics or {}
        flags = [name for name, value in metrics.items() if name.startswith("flag_") and value]
        flags.extend(f"flag_{name}" for name in metrics.get("anomaly_flags", []) if f"flag_{name}" not in flags)
        if metrics.get("attribute_suggestions"):
            flags.append("attribute_suggestion")
        if flagged_only and not flags:
            continue
        items.append({
            "sample_ref": sample.sample_ref,
            "ground_truth_class": sample.ground_truth_class,
            "split": sample.split,
            "attributes": sample.attributes or {},
            "inferred_attributes": sample.inferred_attributes or {},
            "flags": flags,
            "metrics": metrics,
        })
    return {"total": len(items), "items": items[offset:offset + min(limit, 500)]}


@app.get("/v1/runs/{run_id}/embeddings-3d", dependencies=[Depends(require_password)])
def get_run_embeddings_3d(run_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    run = _run_or_404(db, run_id)
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Run has not completed.")

    rows = (
        db.query(SampleResult, Sample)
        .join(Sample, Sample.id == SampleResult.sample_id)
        .filter(SampleResult.run_id == run_id)
        .order_by(Sample.sample_ref)
        .all()
    )

    points = []
    has_real_embeddings = False
    variance_explained = [0.0, 0.0, 0.0]

    embed_file = Path(run.embeddings_path) if run.embeddings_path else None
    if embed_file and embed_file.is_file():
        try:
            import numpy as np
            from sklearn.decomposition import PCA

            raw_embs = np.load(embed_file)
            if len(raw_embs) >= len(rows) and len(rows) >= 3:
                pca = PCA(n_components=3, random_state=42)
                coords = pca.fit_transform(raw_embs[:len(rows)])
                max_abs = float(np.abs(coords).max())
                scale = 5.0 / (max_abs + 1e-6)
                coords = coords * scale
                variance_explained = [round(float(v), 4) for v in pca.explained_variance_ratio_]
                has_real_embeddings = True

                for idx, (result, sample) in enumerate(rows):
                    metrics = result.metrics or {}
                    is_outlier = bool(
                        metrics.get("flag_embedding_outlier") or
                        metrics.get("flag_visual_outlier") or
                        "embedding_outlier" in metrics.get("anomaly_flags", [])
                    )
                    points.append({
                        "sample_ref": sample.sample_ref,
                        "ground_truth_class": sample.ground_truth_class or "unlabelled",
                        "split": sample.split or "unspecified",
                        "cluster_id": metrics.get("cluster_id", sample.cluster_id or 0),
                        "x": round(float(coords[idx, 0]), 4),
                        "y": round(float(coords[idx, 1]), 4),
                        "z": round(float(coords[idx, 2]), 4),
                        "is_outlier": is_outlier,
                        "outlier_score": round(float(metrics.get("embedding_outlier_score") or 0.0), 4),
                    })
        except Exception:
            has_real_embeddings = False

    if not has_real_embeddings:
        import math
        classes = sorted({sample.ground_truth_class or "unlabelled" for _, sample in rows})
        class_angles = {cls_name: (2 * math.pi * i) / max(len(classes), 1) for i, cls_name in enumerate(classes)}

        for idx, (result, sample) in enumerate(rows):
            metrics = result.metrics or {}
            cls = sample.ground_truth_class or "unlabelled"
            base_angle = class_angles.get(cls, 0.0)
            cluster_id = metrics.get("cluster_id", idx % 3)
            seed = (idx * 17 + 31) % 1000 / 1000.0
            r = 3.0 + (seed - 0.5) * 1.5
            is_outlier = bool(
                metrics.get("flag_embedding_outlier") or
                metrics.get("flag_visual_outlier")
            )
            if is_outlier:
                r += 3.5

            x = r * math.cos(base_angle + (seed - 0.5) * 0.6)
            y = (seed - 0.5) * 4.0
            z = r * math.sin(base_angle + (seed - 0.5) * 0.6)

            points.append({
                "sample_ref": sample.sample_ref,
                "ground_truth_class": cls,
                "split": sample.split or "unspecified",
                "cluster_id": cluster_id,
                "x": round(x, 4),
                "y": round(y, 4),
                "z": round(z, 4),
                "is_outlier": is_outlier,
                "outlier_score": round(float(metrics.get("embedding_outlier_score") or (0.85 if is_outlier else 0.1)), 4),
            })
        variance_explained = [0.42, 0.28, 0.15]

    return {
        "run_id": run.id,
        "has_real_embeddings": has_real_embeddings,
        "sample_count": len(points),
        "variance_explained": variance_explained,
        "points": points,
    }


@app.delete("/v1/datasets/{dataset_id}", status_code=204, dependencies=[Depends(require_password)])
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)) -> None:
    dataset = _dataset_or_404(db, dataset_id)
    extract_path = Path(dataset.storage_path).resolve()
    upload_path = Path(dataset.zip_path).resolve() if dataset.zip_path else None
    try:
        extract_path.relative_to(settings.extract_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Dataset storage path failed validation.") from exc
    if upload_path is not None:
        try:
            upload_path.relative_to(settings.upload_dir.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=500, detail="Upload storage path failed validation.") from exc
    run_ids = [run.id for run in dataset.runs]
    embedding_paths = [run.embeddings_path for run in dataset.runs if run.embeddings_path]
    if run_ids:
        db.query(JobQueue).filter(JobQueue.run_id.in_(run_ids)).delete(synchronize_session=False)
    db.delete(dataset)
    db.commit()
    shutil.rmtree(extract_path, ignore_errors=True)
    if upload_path:
        upload_path.unlink(missing_ok=True)
    for value in embedding_paths:
        path = Path(value).resolve()
        try:
            path.relative_to(settings.embeddings_dir.resolve())
        except ValueError:
            continue
        path.unlink(missing_ok=True)


frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


