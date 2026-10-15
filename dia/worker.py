"""Single-process database-backed analysis worker; run with ``python -m dia.worker``."""

from __future__ import annotations

import logging
import os
import socket
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dia.config import settings
from dia.core.pipeline import run_analysis
from dia.db.models import AnalysisRun, Dataset, JobQueue, Sample, SampleResult
from dia.db.session import get_db_session

logging.basicConfig(level=os.getenv("DIA_LOG_LEVEL", "INFO"))
logger = logging.getLogger("dia.worker")
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
LEASE = timedelta(hours=2)


class AnalysisCancelled(Exception):
    pass


def _claim_one() -> str | None:
    with get_db_session() as db:
        now = datetime.now(timezone.utc)
        job = (
            db.query(JobQueue)
            .filter(
                (JobQueue.status == "pending")
                | ((JobQueue.status == "processing") & (JobQueue.lease_expires_at < now))
            )
            .order_by(JobQueue.created_at)
            .first()
        )
        if job is None:
            return None
        changed = (
            db.query(JobQueue)
            .filter(JobQueue.id == job.id)
            .filter(
                (JobQueue.status == "pending")
                | ((JobQueue.status == "processing") & (JobQueue.lease_expires_at < now))
            )
            .update({
                "status": "processing", "picked_at": now,
                "lease_expires_at": now + LEASE, "worker_id": WORKER_ID,
            }, synchronize_session=False)
        )
        if changed != 1:
            return None
        run = db.get(AnalysisRun, job.run_id)
        if run is not None:
            run.status = "running"
            run.started_at = now
            run.progress_percent = 1
            run.status_message = "Starting analysis"
            run.error_message = None
        return job.id


def recover_abandoned_jobs() -> int:
    """Requeue work left running when the configured single worker stopped."""
    with get_db_session() as db:
        jobs = db.query(JobQueue).filter(JobQueue.status == "processing").all()
        for job in jobs:
            job.status = "pending"
            job.worker_id = None
            job.lease_expires_at = None
            run = db.get(AnalysisRun, job.run_id)
            if run is not None and run.status == "running":
                run.status = "queued"
                run.started_at = None
        return len(jobs)


def run_once() -> bool:
    job_id = _claim_one()
    if job_id is None:
        return False
    start = time.monotonic()
    try:
        with get_db_session() as db:
            job = db.get(JobQueue, job_id)
            if job is None:
                return True
            run = db.get(AnalysisRun, job.run_id)
            if run is None:
                job.status = "failed"
                job.error_message = "Analysis run record is missing."
                job.completed_at = datetime.now(timezone.utc)
                return True
            dataset = db.get(Dataset, run.dataset_id)
            if dataset is None:
                raise ValueError("Dataset record is missing.")
            records = [{
                "id": sample.id,
                "sample_ref": sample.sample_ref,
                "path": sample.file_path,
                "ground_truth_class": sample.ground_truth_class,
                "split": sample.split,
                "attributes": sample.attributes or {},
                "content_sha256": sample.content_sha256,
                "inferred_attributes": sample.inferred_attributes or {},
                "anomaly_flags": sample.anomaly_flags or [],
                "is_valid": sample.is_valid,
                "error_message": sample.error_message,
            } for sample in db.query(Sample).filter(Sample.dataset_id == dataset.id).order_by(Sample.sample_ref).all()]
            run_id = run.id
            fingerprint = dataset.fingerprint
            config = run.config or {}
            warnings = []
            try:
                import json
                warnings = json.loads(dataset.description or "{}").get("ingestion_warnings", [])
            except (ValueError, TypeError):
                pass
            embed_path = settings.embeddings_dir / f"{run_id}.npy"
            storage_path = Path(dataset.storage_path)

        def update_progress(percent: int, message: str) -> None:
            with get_db_session() as progress_db:
                current = progress_db.get(AnalysisRun, run_id)
                if current is None or current.status == "cancelled":
                    raise AnalysisCancelled("Analysis was cancelled by the user.")
                if current.status == "running":
                    current.progress_percent = percent
                    current.status_message = message[:255]

        report = run_analysis(
            records,
            targets=config.get("fairness_targets", {}),
            class_targets=config.get("class_fairness_targets", {}),
            metadata_schema=config.get("metadata_schema", {}),
            sampling_rate=config.get("sampling_rate", 1.0),
            sampling_seed=config.get("sampling_seed", 42),
            dataset_fingerprint=fingerprint,
            warnings=warnings,
            embeddings_path=embed_path,
            estimate_attributes=config.get("estimate_attributes", False),
            progress_callback=update_progress,
        )

        with get_db_session() as db:
            job = db.get(JobQueue, job_id)
            run = db.get(AnalysisRun, run_id)
            if job is None or run is None:
                raise RuntimeError("Job or run was deleted while processing.")
            sample_ids = {
                sample.sample_ref: sample.id
                for sample in db.query(Sample).filter(Sample.dataset_id == run.dataset_id).all()
            }
            db.query(SampleResult).filter(SampleResult.run_id == run.id).delete(synchronize_session=False)
            db.add_all([
                SampleResult(run_id=run.id, sample_id=sample_ids[item["sample_ref"]], metrics=item["metrics"])
                for item in report.get("sample_results", [])
                if item["sample_ref"] in sample_ids
            ])
            run.report = report
            run.metrics = report.get("results", {})
            run.findings = report.get("findings", [])
            run.analyzer_versions = report.get("analyzer_versions", {})
            run.embeddings_path = str(embed_path) if embed_path.exists() else None
            run.duration_seconds = round(time.monotonic() - start, 3)
            run.status = "completed"
            run.progress_percent = 100
            run.status_message = "Analysis complete"
            run.completed_at = datetime.now(timezone.utc)
            job.status = "done"
            job.completed_at = datetime.now(timezone.utc)
            job.lease_expires_at = None
        logger.info("Completed DIA run %s", run_id)
    except AnalysisCancelled as exc:
        logger.info("Cancelled DIA job %s", job_id)
        with get_db_session() as db:
            job = db.get(JobQueue, job_id)
            if job is not None:
                job.status = "cancelled"
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
                job.lease_expires_at = None
                run = db.get(AnalysisRun, job.run_id)
                if run is not None:
                    run.status = "cancelled"
                    run.status_message = "Cancelled"
                    run.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.exception("DIA worker failed job %s", job_id)
        with get_db_session() as db:
            job = db.get(JobQueue, job_id)
            if job is not None:
                job.status = "failed"
                job.error_message = f"{type(exc).__name__}: {exc}"[:4000]
                job.completed_at = datetime.now(timezone.utc)
                job.lease_expires_at = None
                run = db.get(AnalysisRun, job.run_id)
                if run is not None:
                    run.status = "failed"
                    run.status_message = "Analysis failed"
                    run.error_message = job.error_message
                    run.completed_at = datetime.now(timezone.utc)
                    run.duration_seconds = round(time.monotonic() - start, 3)
    return True


def main() -> None:
    logger.info("DIA worker %s started", WORKER_ID)
    recovered = recover_abandoned_jobs()
    if recovered:
        logger.warning("Requeued %s abandoned analysis job(s)", recovered)
    while True:
        try:
            if not run_once():
                time.sleep(settings.worker_poll_seconds)
        except KeyboardInterrupt:
            logger.info("DIA worker stopping")
            break


if __name__ == "__main__":
    main()
