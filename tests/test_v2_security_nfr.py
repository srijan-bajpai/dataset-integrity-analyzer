"""Security, performance, and non-functional requirement verification (NFR-SEC*, NFR-P*)."""

import io
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from dia.api.main import app
from dia.config import settings
from dia.core.ingestion import DatasetValidationError, safe_extract_zip
from dia.db.session import reset_session_factory_for_tests


@pytest.fixture
def client(tmp_path):
    old = {name: getattr(settings, name) for name in ("storage_dir", "shared_password", "environment")}
    object.__setattr__(settings, "storage_dir", tmp_path / "storage")
    settings.ensure_directories()
    object.__setattr__(settings, "shared_password", "sec-secret")
    object.__setattr__(settings, "environment", "test")
    reset_session_factory_for_tests(f"sqlite:///{tmp_path / 'sec_test.db'}")
    with TestClient(app) as test_client:
        yield test_client
    reset_session_factory_for_tests(f"sqlite:///{tmp_path / 'sec_test.db'}")
    for name, value in old.items():
        object.__setattr__(settings, name, value)


def _dataset_zip() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for label in ("cats", "dogs"):
            image = io.BytesIO()
            Image.new("RGB", (20, 20), (50, 100, 150)).save(image, format="PNG")
            archive.writestr(f"{label}/sample.png", image.getvalue())
    return stream.getvalue()


def test_zip_slip_and_parent_traversal_blocked(tmp_path):
    """NFR-SEC5: Reject zip slip and directory traversal."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("../../etc/passwd", "evil")
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(stream.getvalue())

    with pytest.raises(DatasetValidationError, match="Unsafe archive path"):
        safe_extract_zip(bad_zip, tmp_path / "out")


def test_zip_bomb_protection(tmp_path):
    """NFR-SEC5: Reject archives exceeding declared uncompressed size limits."""
    old_limit = settings.max_extracted_size_mb
    try:
        object.__setattr__(settings, "max_extracted_size_mb", 2)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            # 5 MB of zeros compresses to a few KB
            archive.writestr("class_a/large_zeros.bin", b"\x00" * (5 * 1024 * 1024))
        bomb_zip = tmp_path / "bomb.zip"
        bomb_zip.write_bytes(stream.getvalue())

        with pytest.raises(DatasetValidationError, match="expanded archive exceeds the configured size limit"):
            safe_extract_zip(bomb_zip, tmp_path / "out")
    finally:
        object.__setattr__(settings, "max_extracted_size_mb", old_limit)


def test_cleanup_on_deletion(client):
    """NFR-S1, CON-4: Deleting a dataset cleanly removes stored files without leaving orphans."""
    headers = {"X-DIA-Password": "sec-secret"}
    uploaded = client.post(
        "/v1/datasets", headers=headers,
        files={"file": ("dataset.zip", _dataset_zip(), "application/zip")},
    )
    dataset_id = uploaded.json()["id"]

    # Verify extracted storage exists
    dataset_dir = settings.extract_dir / dataset_id
    assert dataset_dir.exists()

    # Delete dataset
    del_res = client.delete(f"/v1/datasets/{dataset_id}", headers=headers)
    assert del_res.status_code == 204
    assert not dataset_dir.exists()


def test_embedding_cache_speedup_on_rerun(tmp_path):
    """NFR-P8: Rerunning analysis on the same dataset reuses cached embeddings."""
    from dia.extract.embeddings import FeatureExtractor

    # 4 images
    paths = []
    for i in range(4):
        p = tmp_path / f"img_{i}.png"
        Image.new("RGB", (32, 32), (i * 20, 50, 100)).save(p)
        paths.append(str(p))

    df = pd.DataFrame({"path": paths})
    embed_file = tmp_path / "cached_embeds.npy"

    extractor = FeatureExtractor(df)
    t0 = time.monotonic()
    embs1 = extractor.extract(output_path=str(embed_file))
    t_first = time.monotonic() - t0

    # Second call on same output path must hit cache immediately
    t0 = time.monotonic()
    embs2 = extractor.extract(output_path=str(embed_file))
    t_cached = time.monotonic() - t0

    assert np.allclose(embs1, embs2)
    assert t_cached < t_first or t_cached < 0.1
