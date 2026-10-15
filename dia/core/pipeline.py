"""Shared analysis pipeline used by the API worker and command line."""

from __future__ import annotations

import math
import hashlib
from pathlib import Path
from typing import Any
from importlib.metadata import PackageNotFoundError, version

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


def _runtime_versions() -> dict[str, str]:
    versions = {}
    for distribution in ("fastapi", "sqlalchemy", "pandas", "numpy", "scikit-learn", "scipy", "torch", "torchvision", "opencv-python-headless", "Pillow", "ImageHash"):
        try:
            versions[distribution] = version(distribution)
        except PackageNotFoundError:
            continue
    return versions


def run_analysis(records: list[dict[str, Any]], *, targets: dict[str, dict[str, float]] | None = None,
                 class_targets: dict[str, dict[str, dict[str, float]]] | None = None,
                 metadata_schema: dict[str, dict[str, Any]] | None = None,
                 warnings: list[str] | None = None, embeddings_path: Path | None = None,
                 use_embeddings: bool = True, estimate_attributes: bool = False,
                 sampling_rate: float = 1.0, sampling_seed: int = 42,
                 dataset_fingerprint: str | None = None,
                 progress_callback=None) -> dict[str, Any]:
    """Run all available checks and return a JSON-safe, versioned report."""
    if not records:
        raise ValueError("The dataset contains no samples.")
    df = pd.DataFrame.from_records(records)
    supplied_rows = df["attributes"].apply(lambda v: v if isinstance(v, dict) else {}) if "attributes" in df else pd.Series([{}] * len(df))
    inferred_rows = df["inferred_attributes"].apply(lambda v: v if isinstance(v, dict) else {}) if "inferred_attributes" in df else pd.Series([{}] * len(df))
    supplied_frame = pd.json_normalize(supplied_rows).add_prefix("attribute:")
    inferred_values = inferred_rows.apply(lambda values: {
        key: value.get("value") if isinstance(value, dict) and "value" in value else value
        for key, value in values.items()
    })
    inferred_frame = pd.json_normalize(inferred_values).add_prefix("attribute:")
    attr_cols = sorted(set(supplied_frame.columns) | set(inferred_frame.columns))
    metadata_frame = pd.DataFrame(index=df.index)
    for column in attr_cols:
        supplied = supplied_frame[column] if column in supplied_frame else pd.Series([None] * len(df), index=df.index)
        inferred = inferred_frame[column] if column in inferred_frame else pd.Series([None] * len(df), index=df.index)
        present = supplied.notna() & supplied.astype("string").str.strip().ne("").fillna(False)
        metadata_frame[column] = supplied.where(present, inferred)
        name = column.removeprefix("attribute:")
        metadata_frame[f"metadata_source:{name}"] = [
            "manifest" if bool(has_supplied) else (
                (row.get(name, {}).get("provenance", "inferred") if isinstance(row.get(name), dict) else "inferred")
                if pd.notna(inferred.iloc[i]) else "missing"
            )
            for i, (has_supplied, row) in enumerate(zip(present, inferred_rows))
        ]
        metadata_frame[f"attribute_confidence:{name}"] = [
            1.0 if bool(has_supplied) else (
                row.get(name, {}).get("confidence") if isinstance(row.get(name), dict) else None
            )
            for has_supplied, row in zip(present, inferred_rows)
        ]
    provenance_summary = {}
    for column in attr_cols:
        name = column.removeprefix("attribute:")
        source_col = f"metadata_source:{name}"
        confidence_col = f"attribute_confidence:{name}"
        confidence_values = pd.to_numeric(metadata_frame[confidence_col], errors="coerce").dropna() if confidence_col in metadata_frame else pd.Series(dtype=float)
        provenance_summary[name] = {
            "sample_count": int(len(metadata_frame)),
            "source_counts": {str(key): int(value) for key, value in metadata_frame[source_col].value_counts(dropna=False).items()},
            "mean_confidence": float(confidence_values.mean()) if len(confidence_values) else None,
        }
    df = pd.concat([df.drop(columns=[key for key in ("attributes", "inferred_attributes") if key in df]), metadata_frame], axis=1)

    valid_mask = df["is_valid"].fillna(False).astype(bool) if "is_valid" in df else pd.Series(True, index=df.index)
    all_usable = df.loc[valid_mask].copy().reset_index(drop=True)
    if not 0 < float(sampling_rate) <= 1:
        raise ValueError("sampling_rate must be greater than 0 and at most 1.")
    sampled = all_usable
    if sampling_rate < 1 and len(all_usable) > 1:
        rng = np.random.default_rng(sampling_seed)
        stratum_cols = [c for c in ("ground_truth_class", "split") if c in all_usable]
        groups = all_usable.groupby(stratum_cols, dropna=False, sort=True) if stratum_cols else [(None, all_usable)]
        selected = []
        for _, group in groups:
            count = min(len(group), max(1, int(round(len(group) * sampling_rate))))
            selected.extend(rng.choice(group.index.to_numpy(), size=count, replace=False).tolist())
        sampled = all_usable.loc[sorted(set(selected))].reset_index(drop=True)
    usable = sampled.copy()
    errors: dict[str, str] = {}
    results: dict[str, Any] = {}
    all_findings: list[dict[str, Any]] = []

    def progress(value: int, message: str) -> None:
        if progress_callback:
            progress_callback(value, message)

    progress(5, "Checking supplied metadata")

    results["metadata"] = MetadataAnalyzer(df, metadata_schema).run()
    all_findings.extend(results["metadata"].get("findings", []))

    progress(15, "Comparing group representation")

    labeled = usable[usable["ground_truth_class"].notna()].copy().reset_index(drop=True) if "ground_truth_class" in usable else usable.iloc[0:0].copy()
    if not labeled.empty:
        try:
            results["distribution"] = DistributionAnalyzer(labeled).run()
        except Exception as exc:
            errors["distribution"] = f"{type(exc).__name__}: {exc}"
    else:
        results["distribution"] = {"status": "unavailable", "reason": "No class labels were supplied."}
    progress(25, "Measuring class distribution")

    if not usable.empty:
        try:
            quality_frame = usable.copy().reset_index(drop=True)
            results["quality"] = QualityAnalyzer(quality_frame).run()
            results["quality"]["invalid_image_count"] = int(len(df) - len(all_usable))
            results["quality"]["sample_count"] = int(len(usable))
            results["quality"]["not_sampled_count"] = int(len(all_usable) - len(usable))
            usable = quality_frame
            usable["attribute:lighting_condition"] = usable["quality_lighting_condition"]
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
    progress(45, "Checking image quality and duplicates")

    fairness_frame = usable.rename(columns={
        column: column.removeprefix("attribute:")
        for column in usable.columns if column.startswith("attribute:")
    })
    results["fairness"] = FairnessAnalyzer(fairness_frame, targets, class_targets).run()
    for finding in results["fairness"].get("findings", []):
        all_findings.append(finding)
    for dimension, split_result in results["fairness"].get("split_skew", {}).get("dimensions", {}).items():
        if split_result.get("flagged"):
            all_findings.append({
                "code": "SPLIT_DISTRIBUTION_SKEW", "severity": "warning",
                "dimension": dimension, "comparisons": split_result.get("comparisons", []),
                "description": f"The distribution of '{dimension}' differs between at least two dataset splits (Jensen-Shannon divergence > 0.1).",
            })

    embedding_dimensions = {"status": "unavailable", "reason": "At least two readable images are required."}
    sample_enrichment: dict[str, dict[str, Any]] = {}
    attribute_estimates: dict[str, Any] = {
        "status": "not_requested",
        "reason": None,
    }
    if len(usable) >= 2 and use_embeddings:
        try:
            from dia.extract.embeddings import FeatureExtractor

            extractor = FeatureExtractor(usable)
            path = str(embeddings_path) if embeddings_path else "embeddings.npy"
            embeddings = extractor.extract(path, progress_callback=progress_callback)
            if len(embeddings) != len(usable):
                raise ValueError("Embedding count does not match the readable sample count.")
            confirmed_duplicate_frame = usable.copy().reset_index(drop=True)
            results["duplicates"] = DuplicatesAnalyzer(confirmed_duplicate_frame, embeddings=embeddings).run()
            usable = confirmed_duplicate_frame
            try:
                results["diversity"] = DiversityAnalyzer(usable, embeddings).run()
            except Exception as exc:
                errors["diversity"] = f"{type(exc).__name__}: {exc}"
                results["diversity"] = {"status": "unavailable", "reason": str(exc)}
            labeled_positions = np.flatnonzero(usable["ground_truth_class"].notna().to_numpy())
            labeled_for_audit = usable.iloc[labeled_positions].copy().reset_index(drop=True)
            if len(labeled_for_audit) >= 2 and labeled_for_audit["ground_truth_class"].nunique() >= 2:
                try:
                    results["labels"] = LabelAuditAnalyzer(labeled_for_audit, embeddings[labeled_positions]).run()
                    for column in ("label_issue_prob", "flag_suspected_mislabel", "predicted_class"):
                        if column in labeled_for_audit:
                            usable.loc[labeled_positions, column] = labeled_for_audit[column].to_numpy()
                except Exception as exc:
                    errors["labels"] = f"{type(exc).__name__}: {exc}"
                    results["labels"] = {"status": "unavailable", "reason": str(exc)}
            else:
                results["labels"] = {"status": "unavailable", "reason": "At least two labelled classes with repeated samples are required."}
            embedding_dimensions = {"status": "available", "model": "ResNet18_Weights.IMAGENET1K_V1", "count": len(embeddings)}
            progress(75, "Measuring visual diversity and label signals")

            if estimate_attributes:
                from dia.analyzers.attribute_suggestions import AttributeSuggestionAnalyzer
                attribute_estimates = {
                    "status": "available",
                    **AttributeSuggestionAnalyzer(usable, embeddings).run(),
                }
                for suggestion in attribute_estimates.get("suggestions", []):
                    all_findings.append({
                        "code": "ATTRIBUTE_SUGGESTION_FOR_REVIEW",
                        "severity": "review",
                        **suggestion,
                    })

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
    if estimate_attributes and attribute_estimates["status"] == "not_requested":
        attribute_estimates = {
            "status": "unavailable",
            "reason": "Attribute suggestions require pretrained image features, which were unavailable for this run.",
        }

    try:
        confound_frame = usable.copy().reset_index(drop=True)
        for column in ("label_issue_prob", "flag_suspected_mislabel", "predicted_class"):
            if column in usable:
                confound_frame[column] = usable[column].to_numpy()
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
    if results.get("duplicates", {}).get("cross_split_duplicate_groups", 0):
        all_findings.append({
            "code": "CROSS_SPLIT_DUPLICATE_LEAKAGE", "severity": "critical",
            "count": results["duplicates"]["cross_split_duplicate_groups"],
            "description": "Near-duplicate image groups span multiple data splits and may leak evaluation examples into training.",
        })
    if results.get("duplicates", {}).get("conflicting_label_duplicate_groups", 0):
        all_findings.append({
            "code": "CONFLICTING_DUPLICATE_LABELS", "severity": "high",
            "count": results["duplicates"]["conflicting_label_duplicate_groups"],
            "description": "A near-duplicate group contains more than one supplied class label; review these labels.",
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
    results["readiness"] = ReadinessScorer().compute(results)
    results["bias_impact"] = BiasImpactPredictor(results).predict()
    results["recommendations"] = RecommendationEngine(results).generate()
    progress(95, "Saving report")

    sample_findings = []
    enriched = usable.set_index("sample_ref", drop=False) if "sample_ref" in usable else usable
    sample_results = []
    for _, row in df.iterrows():
        ref = str(row.get("sample_ref", row.get("id", "")))
        current = enriched.loc[ref] if ref in enriched.index else row
        metrics = {}
        for key, value in current.items():
            if key.startswith(("quality_", "flag_", "label_", "predicted_", "duplicate_", "phash", "cluster_", "metadata_source:", "attribute_confidence:")):
                metrics[key] = _clean(value)
        metrics = {
            key: _clean(value) for key, value in metrics.items()
        }
        metrics["is_valid"] = bool(row.get("is_valid", True))
        metrics["analysis_status"] = "invalid_image" if not bool(row.get("is_valid", True)) else "analyzed" if ref in enriched.index else "not_sampled"
        metrics["error_message"] = _clean(row.get("error_message"))
        metrics["flag_invalid_image"] = not bool(row.get("is_valid", True))
        metrics["anomaly_flags"] = _clean(row.get("anomaly_flags", []))
        metrics["attribute_suggestions"] = [
            {key: value for key, value in suggestion.items() if key != "sample_ref"}
            for suggestion in attribute_estimates.get("suggestions", [])
            if suggestion.get("sample_ref") == ref
        ]
        sample_results.append({
            "sample_ref": ref,
            "metrics": metrics,
        })
    for ref, row in enriched.iterrows():
        details = sample_enrichment.get(str(ref), {})
        flags = [key for key in ("flag_blurred", "flag_underexposed", "flag_overexposed", "flag_low_contrast", "flag_low_resolution", "flag_duplicate", "flag_suspected_mislabel") if bool(row.get(key, False))]
        if row.get("anomaly_flags"):
            flags.extend(f"flag_{value}" for value in row.get("anomaly_flags", []))
        if flags or details.get("flag_suspected_mislabel"):
            sample_findings.append({
                "sample_ref": str(ref),
                "ground_truth_class": _clean(row.get("ground_truth_class")),
                "flags": flags,
                "predicted_class": details.get("predicted_class", _clean(row.get("predicted_class"))),
                "label_issue_prob": details.get("label_issue_prob", _clean(row.get("label_issue_prob"))),
                "duplicate_group": _clean(row.get("duplicate_group")),
            })

    report = _clean({
        "report_version": "dia-report-v2",
        "analyzer_versions": {"core": "2.0.0", "readiness": ReadinessScorer.VERSION,
                              "runtime_libraries": _runtime_versions()},
        "model_versions": {
            "embedding": embedding_dimensions.get("model"),
            "attribute_suggestions": "dataset-conditioned logistic regression (trained per run)" if attribute_estimates.get("status") == "available" else None,
            "filename_attributes": "utkface-filename-parser-v1",
        },
        "sample_count": len(df),
        "readable_sample_count": len(all_usable),
        "analyzed_sample_count": len(usable),
        "sampling": {"requested_rate": float(sampling_rate), "actual_rate": len(usable) / len(all_usable) if len(all_usable) else 0.0,
                     "seed": int(sampling_seed), "strategy": "deterministic_stratified_by_class_and_split"},
        "dataset_fingerprint": dataset_fingerprint or hashlib.sha256("\n".join(sorted(str(v) for v in df.get("sample_ref", []))).encode()).hexdigest(),
        "metadata_provenance": provenance_summary,
        "disclaimer": "This report describes dataset-level evidence and review signals. It does not prove that a dataset or model is fair. Demographic attributes parsed from filenames or suggested from images may be inaccurate and should be reviewed; do not use them to make decisions about individuals.",
        "embedding_analysis": embedding_dimensions,
        "results": results,
        "attribute_estimates": attribute_estimates,
        "findings": all_findings,
        "sample_findings": sample_findings,
        "sample_results": sample_results,
        "warnings": warnings or [],
        "analyzer_errors": errors,
    })
    progress(100, "Analysis complete")
    return report
