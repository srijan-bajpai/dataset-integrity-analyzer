"""Safe archive handling and dataset layout parsing."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import stat
import zipfile
import warnings as py_warnings
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
        if len(zf.infolist()) > settings.max_samples * 5 + 256:
            raise DatasetValidationError("The archive contains too many entries for the configured dataset limit.")
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
            member_bytes = 0
            with zf.open(info) as source, target.open("wb") as output:
                while block := source.read(1024 * 1024):
                    member_bytes += len(block)
                    if member_bytes > settings.max_member_size_mb * 1024 * 1024:
                        raise DatasetValidationError(f"Archive member exceeds the per-file limit: {info.filename}")
                    output.write(block)
            total += member_bytes - info.file_size
            if total > max_bytes:
                raise DatasetValidationError("The expanded archive exceeds the configured size limit.")


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


def _filename_attributes(path: Path) -> dict[str, Any]:
    """Parse deterministic UTKFace-style filename fields as low-risk metadata."""
    match = re.match(r"^(\d{1,3})_([01])_([0-4])_", path.stem)
    if not match:
        return {}
    age = int(match.group(1))
    gender_code = int(match.group(2))
    race_code = int(match.group(3))
    age_band = "0-12" if age <= 12 else "13-19" if age <= 19 else "20-29" if age <= 29 else "30-39" if age <= 39 else "40-49" if age <= 49 else "50-59" if age <= 59 else "60+"
    values = {"age": age, "age_band": age_band, "gender": "male" if gender_code == 0 else "female",
              "race": {0: "white", 1: "black", 2: "asian", 3: "indian", 4: "other"}[race_code]}
    return {key: {"value": value, "confidence": 1.0, "provenance": "filename"} for key, value in values.items()}


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
        if not isinstance(row, dict):
            raise DatasetValidationError(f"Manifest row {i} must be an object with named fields.")
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
            "inferred_attributes": _filename_attributes(image_path),
        })
    return rows


def parse_dataset(root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Return layout, sample records, and ingestion warnings for a dataset root."""
    root = _unwrap_single_directory(root.resolve())
    manifests = [p for p in root.iterdir() if p.is_file() and p.name.lower() in {"metadata.csv", "manifest.csv", "metadata.jsonl", "manifest.jsonl", "metadata.ndjson", "manifest.ndjson"}]
    if len(manifests) > 1:
        raise DatasetValidationError("Provide only one metadata.csv, manifest.csv, metadata.jsonl, manifest.jsonl, metadata.ndjson, or manifest.ndjson file.")
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
                "inferred_attributes": _filename_attributes(image),
            })
        layout = "folder_per_class"

    if not records:
        raise DatasetValidationError("No supported image samples were found.")
    refs = [record["sample_ref"] for record in records]
    if len(set(refs)) != len(refs):
        raise DatasetValidationError("The dataset contains duplicate sample paths; each manifest row must refer to a unique image path.")
    if len(records) > settings.max_samples:
        raise DatasetValidationError(f"Dataset contains {len(records)} images; the limit is {settings.max_samples}.")

    warnings: list[str] = []
    valid_count = 0
    for record in records:
        path = Path(record["path"])
        record["content_sha256"] = _sha256(path)
        try:
            with py_warnings.catch_warnings():
                py_warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    gray = image.convert("L")
                    extrema = gray.getextrema()
                    record["anomaly_flags"] = [
                        flag for condition, flag in (
                            (extrema == (0, 0), "all_black"),
                            (extrema == (255, 255), "all_white"),
                            (extrema[0] == extrema[1], "zero_variance"),
                        ) if condition
                    ]
            record["is_valid"] = True
            valid_count += 1
        except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError, ValueError) as exc:
            record["is_valid"] = False
            record["error_message"] = f"Unreadable image: {type(exc).__name__}"
            warnings.append(f"{record['sample_ref']}: unreadable image")
    if valid_count == 0:
        raise DatasetValidationError("No readable image files were found.")
    classes_with_readable_images = {r["ground_truth_class"] for r in records if r.get("is_valid") and r.get("ground_truth_class")}
    classes_in_manifest = {r["ground_truth_class"] for r in records if r.get("ground_truth_class")}
    classes_without_readable_images = sorted(classes_in_manifest - classes_with_readable_images)
    if classes_without_readable_images:
        warnings.append(f"These classes contain no readable images and will be absent from image analyses: {classes_without_readable_images}.")
    labeled = [r for r in records if r["ground_truth_class"]]
    if not labeled:
        warnings.append("No class labels were found; label and class-balance checks will be unavailable.")
    elif len(labeled) < len(records):
        warnings.append(f"{len(records) - len(labeled)} sample(s) have no class label.")
    elif len({r["ground_truth_class"] for r in labeled}) < 2:
        warnings.append("Only one class label was found; class comparisons will be limited.")
    return layout, records, warnings


def dataset_fingerprint(root: Path, records: list[dict[str, Any]]) -> str:
    """Stable fingerprint from sorted sample paths and byte sizes."""
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: item["sample_ref"]):
        path = Path(record["path"])
        digest.update(record["sample_ref"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
