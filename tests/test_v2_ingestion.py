import csv
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from dia.core.ingestion import DatasetValidationError, parse_dataset, safe_extract_zip


def _image(path: Path, color=(20, 40, 90)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (24, 18), color).save(path)


def test_folder_layout_reads_classes_and_splits(tmp_path):
    root = tmp_path / "extract" / "data"
    _image(root / "train" / "cat" / "a.png")
    _image(root / "test" / "dog" / "b.webp")

    layout, rows, warnings = parse_dataset(tmp_path / "extract")

    assert layout == "folder_per_class"
    assert {(r["ground_truth_class"], r["split"]) for r in rows} == {("cat", "train"), ("dog", "test")}
    assert all(row["is_valid"] for row in rows)
    assert warnings == []


def test_manifest_preserves_metadata_and_missing_labels(tmp_path):
    root = tmp_path / "dataset"
    _image(root / "imgs" / "a.jpg")
    _image(root / "imgs" / "b.jpg", color=(70, 20, 40))
    with (root / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "label", "age_group", "split"])
        writer.writeheader()
        writer.writerow({"image_path": "imgs/a.jpg", "label": "cat", "age_group": "adult", "split": "train"})
        writer.writerow({"image_path": "imgs/b.jpg", "label": "", "age_group": "", "split": "test"})

    layout, rows, warnings = parse_dataset(root)

    assert layout == "manifest"
    assert rows[0]["attributes"] == {"age_group": "adult"}
    assert rows[1]["ground_truth_class"] is None
    assert any("1 sample(s) have no class label" in warning for warning in warnings)


def test_zip_path_traversal_is_rejected(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../outside.txt", "bad")

    with pytest.raises(DatasetValidationError, match="Unsafe archive path"):
        safe_extract_zip(archive, tmp_path / "out")


def test_manifest_cannot_escape_dataset_root(tmp_path):
    root = tmp_path / "dataset"
    root.mkdir()
    with (root / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "label"])
        writer.writeheader()
        writer.writerow({"image_path": "../outside.jpg", "label": "cat"})

    with pytest.raises(DatasetValidationError, match="unsafe image path"):
        parse_dataset(root)
