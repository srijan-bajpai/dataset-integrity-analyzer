"""Controlled transformation fixtures and degenerate input validation (NFR-Q1, NFR-Q12)."""

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from dia.analyzers.duplicates import DuplicatesAnalyzer
from dia.analyzers.quality import QualityAnalyzer
from dia.core.ingestion import DatasetValidationError, parse_dataset
from dia.core.pipeline import run_analysis


def test_quality_analyzer_across_supported_formats_and_resolutions(tmp_path):
    """Verifies quality analyzer across JPEG, PNG, WebP, BMP, TIFF and varied resolutions."""
    formats = [
        ("test.jpg", "JPEG", (64, 64), (120, 100, 80)),
        ("test.png", "PNG", (128, 96), (40, 50, 60)),
        ("test.webp", "WEBP", (48, 48), (200, 200, 200)),
        ("test.bmp", "BMP", (32, 64), (10, 20, 30)),
        ("test.tif", "TIFF", (80, 80), (150, 140, 130)),
    ]

    paths = []
    for fname, fmt, size, color in formats:
        p = tmp_path / fname
        Image.new("RGB", size, color).save(p, format=fmt)
        paths.append(str(p))

    df = pd.DataFrame({"path": paths})
    res = QualityAnalyzer(df).run()

    assert len(df) == 5
    assert df["quality_resolution"].tolist() == [64 * 64, 128 * 96, 48 * 48, 32 * 64, 80 * 80]
    assert df["quality_brightness"].notna().all()
    assert df["quality_contrast"].notna().all()
    assert df["quality_noise_mad"].notna().all()
    assert res["brisque"]["status"] == "unavailable"


def test_duplicate_thresholds_under_controlled_transformations(tmp_path):
    """
    Validates duplicate detection behavior under controlled transformations:
    - Byte-identical: exact duplicate
    - Slight brightness shift: near duplicate
    - Different content: not duplicate
    """
    base_img = Image.new("RGB", (64, 64), (100, 150, 200))
    # Draw some structure so hash isn't flat
    for x in range(20, 45):
        for y in range(20, 45):
            base_img.putpixel((x, y), (250, 50, 50))

    base_path = tmp_path / "base.png"
    exact_path = tmp_path / "exact.png"
    slight_bright_path = tmp_path / "bright.png"
    diff_path = tmp_path / "diff.png"

    base_img.save(base_path)
    base_img.save(exact_path)

    # Slight brightness shift (+5)
    bright_img = Image.new("RGB", (64, 64), (105, 155, 205))
    for x in range(20, 45):
        for y in range(20, 45):
            bright_img.putpixel((x, y), (255, 55, 55))
    bright_img.save(slight_bright_path)

    # Completely different image (checkerboard)
    diff_img = Image.new("RGB", (64, 64), (10, 10, 10))
    for x in range(0, 64, 8):
        for y in range(0, 64, 8):
            diff_img.putpixel((x, y), (240, 240, 240))
    diff_img.save(diff_path)

    df = pd.DataFrame({
        "path": [str(base_path), str(exact_path), str(slight_bright_path), str(diff_path)],
        "ground_truth_class": ["cat", "cat", "cat", "dog"],
        "split": ["train", "train", "train", "test"],
    })

    res = DuplicatesAnalyzer(df, near_distance=5).run()

    # Base and exact match must be exact duplicate
    assert res["exact_duplicate_count"] >= 1
    # Base, exact, and slightly brightened should share duplicate group
    assert df.loc[0, "duplicate_group"] == df.loc[1, "duplicate_group"]
    # Distinct checkerboard must NOT be in the same duplicate group
    assert df.loc[3, "duplicate_group"] != df.loc[0, "duplicate_group"]


def test_degenerate_inputs_handled_robustly(tmp_path):
    """Verifies robustness against degenerate inputs per NFR-Q12."""
    # 1. 1x1 pixel image
    p_1px = tmp_path / "tiny.png"
    Image.new("RGB", (1, 1), (50, 50, 50)).save(p_1px)

    df_1px = pd.DataFrame({"path": [str(p_1px)]})
    res_1px = QualityAnalyzer(df_1px).run()
    assert bool(df_1px.loc[0, "flag_low_resolution"]) is True
    assert df_1px.loc[0, "quality_resolution"] == 1

    # 2. Corrupt / empty file alongside valid image
    p_corrupt = tmp_path / "corrupt.jpg"
    p_corrupt.write_bytes(b"garbage content not an image")
    p_valid = tmp_path / "valid.png"
    Image.new("RGB", (32, 32), (100, 100, 100)).save(p_valid)

    # Ingestion marks corrupt file as is_valid=False and continues without crashing (NFR-Q2)
    layout_dir = tmp_path / "dataset"
    (layout_dir / "class_a").mkdir(parents=True)
    (layout_dir / "class_b").mkdir(parents=True)
    p_corrupt_in_data = layout_dir / "class_a" / "bad.jpg"
    p_corrupt_in_data.write_bytes(b"bad bytes")
    Image.new("RGB", (32, 32), (10, 20, 30)).save(layout_dir / "class_a" / "good_a.png")
    Image.new("RGB", (32, 32), (40, 50, 60)).save(layout_dir / "class_b" / "good_b.png")

    _, records, warnings = parse_dataset(layout_dir)
    assert len(records) == 3
    bad_rec = next(r for r in records if r["sample_ref"].endswith("bad.jpg"))
    assert bad_rec["is_valid"] is False

    # Run analysis continues smoothly despite presence of corrupt sample
    report = run_analysis(records, use_embeddings=False)
    assert report["sample_count"] == 3
    assert report["readable_sample_count"] == 2
    assert report["results"]["quality"]["invalid_image_count"] == 1
