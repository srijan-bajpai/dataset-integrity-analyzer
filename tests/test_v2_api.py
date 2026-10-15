import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from dia.api.main import app
from dia.config import settings
from dia.db.session import reset_session_factory_for_tests


@pytest.fixture
def client(tmp_path):
    old = {name: getattr(settings, name) for name in ("storage_dir", "shared_password", "environment")}
    object.__setattr__(settings, "storage_dir", tmp_path / "storage")
    settings.ensure_directories()
    object.__setattr__(settings, "shared_password", "test-secret")
    object.__setattr__(settings, "environment", "test")
    reset_session_factory_for_tests(f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as test_client:
        yield test_client
    reset_session_factory_for_tests(f"sqlite:///{tmp_path / 'test.db'}")
    for name, value in old.items():
        object.__setattr__(settings, name, value)


def _dataset_zip() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for label, color in (("cats", "red"), ("dogs", "blue")):
            image = io.BytesIO()
            Image.new("RGB", (12, 12), color).save(image, format="PNG")
            archive.writestr(f"{label}/sample.png", image.getvalue())
    return stream.getvalue()


def test_api_upload_queue_report_and_delete(client):
    headers = {"X-DIA-Password": "test-secret"}
    uploaded = client.post(
        "/v1/datasets", headers=headers,
        files={"file": ("dataset.zip", _dataset_zip(), "application/zip")},
    )
    assert uploaded.status_code == 201, uploaded.text
    dataset_id = uploaded.json()["id"]
    assert uploaded.json()["sample_count"] == 2

    queued = client.post(
        f"/v1/datasets/{dataset_id}/runs", headers=headers,
        json={"fairness_targets": {"region": {"north": 0.5, "south": 0.5}}},
    )
    assert queued.status_code == 202, queued.text
    run_id = queued.json()["run_id"]
    assert client.get(f"/v1/runs/{run_id}", headers=headers).json()["status"] == "queued"
    assert len(client.get("/v1/datasets", headers=headers).json()) == 1

    deleted = client.delete(f"/v1/datasets/{dataset_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/v1/datasets/{dataset_id}", headers=headers).status_code == 404


def test_worker_persists_report_and_per_sample_metrics(client, monkeypatch):
    import dia.worker as worker

    headers = {"X-DIA-Password": "test-secret"}
    uploaded = client.post(
        "/v1/datasets", headers=headers,
        files={"file": ("dataset.zip", _dataset_zip(), "application/zip")},
    )
    dataset_id = uploaded.json()["id"]
    queued = client.post(f"/v1/datasets/{dataset_id}/runs", headers=headers, json={})
    run_id = queued.json()["run_id"]

    assert worker._claim_one() is not None
    assert worker.recover_abandoned_jobs() == 1
    assert client.get(f"/v1/runs/{run_id}", headers=headers).json()["status"] == "queued"

    monkeypatch.setattr(worker, "run_analysis", lambda *args, **kwargs: {
        "report_version": "dia-report-v2",
        "dataset_fingerprint": "fingerprint-1",
        "analyzer_versions": {"core": "test"},
        "results": {
            "readiness": {"overall_score": 72},
            "distribution": {"imbalance_ratio": 2.0, "class_counts": {"cat": 1, "dog": 1}},
            "fairness": {"worst_absolute_target_gap": 0.1},
            "quality": {"defect_rate_pct": 5.0},
            "duplicates": {"redundancy_ratio": 0.05, "cross_split_duplicate_groups": 0},
            "diversity": {"cluster_entropy": 0.8},
            "labels": {"label_noise_rate_pct": 2.0},
        },
        "findings": [],
        "sample_findings": [],
        "sample_results": [{"sample_ref": "cats/sample.png", "metrics": {"quality_blur": 4.0, "flag_blurred": True}}],
    })

    assert worker.run_once() is True
    assert client.get(f"/v1/runs/{run_id}", headers=headers).json()["status"] == "completed"
    assert client.get(f"/v1/runs/{run_id}/report", headers=headers).json()["results"]["readiness"]["overall_score"] == 72
    sample_response = client.get(f"/v1/runs/{run_id}/samples", headers=headers).json()
    assert sample_response["total"] == 1
    assert sample_response["items"][0]["metrics"]["quality_blur"] == 4.0
    csv_response = client.get(f"/v1/runs/{run_id}/samples.csv", headers=headers)
    assert csv_response.status_code == 200
    assert "sample_ref,flag_blurred,quality_blur" in csv_response.text
    scenario = client.post(f"/v1/runs/{run_id}/what-if", headers=headers, json={"changes": {"defect_rate_pct": 0}})
    assert scenario.status_code == 200
    assert scenario.json()["persisted"] is False
    assert client.get(f"/v1/runs/{run_id}/report", headers=headers).json()["results"]["readiness"]["overall_score"] == 72

    second = client.post(f"/v1/datasets/{dataset_id}/runs", headers=headers, json={}).json()["run_id"]
    assert worker.run_once() is True
    comparison = client.get(f"/v1/runs/{run_id}/compare/{second}", headers=headers)
    assert comparison.status_code == 200
    assert comparison.json()["same_dataset_fingerprint"] is True
    assert client.delete(f"/v1/datasets/{dataset_id}", headers=headers).status_code == 204


def test_api_requires_password_when_configured(client):
    response = client.get("/v1/datasets")
    assert response.status_code == 401
    assert client.get("/health").status_code == 200


def test_api_rejects_non_zip_upload(client):
    response = client.post(
        "/v1/datasets", headers={"X-DIA-Password": "test-secret"},
        files={"file": ("data.csv", b"not a zip", "text/csv")},
    )
    assert response.status_code == 415


def test_queued_analysis_can_be_cancelled(client):
    headers = {"X-DIA-Password": "test-secret"}
    uploaded = client.post(
        "/v1/datasets", headers=headers,
        files={"file": ("dataset.zip", _dataset_zip(), "application/zip")},
    )
    dataset_id = uploaded.json()["id"]
    queued = client.post(f"/v1/datasets/{dataset_id}/runs", headers=headers, json={})
    run_id = queued.json()["run_id"]
    response = client.post(f"/v1/runs/{run_id}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
