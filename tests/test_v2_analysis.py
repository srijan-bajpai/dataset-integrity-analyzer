from pathlib import Path

import pandas as pd
import numpy as np
from PIL import Image

from dia.analyzers.fairness import FairnessAnalyzer
from dia.analyzers.metadata import MetadataAnalyzer
from dia.analyzers.attribute_suggestions import AttributeSuggestionAnalyzer
from dia.analyzers.duplicates import DuplicatesAnalyzer
from dia.analyzers.quality import QualityAnalyzer
from dia.core.pipeline import run_analysis
from dia.scoring.readiness import ReadinessScorer


def test_fairness_reports_target_gap_and_class_breakdown():
    frame = pd.DataFrame({
        "age_group": ["adult"] * 8 + ["child"] * 2,
        "ground_truth_class": ["cat"] * 5 + ["dog"] * 5,
    })
    result = FairnessAnalyzer(frame, {"age_group": {"adult": 0.5, "child": 0.5}}).run()

    assert result["attributes"]["age_group"]["groups"]["adult"]["count"] == 8
    assert result["worst_absolute_target_gap"] == 0.3
    assert {f["scope"] for f in result["findings"]} == {"overall"}


def test_fairness_uses_explicit_class_targets_for_intersection_checks():
    frame = pd.DataFrame({"gender": ["a", "a", "b", "b"], "ground_truth_class": ["cat", "cat", "dog", "dog"]})
    targets = {"cat": {"gender": {"a": 0.5, "b": 0.5}}}
    result = FairnessAnalyzer(frame, class_targets=targets).run()
    assert any(f["scope"] == "class:cat" for f in result["findings"])


def test_fairness_rejects_invalid_target():
    frame = pd.DataFrame({"region": ["north", "south"]})
    try:
        FairnessAnalyzer(frame, {"region": {"north": 0.8, "south": 0.8}}).run()
    except ValueError as exc:
        assert "sum to 1" in str(exc)
    else:
        raise AssertionError("Invalid target proportions were accepted")


def test_metadata_reports_missing_values():
    result = MetadataAnalyzer(pd.DataFrame({"region": ["north", None, ""]})).run()
    assert result["attributes"]["region"]["missing_count"] == 2
    assert result["findings"][0]["code"] == "METADATA_MISSING_VALUES"


def test_metadata_schema_finds_invalid_values():
    frame = pd.DataFrame({"attribute:age": ["21", "unknown"], "sample_ref": ["a.jpg", "b.jpg"]})
    result = MetadataAnalyzer(frame, {"age": {"type": "integer"}}).run()
    assert result["attributes"]["age"]["invalid_count"] == 1
    assert any(f["code"] == "METADATA_INVALID_VALUES" and f["sample_refs"] == ["b.jpg"] for f in result["findings"])


def test_readiness_never_calls_low_coverage_production_ready():
    result = ReadinessScorer().compute({"distribution": {"imbalance_ratio": 1.0}})
    assert result["coverage_pct"] == 20.0
    assert result["verdict"] == "Insufficient Coverage"
    assert "Fairness" in result["unavailable_dimensions"]


def test_attribute_suggestions_are_opt_in_review_values_only():
    frame = pd.DataFrame({
        "sample_ref": [f"{i}.jpg" for i in range(9)],
        "attribute:group": ["a"] * 4 + ["b"] * 4 + [None],
    })
    embeddings = np.array([[float(i < 4), float(i >= 4)] for i in range(9)])
    result = AttributeSuggestionAnalyzer(frame, embeddings, minimum_per_value=2, review_confidence=0.5).run()
    suggestion = next(item for item in result["suggestions"] if item["sample_ref"] == "8.jpg")
    assert suggestion["supplied_value"] is None
    assert suggestion["suggested_value"] in {"a", "b"}
    assert pd.isna(frame.iloc[8]["attribute:group"])


def test_pipeline_emits_json_safe_per_sample_results_without_embeddings(tmp_path):
    image_path = tmp_path / "cat.png"
    Image.new("RGB", (32, 32), (100, 120, 140)).save(image_path)
    report = run_analysis([{
        "id": "sample-1", "sample_ref": "cat.png", "path": str(image_path),
        "ground_truth_class": "cat", "split": "train", "attributes": {"region": "north"},
        "content_sha256": "abc", "is_valid": True,
    }], use_embeddings=False)

    assert report["report_version"] == "dia-report-v2"
    assert report["sample_results"][0]["sample_ref"] == "cat.png"
    assert report["results"]["bias_impact"]["status"] == "unavailable"
    assert report["attribute_estimates"]["status"] == "not_requested"


def test_readiness_flags_cross_split_leakage_without_falsifying_score():
    inputs = {
        "distribution": {"imbalance_ratio": 1.0},
        "fairness": {"worst_absolute_target_gap": 0.0},
        "quality": {"defect_rate_pct": 0.0},
        "duplicates": {"redundancy_ratio": 0.0, "cross_split_duplicate_groups": 1},
        "diversity": {"cluster_entropy": 1.0},
        "labels": {"label_noise_rate_pct": 0.0},
    }
    result = ReadinessScorer().compute(inputs)
    assert result["overall_score"] == 100.0
    assert result["verdict"] == "Not Ready"
    assert result["hard_gate"]["cross_split_duplicate_leakage"]


def test_sampling_is_repeatable_and_reported(tmp_path):
    records = []
    for index in range(8):
        image = tmp_path / f"{index}.png"
        Image.new("RGB", (40, 40), (index * 10, 100, 100)).save(image)
        records.append({"sample_ref": image.name, "path": str(image), "ground_truth_class": "cat" if index < 4 else "dog",
                        "split": "train", "attributes": {}, "is_valid": True})
    first = run_analysis(records, use_embeddings=False, sampling_rate=0.5, sampling_seed=7)
    second = run_analysis(records, use_embeddings=False, sampling_rate=0.5, sampling_seed=7)
    assert [row["sample_ref"] for row in first["sample_results"]] == [row["sample_ref"] for row in second["sample_results"]]
    assert first["sampling"]["actual_rate"] == 0.5
    assert first["dataset_fingerprint"]


def test_quality_reports_noise_lighting_and_minimum_resolution(tmp_path):
    tiny = tmp_path / "tiny.png"
    Image.new("RGB", (16, 16), (5, 5, 5)).save(tiny)
    frame = pd.DataFrame({"path": [str(tiny)]})
    result = QualityAnalyzer(frame).run()
    assert frame.iloc[0]["quality_lighting_condition"] == "low"
    assert bool(frame.iloc[0]["flag_low_resolution"])
    assert frame.iloc[0]["quality_noise_mad"] == 0
    assert result["brisque"]["status"] == "unavailable"


def test_duplicate_detection_uses_exact_hashes_and_cross_split_groups(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (48, 48), (20, 50, 80)).save(first)
    first_bytes = first.read_bytes()
    second.write_bytes(first_bytes)
    frame = pd.DataFrame({
        "path": [str(first), str(second)], "content_sha256": ["same", "same"],
        "split": ["train", "test"], "ground_truth_class": ["cat", "dog"],
    })
    result = DuplicatesAnalyzer(frame).run()
    assert result["exact_duplicate_count"] == 1
    assert result["cross_split_duplicate_groups"] == 1
    assert result["conflicting_label_duplicate_groups"] == 1
