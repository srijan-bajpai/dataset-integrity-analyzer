"""Shared analysis pipeline used by the API worker and command line."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dia.analyzers.confounds import ConfoundAnalyzer
from dia.analyzers.distribution import DistributionAnalyzer
from dia.analyzers.diversity import DiversityAnalyzer
from dia.analyzers.duplicates import DuplicatesAnalyzer
from dia.analyzers.fairness import FairnessAnalyzer
from dia.analyzers.labels import LabelAuditAnalyzer
from dia.analyzers.metadata import MetadataAnalyzer
from dia.analyzers.quality import QualityAnalyzer
from dia.predict.impact import BiasImpactPredictor
from dia.recommend.engine import RecommendationEngine
from dia.scoring.readiness import ReadinessScorer


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if pd.isna(value) if not isinstance(value, (dict, list, tuple)) else False:
        return None
    return value


def run_analysis(records: list[dict[str, Any]], *, targets: dict[str, dict[str, float]] | None = None,
                 warnings: list[str] | None = None, embeddings_path: Path | None = None) -> dict[str, Any]:
    """Run all available checks and return a JSON-safe, versioned report."""
    if not records:
        raise ValueError("The dataset contains no samples.")
    df = pd.DataFrame.from_records(records)
    for key in ("attributes", "inferred_attributes"):
        if key in df.columns:
            attribute_rows = df[key].apply(lambda v: v if isinstance(v, dict) else {})
            attributes = pd.json_normalize(attribute_rows).add_prefix("attribute:")
            if not attributes.empty:
                df = pd.concat([df.drop(columns=[key]), attributes], axis=1)

    usable = df[df.get("is_valid", True).astype(bool)].copy().reset_index(drop=True)
    errors: dict[str, str] = {}
    results: dict[str, Any] = {}
    all_findings: list[dict[str, Any]] = []

    results["metadata"] = MetadataAnalyzer(df).run()
    all_findings.extend(results["metadata"].get("findings", []))

    target_columns = {f"attribute:{key}": value for key, value in (targets or {}).items()}
    results["fairness"] = FairnessAnalyzer(usable, target_columns).run()
    for finding in results["fairness"].get("findings", []):
        finding["attribute"] = finding["attribute"].removeprefix("attribute:")
        all_findings.append(finding)

    labeled = usable[usable["ground_truth_class"].notna()].copy().reset_index(drop=True) if "ground_truth_class" in usable else usable.iloc[0:0].copy()
    if not labeled.empty:
        try:
            results["distribution"] = DistributionAnalyzer(labeled).run()
        except Exception as exc:
            errors["distribution"] = f"{type(exc).__name__}: {exc}"
    else:
        results["distribution"] = {"status": "unavailable", "reason": "No class labels were supplied."}

    if not usable.empty:
        try:
            quality_frame = usable.copy().reset_index(drop=True)
            results["quality"] = QualityAnalyzer(quality_frame).run()
            results["quality"]["invalid_image_count"] = int(len(df) - len(usable))
            results["quality"]["defect_rate_pct"] = round(
                100 * float(quality_frame[["flag_blurred", "flag_underexposed", "flag_overexposed", "flag_low_contrast"]].any(axis=1).mean()), 2
            )
            usable = quality_frame
        except Exception as exc:
            errors["quality"] = f"{type(exc).__name__}: {exc}"
            results["quality"] = {"status": "unavailable", "reason": str(exc)}

        try:
            duplicate_frame = usable.copy().reset_index(drop=True)
            results["duplicates"] = DuplicatesAnalyzer(duplicate_frame).run()
            usable = duplicate_frame
        except Exception as exc:
            errors["duplicates"] = f"{type(exc).__name__}: {exc}"
            results["duplicates"] = {"status": "unavailable", "reason": str(exc)}
    else:
        results["quality"] = {"status": "unavailable", "reason": "No readable images."}
        results["duplicates"] = {"status": "unavailable", "reason": "No readable images."}

    embedding_dimensions = {"status": "unavailable", "reason": "At least two readable images are required."}
    sample_enrichment: dict[str, dict[str, Any]] = {}
    if len(usable) >= 2:
        try:
            from dia.extract.embeddings import FeatureExtractor

            extractor = FeatureExtractor(usable)
            path = str(embeddings_path) if embeddings_path else "embeddings.npy"
            embeddings = extractor.extract(path)
            if len(embeddings) != len(usable):
                raise ValueError("Embedding count does not match the readable sample count.")
            try:
                results["diversity"] = DiversityAnalyzer(usable, embeddings).run()
            except Exception as exc:
                errors["diversity"] = f"{type(exc).__name__}: {exc}"
                results["diversity"] = {"status": "unavailable", "reason": str(exc)}
            labeled_for_audit = usable[usable["ground_truth_class"].notna()].copy().reset_index(drop=True)
            if len(labeled_for_audit) >= 2 and labeled_for_audit["ground_truth_class"].nunique() >= 2:
                row_positions = usable.index[usable["ground_truth_class"].notna()].to_numpy()
                try:
                    results["labels"] = LabelAuditAnalyzer(labeled_for_audit, embeddings[row_positions]).run()
                except Exception as exc:
                    errors["labels"] = f"{type(exc).__name__}: {exc}"
                    results["labels"] = {"status": "unavailable", "reason": str(exc)}
            else:
                results["labels"] = {"status": "unavailable", "reason": "At least two labelled classes with repeated samples are required."}
            embedding_dimensions = {"status": "available", "model": "ResNet18_Weights.IMAGENET1K_V1", "count": len(embeddings)}

            for _, row in usable.iterrows():
                sample_enrichment[str(row.get("sample_ref", row.get("id", "")))] = {
                    key: _clean(row[key]) for key in ("cluster_id", "label_issue_prob", "flag_suspected_mislabel", "predicted_class") if key in row
                }
        except Exception as exc:
            embedding_dimensions = {"status": "unavailable", "reason": "Pretrained image features could not be loaded or computed."}
            errors["embeddings"] = f"{type(exc).__name__}: {exc}"
            results["diversity"] = {"status": "unavailable", "reason": embedding_dimensions["reason"]}
            results["labels"] = {"status": "unavailable", "reason": embedding_dimensions["reason"]}
    else:
        results["diversity"] = embedding_dimensions
        results["labels"] = {"status": "unavailable", "reason": "At least two readable, labelled classes are required."}

    try:
        confound_frame = usable.copy().reset_index(drop=True)
        if "flag_suspected_mislabel" in results.get("labels", {}):
            pass
        if "ground_truth_class" in confound_frame and "quality_blur" in confound_frame:
            results["confounds"] = ConfoundAnalyzer(confound_frame).run()
        else:
            results["confounds"] = {"detected_confounds": [], "status": "limited"}
    except Exception as exc:
        errors["confounds"] = f"{type(exc).__name__}: {exc}"
        results["confounds"] = {"detected_confounds": [], "status": "unavailable", "reason": str(exc)}

    if results.get("quality", {}).get("defect_rate_pct", 0) >= 5:
        all_findings.append({
            "code": "IMAGE_QUALITY_DEFECTS", "severity": "warning",
            "defect_rate_pct": results["quality"]["defect_rate_pct"],
            "description": "Some images fail one or more configurable image-quality checks.",
        })
    if results.get("duplicates", {}).get("near_duplicate_count", 0):
        all_findings.append({
            "code": "DUPLICATE_IMAGES", "severity": "warning",
            "count": results["duplicates"]["near_duplicate_count"],
            "description": "Exact or near-duplicate images were found; review possible train/test leakage.",
        })
    all_findings.extend(results.get("confounds", {}).get("detected_confounds", []))
    if results.get("labels", {}).get("label_noise_rate") is not None:
        results["labels"]["label_noise_rate_pct"] = round(100 * results["labels"]["label_noise_rate"], 2)
        if results["labels"]["label_noise_rate"] > 0:
            all_findings.append({
                "code": "POSSIBLE_LABEL_DISAGREEMENT", "severity": "review",
                "count": int((usable.get("flag_suspected_mislabel", pd.Series(dtype=bool)) == True).sum()),
                "description": "An embedding-based classifier disagrees with some supplied labels. Treat these as review suggestions, not confirmed errors.",
            })
    fairness_gaps = [
        abs(f.get("gap_percentage_points", 0)) / 100
        for f in results.get("fairness", {}).get("findings", [])
    ]
    if fairness_gaps:
        results["fairness"]["worst_absolute_target_gap"] = max(fairness_gaps)
    results["readiness"] = ReadinessScorer().compute(results)
    results["bias_impact"] = BiasImpactPredictor(results).predict()
    results["recommendations"] = RecommendationEngine(results).generate()

    sample_findings = []
    enriched = usable.set_index("sample_ref", drop=False) if "sample_ref" in usable else usable
    for ref, row in enriched.iterrows():
        details = sample_enrichment.get(str(ref), {})
        flags = [key for key in ("flag_blurred", "flag_underexposed", "flag_overexposed", "flag_low_contrast", "flag_duplicate", "flag_suspected_mislabel") if bool(row.get(key, False))]
        if flags or details.get("flag_suspected_mislabel"):
            sample_findings.append({
                "sample_ref": str(ref),
                "ground_truth_class": _clean(row.get("ground_truth_class")),
                "flags": flags,
                "predicted_class": details.get("predicted_class", _clean(row.get("predicted_class"))),
                "label_issue_prob": details.get("label_issue_prob", _clean(row.get("label_issue_prob"))),
                "duplicate_group": _clean(row.get("duplicate_group")),
            })

    return _clean({
        "report_version": "dia-report-v2",
        "analyzer_versions": {"core": "2.0.0", "readiness": ReadinessScorer.VERSION},
        "sample_count": len(df),
        "readable_sample_count": len(usable),
        "embedding_analysis": embedding_dimensions,
        "results": results,
        "findings": all_findings,
        "sample_findings": sample_findings,
        "warnings": warnings or [],
        "analyzer_errors": errors,
    })
