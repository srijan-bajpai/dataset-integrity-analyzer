"""Comprehensive acceptance test suite covering confident learning, confounds, recommendations, C2, and reports."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from PIL import Image

from dia.analyzers.confounds import ConfoundAnalyzer
from dia.analyzers.diversity import DiversityAnalyzer
from dia.analyzers.labels import LabelAuditAnalyzer
from dia.cli import run_cli_analysis
from dia.predict.descriptor import FEATURE_NAMES, build_bias_descriptor
from dia.predict.impact import BiasImpactPredictor
from dia.predict.perturbation import DatasetPerturbationHarness
from dia.recommend.engine import RecommendationEngine
from dia.reports.datasheet import format_datasheet_markdown, generate_datasheet
from dia.reports.html_report import render_html_report
from dia.scoring.readiness import ReadinessScorer


def test_confident_learning_estimates_thresholds_and_reliability():
    # 20 samples, 2 classes (10 each)
    embeddings = np.zeros((20, 4), dtype=np.float32)
    embeddings[:10, 0] = 1.0  # class 0 cluster
    embeddings[10:, 1] = 1.0  # class 1 cluster

    # Inject deliberate mislabel: sample 0 is labeled class 1 but sits in class 0 cluster
    labels = ["class_0"] * 10 + ["class_1"] * 10
    labels[0] = "class_1"  # mislabel!

    df = pd.DataFrame({
        "sample_ref": [f"img_{i}.jpg" for i in range(20)],
        "ground_truth_class": labels,
    })

    analyzer = LabelAuditAnalyzer(df, embeddings)
    res = analyzer.run()

    assert res["status"] == "available"
    assert res["suspected_count"] >= 1
    assert "class_0" in res["class_thresholds"]
    assert "class_1" in res["class_thresholds"]
    assert "class_0" in res["per_class_reliability"]
    assert bool(df.loc[0, "flag_suspected_mislabel"]) is True
    assert df.loc[0, "predicted_class"] == "class_0"
    assert res["per_class_reliability"]["class_1"] < 1.0


def test_diversity_cluster_redundancy_and_outliers():
    # 30 samples: 25 tightly clustered (near-identical), 5 sparse/outliers
    embeddings = np.random.normal(0, 0.01, size=(30, 8)).astype(np.float32)
    embeddings[:25, 0] = 5.0  # dense cluster with high cosine similarity
    embeddings[25:, 1] = 10.0  # distinct region

    df = pd.DataFrame({
        "sample_ref": [f"img_{i}.jpg" for i in range(30)],
        "ground_truth_class": ["cat"] * 15 + ["dog"] * 15,
    })

    analyzer = DiversityAnalyzer(df, embeddings, redundancy_cosine_threshold=0.90)
    res = analyzer.run()

    assert res["status"] == "available"
    assert res["total_prunable_samples"] > 0
    assert "redundant_clusters" in res
    assert "dbscan" in res
    assert "flag_visual_outlier" in df.columns


def test_confound_analyzer_detects_all_six_interactions():
    # Construct synthetic dataset with deliberate confounds:
    # 1. Quality x Class: cat has blur=20, dog has blur=300
    # 2. Quality x Attribute: female has blur=20, male has blur=300
    # 3. Redundancy x Class: cat has duplicate_group=0 for 8 samples
    # 4. Leakage x Class: duplicate group crosses train and test
    # 5. Label Noise x Class: class_1 has higher mislabels
    n = 40
    cats = 20
    dogs = 20
    classes = ["cat"] * cats + ["dog"] * dogs
    gender = (["female"] * 10 + ["male"] * 10) * 2

    # Deliberate quality confound
    blur = [20.0] * cats + [300.0] * dogs
    contrast = [10.0] * cats + [60.0] * dogs
    brightness = [35.0] * cats + [120.0] * dogs
    resolution = [64 * 64] * n
    noise = [5.0] * n

    # Deliberate redundancy & leakage confound
    dup_group = [0] * 8 + [None] * (n - 8)
    splits = ["train"] * 4 + ["test"] * 4 + ["train"] * (n - 8)

    # Deliberate mislabels in cat
    mislabels = [True] * 6 + [False] * 14 + [False] * 20

    df = pd.DataFrame({
        "sample_ref": [f"s_{i}.jpg" for i in range(n)],
        "ground_truth_class": classes,
        "attribute:gender": gender,
        "quality_blur": blur,
        "quality_contrast": contrast,
        "quality_brightness": brightness,
        "quality_resolution": resolution,
        "quality_noise_mad": noise,
        "duplicate_group": dup_group,
        "split": splits,
        "flag_suspected_mislabel": mislabels,
        "cluster_id": [0] * cats + [1] * 10 + [2] * 10,
    })

    analyzer = ConfoundAnalyzer(df)
    res = analyzer.run()

    detected_codes = {c["code"] for c in res["detected_confounds"]}
    assert "QUALITY_CLASS_CONFOUND" in detected_codes
    assert "REDUNDANCY_CLASS_CONFOUND" in detected_codes
    assert "LEAKAGE_CLASS_CONFOUND" in detected_codes
    assert len(res["absent_confounds"]) >= 0


def test_recommendation_engine_interaction_awareness_and_manifest():
    # Dataset with class imbalance (IR = 5:1) AND quality confound on minority class
    agg_res = {
        "sample_count": 120,
        "distribution": {"imbalance_ratio": 5.0, "class_counts": {"cat": 100, "dog": 20}},
        "quality": {"defect_rate_pct": 15.0, "sample_count": 120},
        "duplicates": {"redundancy_ratio": 0.08, "near_duplicate_count": 10, "cross_split_duplicate_groups": 1},
        "diversity": {"cluster_entropy": 0.5, "total_prunable_samples": 4},
        "labels": {"label_noise_rate_pct": 4.0, "suspected_count": 5},
        "confounds": {
            "detected_confounds": [{
                "code": "QUALITY_CLASS_CONFOUND",
                "type": "Quality-Class Confound",
                "effect_size_epsilon_squared": 0.25,
            }],
        },
        "sample_results": [
            {
                "sample_ref": "dog_dup.jpg",
                "ground_truth_class": "dog",
                "metrics": {"is_valid": True, "duplicate_group": 1},
            },
            {
                "sample_ref": "dog_dup_copy.jpg",
                "ground_truth_class": "dog",
                "metrics": {"is_valid": True, "duplicate_group": 1},
            },
            {
                "sample_ref": "cat_mislabel.jpg",
                "ground_truth_class": "cat",
                "metrics": {"is_valid": True, "flag_suspected_mislabel": True, "predicted_class": "dog", "label_issue_prob": 0.85},
            },
            {
                "sample_ref": "bad_image.jpg",
                "ground_truth_class": "cat",
                "metrics": {"is_valid": False, "error_message": "Truncated JPEG"},
            },
        ],
    }

    engine = RecommendationEngine(agg_res)
    recs = engine.generate()

    assert len(recs) >= 3
    # Check ranking by gain per effort
    assert recs[0]["rank"] == 1
    assert recs[0]["do_first"] is True
    assert any(r["action_type"] == "RESPLIT_LEAKAGE" for r in recs)

    # REQ-84: Check interaction-aware recommendation (conduct targeted collection, do not simply oversample)
    imb_rec = next(r for r in recs if "INTERACTION_AWARE" in r["action_type"])
    assert "Do NOT simply oversample" in imb_rec["action"]

    # Manifest generation (REQ-86)
    manifest = engine.generate_manifest()
    actions = {m["action"] for m in manifest}
    assert "REMOVE_DUPLICATE" in actions
    assert "RELABEL_SAMPLE" in actions
    assert "REMOVE_CORRUPT" in actions


def test_synthetic_perturbation_harness():
    harness = DatasetPerturbationHarness(42)
    samples = [
        {"id": f"s_{i}", "sample_ref": f"img_{i}.jpg", "ground_truth_class": "cat" if i < 30 else "dog", "split": "train"}
        for i in range(60)
    ]

    # Imbalance
    imbalanced = harness.apply_class_imbalance(samples, imbalance_ratio=3.0, minority_class="dog")
    cats = sum(1 for s in imbalanced if s["ground_truth_class"] == "cat")
    dogs = sum(1 for s in imbalanced if s["ground_truth_class"] == "dog")
    assert cats == 30
    assert dogs == 10

    # Duplicates
    duplicated = harness.inject_duplicates(samples, redundancy_rate=0.20, cross_split=True)
    assert len(duplicated) > len(samples)
    assert any(s.get("split") == "test" for s in duplicated)

    # Label noise
    noisy = harness.inject_label_noise(samples, noise_rate=0.25)
    flips = sum(1 for orig, n in zip(samples, noisy) if orig["ground_truth_class"] != n["ground_truth_class"])
    assert flips > 0


def test_bias_impact_predictor_inference():
    agg_res = {
        "sample_count": 200,
        "distribution": {"imbalance_ratio": 4.0, "normalized_shannon_entropy": 0.8},
        "fairness": {"worst_absolute_target_gap": 0.20},
        "quality": {"defect_rate_pct": 12.0, "mean_blur": 150.0},
        "duplicates": {"redundancy_ratio": 0.05, "cross_split_duplicate_groups": 0},
        "diversity": {"cluster_entropy": 0.85, "low_diversity_classes": []},
        "labels": {"label_noise_rate_pct": 3.0},
        "confounds": {"detected_confounds": []},
    }

    predictor = BiasImpactPredictor(agg_res, enabled=True)
    pred = predictor.predict()

    assert pred["status"] == "available"
    assert pred["is_validated"] is True
    assert pred["predicted_delta_accuracy_pct"] >= 0.0
    assert len(pred["delta_accuracy_prediction_interval"]) == 2
    assert pred["delta_accuracy_prediction_interval"][0] <= pred["predicted_delta_accuracy_pct"] <= pred["delta_accuracy_prediction_interval"][1]
    assert "defect_rate_pct" in pred["feature_attributions_delta_acc"]


def test_reports_html_and_datasheet_generation():
    dummy_report = {
        "report_version": "dia-report-v2",
        "dataset_fingerprint": "a1b2c3d4e5f67890",
        "sample_count": 100,
        "readable_sample_count": 100,
        "analyzed_sample_count": 100,
        "disclaimer": "Diagnostic aid only.",
        "results": {
            "readiness": {
                "overall_score": 78.5,
                "verdict": "Acceptable",
                "coverage_pct": 100.0,
                "sub_scores": {"Balance": 80.0, "Quality": 75.0, "Uniqueness": 90.0, "Diversity": 70.0, "Label Integrity": 85.0, "Fairness": 70.0},
                "weights": {"Balance": 0.2, "Quality": 0.15, "Uniqueness": 0.15, "Diversity": 0.15, "Label Integrity": 0.15, "Fairness": 0.2},
                "formula": "Weighted mean test formula",
                "hard_gate": {"triggered": False},
            },
            "distribution": {"imbalance_ratio": 2.1, "class_counts": {"cat": 60, "dog": 40}, "class_count": 2},
            "quality": {"defect_rate_pct": 3.0, "invalid_image_count": 0},
            "duplicates": {"redundancy_ratio": 0.02, "cross_split_duplicate_groups": 0, "near_duplicate_count": 2, "exact_duplicate_count": 1},
            "diversity": {"cluster_entropy": 0.8, "total_prunable_samples": 0},
            "labels": {"label_noise_rate_pct": 1.5, "suspected_count": 1},
            "fairness": {"worst_absolute_target_gap": 0.05},
            "confounds": {"detected_confounds": [], "absent_confounds": ["Quality-Class Confound"]},
            "recommendations": [{
                "rank": 1,
                "category": "Balance",
                "action_type": "BALANCE_CLASSES",
                "priority": "Medium",
                "defect": "Imbalance ratio 2.1:1",
                "projected_score_gain": 4.0,
                "estimated_effort": "Low",
                "gain_per_effort": 4.0,
                "do_first": True,
                "action": "Collect samples",
                "rationale": "Improve priors",
            }],
        },
        "remediation_manifest": [
            {"sample_ref": "img1.jpg", "action": "REMOVE_DUPLICATE", "target_dimension": "Uniqueness", "reason": "dup", "current_label": "cat", "suggested_value": "drop"},
        ],
    }

    html_out = render_html_report(dummy_report)
    assert "<!DOCTYPE html>" in html_out
    assert "Dataset Health Report" in html_out
    assert "Acceptable" in html_out

    ds = generate_datasheet(dummy_report)
    assert ds["schema_version"] == "datasheet-v1.0"
    assert ds["composition"]["total_instances"] == 100

    md_out = format_datasheet_markdown(dummy_report)
    assert "# Datasheet for Dataset" in md_out


def test_cli_end_to_end(tmp_path):
    # Create tiny dataset directory: 2 classes, 3 images each
    dataset_dir = tmp_path / "dataset"
    for label in ("cats", "dogs"):
        cdir = dataset_dir / label
        cdir.mkdir(parents=True, exist_ok=True)
        for i in range(3):
            Image.new("RGB", (24, 24), (i * 30, 80, 120)).save(cdir / f"{i}.png")

    out_json = tmp_path / "out" / "report.json"
    out_html = tmp_path / "out" / "report.html"
    out_ds = tmp_path / "out" / "datasheet.md"
    out_man = tmp_path / "out" / "manifest.csv"

    report = run_cli_analysis(
        dataset_path=dataset_dir,
        output_path=out_json,
        html_path=out_html,
        datasheet_path=out_ds,
        manifest_path=out_man,
        predict_impact=True,
    )

    assert out_json.exists()
    assert out_html.exists()
    assert out_ds.exists()
    assert out_man.exists()
    assert report["report_version"] == "dia-report-v2"
    assert report["sample_count"] == 6
