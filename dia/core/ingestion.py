"""Safe archive handling and dataset layout parsing."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

from dia.config import settings


class DatasetValidationError(ValueError):
    """Raised when an upload does not follow a supported dataset layout."""


def safe_extract_zip(archive: Path, destination: Path) -> None:
    """Extract a ZIP while rejecting traversal, links, and oversized archives."""
    destination.mkdir(parents=True, exist_ok=True)
    max_bytes = settings.max_extracted_size_mb * 1024 * 1024
    total = 0
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            rel = PurePosixPath(name)
            mode = info.external_attr >> 16
            if rel.is_absolute() or any(part in {"..", ""} for part in rel.parts):
                raise DatasetValidationError(f"Unsafe archive path: {info.filename}")
            if stat.S_ISLNK(mode):
                raise DatasetValidationError(f"Symbolic links are not allowed: {info.filename}")
            if info.file_size > settings.max_member_size_mb * 1024 * 1024:
                raise DatasetValidationError(f"Archive member exceeds the per-file limit: {info.filename}")
            total += info.file_size
            if total > max_bytes:
                raise DatasetValidationError("The expanded archive exceeds the configured size limit.")

            target = (destination / Path(*rel.parts)).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise DatasetValidationError(f"Unsafe archive path: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def _unwrap_single_directory(root: Path) -> Path:
    children = list(root.iterdir())
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return root


def _supported_images(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in settings.supported_image_extensions
    )


def _attributes(row: dict[str, Any], reserved: set[str]) -> dict[str, Any]:
    return {
        key: value.strip() if isinstance(value, str) else value
        for key, value in row.items()
        if key not in reserved and value not in (None, "")
    }


def _parse_manifest(root: Path, manifest: Path) -> list[dict[str, Any]]:
    reserved = {"image_path", "path", "image", "label", "ground_truth_class", "split"}
    rows: list[dict[str, Any]] = []
    if manifest.suffix.lower() == ".csv":
        with manifest.open("r", newline="", encoding="utf-8-sig") as f:
            source_rows = list(csv.DictReader(f))
    elif manifest.suffix.lower() in {".jsonl", ".ndjson"}:
        with manifest.open("r", encoding="utf-8") as f:
            source_rows = [json.loads(line) for line in f if line.strip()]
    else:
        raise DatasetValidationError("Manifest must be CSV or JSONL.")

    if not source_rows:
        raise DatasetValidationError("The manifest contains no samples.")
    for i, row in enumerate(source_rows, start=1):
        image_ref = row.get("image_path") or row.get("path") or row.get("image")
        if not isinstance(image_ref, str) or not image_ref.strip():
            raise DatasetValidationError(f"Manifest row {i} has no image_path.")
        rel = PurePosixPath(image_ref.replace("\\", "/"))
        if rel.is_absolute() or any(part in {"..", ""} for part in rel.parts):
            raise DatasetValidationError(f"Manifest row {i} has an unsafe image path.")
        image_path = (root / Path(*rel.parts)).resolve()
        if not image_path.is_relative_to(root.resolve()) or not image_path.is_file():
            raise DatasetValidationError(f"Manifest image does not exist: {image_ref}")
        if image_path.suffix.lower() not in settings.supported_image_extensions:
            raise DatasetValidationError(f"Unsupported image extension: {image_ref}")
        label = row.get("label") or row.get("ground_truth_class")
        split = row.get("split") or "unspecified"
        rows.append({
            "sample_ref": image_path.relative_to(root).as_posix(),
            "path": str(image_path),
            "ground_truth_class": str(label).strip() if label not in (None, "") else None,
            "split": str(split).strip().lower(),
            "attributes": _attributes(row, reserved),
        })
    return rows


def parse_dataset(root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Return layout, sample records, and ingestion warnings for a dataset root."""
    root = _unwrap_single_directory(root.resolve())
    manifests = [p for p in root.iterdir() if p.is_file() and p.name.lower() in {"metadata.csv", "manifest.csv", "metadata.jsonl", "manifest.jsonl", "metadata.ndjson", "manifest.ndjson"}]
    if manifests:
        records = _parse_manifest(root, manifests[0])
        layout = "manifest"
    else:
        records = []
        split_names = {"train", "val", "validation", "test"}
        top_dirs = [p for p in root.iterdir() if p.is_dir()]
        has_splits = bool(top_dirs) and all(p.name.lower() in split_names for p in top_dirs)
        for image in _supported_images(root):
            rel = image.relative_to(root)
            parts = rel.parts
            if has_splits and len(parts) >= 3:
                split, label = parts[0].lower(), parts[1]
                split = "val" if split == "validation" else split
            elif len(parts) >= 2:
                label, split = parts[0], "unspecified"
            else:
                raise DatasetValidationError("Folder datasets must place images inside class-named folders.")
            records.append({
                "sample_ref": rel.as_posix(), "path": str(image),
                "ground_truth_class": label, "split": split, "attributes": {},
            })
        layout = "folder_per_class"

    if not records:
        raise DatasetValidationError("No supported image samples were found.")
    if len(records) > settings.max_samples:
        raise DatasetValidationError(f"Dataset contains {len(records)} images; the limit is {settings.max_samples}.")

    warnings: list[str] = []
    valid_count = 0
    for record in records:
        path = Path(record["path"])
        record["content_sha256"] = _sha256(path)
        try:
            with Image.open(path) as image:
                image.verify()
            record["is_valid"] = True
            valid_count += 1
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            record["is_valid"] = False
            record["error_message"] = f"Unreadable image: {type(exc).__name__}"
            warnings.append(f"{record['sample_ref']}: unreadable image")
    if valid_count == 0:
        raise DatasetValidationError("No readable image files were found.")
    labeled = [r for r in records if r["ground_truth_class"]]
    if not labeled:
        warnings.append("No class labels were found; label and class-balance checks will be unavailable.")
    elif len({r["ground_truth_class"] for r in labeled}) < 2:
        warnings.append("Only one class label was found; class comparisons will be limited.")
    return layout, records, warnings


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
