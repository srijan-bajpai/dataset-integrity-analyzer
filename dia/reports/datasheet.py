"""Datasheet for Datasets / Model Card generator based on Gebru et al. (REQ-95)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_datasheet(report: dict[str, Any]) -> dict[str, Any]:
    """
    Produce a structured Datasheet for Datasets (Gebru et al., 2021)
    automatically populated from DIA 2.0 audit measurements.
    """
    results = report.get("results", {})
    dist = results.get("distribution", {})
    quality = results.get("quality", {})
    duplicates = results.get("duplicates", {})
    diversity = results.get("diversity", {})
    labels = results.get("labels", {})
    fairness = results.get("fairness", {})
    readiness = results.get("readiness", {})
    sampling = report.get("sampling", {})

    datasheet = {
        "schema_version": "datasheet-v1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_identification": {
            "dataset_fingerprint": report.get("dataset_fingerprint"),
            "report_version": report.get("report_version"),
            "ai_readiness_score": readiness.get("overall_score"),
            "readiness_verdict": readiness.get("verdict"),
            "audit_coverage_pct": readiness.get("coverage_pct"),
        },
        "motivation": {
            "purpose": "Audited using Dataset Integrity Analyzer (DIA) 2.0 for image classification integrity before model training.",
            "intended_uses": "Supervised visual classification evaluation and training.",
            "disclaimer": report.get("disclaimer"),
        },
        "composition": {
            "total_instances": report.get("sample_count"),
            "readable_instances": report.get("readable_sample_count"),
            "analyzed_instances": report.get("analyzed_sample_count"),
            "class_count": dist.get("class_count", len(dist.get("class_counts", {}))),
            "classes": sorted(list(dist.get("class_counts", {}).keys())),
            "class_distribution": dist.get("class_counts", {}),
            "majority_to_minority_imbalance_ratio": dist.get("imbalance_ratio"),
            "shannon_entropy": dist.get("shannon_entropy"),
            "gini_coefficient": dist.get("gini_coefficient"),
            "sampling_rate_applied": sampling.get("actual_rate", 1.0),
            "sampling_strategy": sampling.get("strategy"),
        },
        "collection_process": {
            "metadata_provenance": report.get("metadata_provenance", {}),
            "splits": report.get("splits", {}),
            "cross_split_leakage_groups": duplicates.get("cross_split_duplicate_groups", 0),
        },
        "preprocessing_and_cleaning": {
            "corrupt_or_unreadable_instances": quality.get("invalid_image_count", 0),
            "exact_duplicate_count": duplicates.get("exact_duplicate_count", 0),
            "near_duplicate_count": duplicates.get("near_duplicate_count", 0),
            "redundancy_ratio": duplicates.get("redundancy_ratio", 0.0),
            "prunable_redundant_cluster_samples": diversity.get("total_prunable_samples", 0),
            "confident_learning_suspected_mislabels": labels.get("suspected_count", 0),
            "estimated_label_noise_rate_pct": labels.get("label_noise_rate_pct"),
            "remediation_manifest_records": len(report.get("remediation_manifest", [])),
        },
        "quality_and_fairness_measurements": {
            "dimension_scores": readiness.get("sub_scores", {}),
            "dimension_weights": readiness.get("weights", {}),
            "mean_image_blur_laplacian": quality.get("mean_blur"),
            "mean_image_brightness_lab_l": quality.get("mean_brightness"),
            "mean_image_contrast_std_l": quality.get("mean_contrast"),
            "defect_rate_pct": quality.get("defect_rate_pct"),
            "cluster_entropy": diversity.get("cluster_entropy"),
            "mean_pairwise_cosine_distance": diversity.get("mean_pairwise_cosine_distance"),
            "worst_fairness_target_gap": fairness.get("worst_absolute_target_gap"),
            "cross_dimensional_confounds": report.get("results", {}).get("confounds", {}).get("detected_confounds", []),
        },
        "maintenance_and_reproducibility": {
            "analyzer_versions": report.get("analyzer_versions", {}),
            "embedding_backbone": report.get("model_versions", {}).get("embedding"),
            "reproducibility_seed": sampling.get("seed", 42),
        },
    }
    return datasheet


def format_datasheet_markdown(report: dict[str, Any]) -> str:
    """Format the Datasheet into a publication-ready Markdown document."""
    ds = generate_datasheet(report)
    ident = ds["dataset_identification"]
    comp = ds["composition"]
    prep = ds["preprocessing_and_cleaning"]
    qual = ds["quality_and_fairness_measurements"]

    lines = [
        f"# Datasheet for Dataset (Fingerprint: {ident['dataset_fingerprint'] or 'N/A'})",
        "",
        f"**Generated**: {ds['generated_at']} | **DIA Version**: 2.0.0",
        f"**AI Readiness Score**: {ident['ai_readiness_score']} / 100 ({ident['readiness_verdict']}) | **Audit Coverage**: {ident['audit_coverage_pct']}%",
        "",
        "## 1. Motivation & Purpose",
        f"- **Purpose**: {ds['motivation']['purpose']}",
        f"- **Intended Use**: {ds['motivation']['intended_uses']}",
        f"- **Disclaimer**: {ds['motivation']['disclaimer']}",
        "",
        "## 2. Dataset Composition",
        f"- **Total Instances**: {comp['total_instances']}",
        f"- **Analyzed Instances**: {comp['analyzed_instances']} (sampling rate: {comp['sampling_rate_applied']:.1%})",
        f"- **Number of Classes**: {comp['class_count']}",
        f"- **Imbalance Ratio (Majority : Minority)**: {comp['majority_to_minority_imbalance_ratio']}:1",
        f"- **Shannon Entropy**: {comp['shannon_entropy']} | **Gini Coefficient**: {comp['gini_coefficient']}",
        "",
        "### Class Distribution Table",
        "| Class | Sample Count |",
        "| :--- | :--- |",
    ]
    for c, cnt in sorted(comp["class_distribution"].items(), key=lambda x: -x[1]):
        lines.append(f"| {c} | {cnt:,} |")

    lines.extend([
        "",
        "## 3. Preprocessing, Duplication & Integrity",
        f"- **Corrupt / Unreadable Images**: {prep['corrupt_or_unreadable_instances']}",
        f"- **Exact Duplicates**: {prep['exact_duplicate_count']}",
        f"- **Near-Duplicates**: {prep['near_duplicate_count']} (redundancy ratio: {prep['redundancy_ratio']:.2%})",
        f"- **Cross-Split Leakage Groups**: {ds['collection_process']['cross_split_leakage_groups']}",
        f"- **Prunable Redundant Cluster Samples**: {prep['prunable_redundant_cluster_samples']}",
        f"- **Confident Learning Suspected Mislabels**: {prep['confident_learning_suspected_mislabels']} ({prep['estimated_label_noise_rate_pct']}%)",
        "",
        "## 4. Quality & Health Dimension Scores (0-100 Scale)",
        "| Dimension | Sub-Score | Weight |",
        "| :--- | :--- | :--- |",
    ])
    for dim, score in qual["dimension_scores"].items():
        weight = qual["dimension_weights"].get(dim, 0.0)
        lines.append(f"| {dim} | {score} / 100 | {weight:.0%} |")

    lines.extend([
        "",
        "## 5. Cross-Dimensional Confounds Detected",
    ])
    confounds = qual["cross_dimensional_confounds"]
    if confounds:
        for c in confounds:
            lines.append(f"- **{c.get('type', 'Confound')}**: {c.get('description', '')} Downstream impact: {c.get('downstream_consequence', '')}")
    else:
        lines.append("- No significant cross-dimensional confounds detected.")

    lines.extend([
        "",
        "## 6. Reproducibility & Provenance",
        f"- **Embedding Model**: {ds['maintenance_and_reproducibility']['embedding_backbone']}",
        f"- **Sampling Seed**: {ds['maintenance_and_reproducibility']['reproducibility_seed']}",
        f"- **Core Analyzers**: DIA 2.0 unified evaluation suite",
        "",
    ])
    return "\n".join(lines)
