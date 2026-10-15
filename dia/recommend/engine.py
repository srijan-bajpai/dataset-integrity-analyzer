"""Prioritised, interaction-aware remediation recommendation engine (REQ-81..88)."""

from __future__ import annotations

import copy
from typing import Any

import pandas as pd

from dia.scoring.readiness import ReadinessScorer


class RecommendationEngine:
    """
    Translates findings into ranked, cost-aware, interaction-aware recommendations.
    Computes projected readiness score gains using the actual ReadinessScorer.
    Generates sample-level remediation manifests for automated execution.
    (REQ-81, REQ-82, REQ-83, REQ-84, REQ-85, REQ-86, REQ-87, REQ-88)
    """

    EFFORT_MAP = {
        "Low": 1.0,
        "Medium": 2.0,
        "High": 3.0,
    }

    def __init__(self, agg_results: dict[str, Any], df: pd.DataFrame | None = None):
        self.agg = agg_results
        self.df = df
        self.scorer = ReadinessScorer()
        self.baseline_readiness = self.agg.get("readiness") or self.scorer.compute(self.agg)
        self.baseline_score = float(self.baseline_readiness.get("overall_score") or 0.0)

    def _simulated_gain(self, patch: dict[str, dict[str, Any]]) -> float:
        """Estimate readiness score gain if a specific defect is resolved."""
        cloned = copy.deepcopy(self.agg)
        for section, values in patch.items():
            cloned.setdefault(section, {}).update(values)
        new_res = self.scorer.compute(cloned)
        new_score = float(new_res.get("overall_score") or 0.0)
        return max(0.0, round(new_score - self.baseline_score, 1))

    def generate(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

        # Check detected cross-dimensional confounds for interaction-aware guidance (REQ-84)
        confounds = self.agg.get("confounds", {}).get("detected_confounds", [])
        has_quality_class_confound = any(c.get("code") == "QUALITY_CLASS_CONFOUND" for c in confounds)
        has_diversity_class_confound = any(c.get("code") == "DIVERSITY_CLASS_CONFOUND" for c in confounds)
        has_leakage_confound = any(c.get("code") == "LEAKAGE_CLASS_CONFOUND" for c in confounds)
        has_label_noise_confound = any(c.get("code") == "LABEL_NOISE_CLASS_CONFOUND" for c in confounds)

        # 1. Cross-Split Duplicate Leakage (REQ-37, REQ-81)
        duplicates = self.agg.get("duplicates", {})
        cross_split_groups = int(duplicates.get("cross_split_duplicate_groups", 0) or 0)
        if cross_split_groups > 0:
            gain = self._simulated_gain({"duplicates": {"cross_split_duplicate_groups": 0}})
            leak_samples = int(duplicates.get("near_duplicate_count", 0))
            candidates.append({
                "category": "Data Leakage",
                "action_type": "RESPLIT_LEAKAGE",
                "priority": "Critical",
                "defect": f"{cross_split_groups} duplicate group(s) cross train/val/test splits.",
                "affected_sample_count": leak_samples,
                "projected_score_gain": gain,
                "estimated_effort": "Low",
                "machine_actionable": True,
                "rationale": "Cross-split duplicates invalidate test set integrity and falsely inflate evaluation accuracy.",
                "action": "Re-split the dataset to ensure identical or near-duplicate images reside strictly in the same split (move test duplicates to train, or vice versa).",
                "trade_off_risk": "Moving evaluation samples to train may slightly change split proportions.",
            })

        # 2. General Near/Exact Duplicates (REQ-81)
        near_dups = int(duplicates.get("near_duplicate_count", 0) or 0)
        exact_dups = int(duplicates.get("exact_duplicate_count", 0) or 0)
        if near_dups > 0 and cross_split_groups == 0:
            gain = self._simulated_gain({"duplicates": {"redundancy_ratio": 0.0}})
            candidates.append({
                "category": "Duplicates",
                "action_type": "REMOVE_DUPLICATE",
                "priority": "High" if near_dups > 10 else "Medium",
                "defect": f"{near_dups} redundant image(s) ({exact_dups} exact byte matches).",
                "affected_sample_count": near_dups,
                "projected_score_gain": gain,
                "estimated_effort": "Low",
                "machine_actionable": True,
                "rationale": "Redundant images waste compute and skew frequency priors.",
                "action": "Remove redundant duplicate images while preserving one exemplar sample per duplicate group.",
                "trade_off_risk": "Deduplication reduces total dataset count; ensure minority classes retain sufficient samples.",
            })

        # 3. Label Noise / Suspected Mislabels (REQ-48..50, REQ-81)
        labels = self.agg.get("labels", {})
        mislabel_count = int(labels.get("suspected_count", 0) or 0)
        if mislabel_count > 0:
            gain = self._simulated_gain({"labels": {"label_noise_rate_pct": 0.0}})
            candidates.append({
                "category": "Label Integrity",
                "action_type": "RELABEL_SUSPECTED",
                "priority": "High" if has_label_noise_confound or mislabel_count > 10 else "Medium",
                "defect": f"{mislabel_count} sample(s) flagged with probable label disagreements via confident learning.",
                "affected_sample_count": mislabel_count,
                "projected_score_gain": gain,
                "estimated_effort": "Medium",
                "machine_actionable": True,
                "rationale": "Models trained on corrupted class labels suffer lower generalization accuracy and test noise.",
                "action": "Re-annotate the top-ranked suspected mislabels surfaced by confident learning, verifying annotations with domain experts.",
                "trade_off_risk": "Manual re-annotation requires human verification time.",
            })

        # 4. Class Imbalance (REQ-17, REQ-22, REQ-81, REQ-84, REQ-85)
        dist = self.agg.get("distribution", {})
        ir = dist.get("imbalance_ratio")
        counts = dist.get("class_counts", {})
        if ir is not None and ir > 1.5:
            gain = self._simulated_gain({"distribution": {"imbalance_ratio": 1.0}})
            maj_count = max(counts.values()) if counts else 0
            min_count = min(counts.values()) if counts else 0
            min_class = min(counts, key=counts.get) if counts else "minority"
            needed_samples = max(0, int(round(maj_count / 3.0)) - min_count)

            # REQ-84: Interaction-aware remediation when minority class also has low quality or low diversity!
            if has_quality_class_confound or has_diversity_class_confound:
                candidates.append({
                    "category": "Class Balance & Confound Interaction",
                    "action_type": "TARGETED_COLLECTION_INTERACTION_AWARE",
                    "priority": "High",
                    "defect": f"Class imbalance ratio is {ir:.2f}:1, compounding with lower image quality or visual diversity on minority classes.",
                    "affected_sample_count": min_count,
                    "projected_score_gain": gain,
                    "estimated_effort": "High",
                    "machine_actionable": False,
                    "rationale": "Minority classes exhibit correlated defects; naive oversampling would merely amplify degraded or duplicate images.",
                    "action": f"Do NOT simply oversample '{min_class}'. Instead, conduct targeted collection of ≈ {needed_samples} new, high-quality, diverse samples to bring the Imbalance Ratio below 3.0:1.",
                    "trade_off_risk": "Requires acquiring new external imagery rather than algorithmic re-sampling.",
                })
            else:
                candidates.append({
                    "category": "Class Balance",
                    "action_type": "BALANCE_CLASSES",
                    "priority": "High" if ir > 5.0 else "Medium",
                    "defect": f"Imbalance ratio is {ir:.2f}:1 between majority and minority classes.",
                    "affected_sample_count": maj_count - min_count,
                    "projected_score_gain": gain,
                    "estimated_effort": "Medium",
                    "machine_actionable": False,
                    "rationale": "High class imbalance leads classifiers to predict majority classes and ignore minority classes.",
                    "action": f"Apply class-weighted loss during training or collect ≈ {needed_samples} additional samples for '{min_class}' to lower the imbalance ratio below 3.0:1.",
                    "trade_off_risk": "Undersampling the majority class would discard valuable data; prefer class weighting or data augmentation.",
                })

        # 5. Image Quality Defects (REQ-27, REQ-81)
        quality = self.agg.get("quality", {})
        defect_rate = quality.get("defect_rate_pct", 0) or 0
        if defect_rate >= 5.0:
            gain = self._simulated_gain({"quality": {"defect_rate_pct": 0.0}})
            flags = ["flag_blurred", "flag_underexposed", "flag_overexposed", "flag_low_contrast", "flag_low_resolution"]
            sample_count = int(quality.get("sample_count", 0))
            affected_q = max(1, int(round(sample_count * defect_rate / 100.0)))
            candidates.append({
                "category": "Image Quality",
                "action_type": "RECAPTURE_OR_AUGMENT_QUALITY",
                "priority": "Medium",
                "defect": f"{defect_rate:.1f}% of images failed quality thresholds (blur, exposure, contrast, or resolution).",
                "affected_sample_count": affected_q,
                "projected_score_gain": gain,
                "estimated_effort": "Medium",
                "machine_actionable": True,
                "rationale": "Degraded images cause neural networks to learn noisy artifacts and struggle on clean evaluation images.",
                "action": "Filter severely degraded images (e.g. extreme blur or zero contrast) and apply targeted photometric augmentation (brightness/contrast adjustments) for exposure bias.",
                "trade_off_risk": "Filtering low-quality images reduces dataset size; verify whether low-quality images represent realistic deployment conditions.",
            })

        # 6. Group Representation / Fairness Gaps (REQ-13, REQ-81, REQ-85)
        fairness = self.agg.get("fairness", {})
        worst_gap = fairness.get("worst_absolute_target_gap")
        if worst_gap is not None and worst_gap > 0.05:
            gain = self._simulated_gain({"fairness": {"worst_absolute_target_gap": 0.0}})
            findings = fairness.get("findings", [])
            gap_attr = findings[0].get("attribute", "group") if findings else "group"
            candidates.append({
                "category": "Group Representation",
                "action_type": "COLLECT_UNDERREPRESENTED_GROUP",
                "priority": "High" if worst_gap > 0.20 else "Medium",
                "defect": f"Representation gap of {worst_gap:.1%} observed against specified target distribution on '{gap_attr}'.",
                "affected_sample_count": int(round(worst_gap * (self.agg.get("sample_count") or 100))),
                "projected_score_gain": gain,
                "estimated_effort": "High",
                "machine_actionable": False,
                "rationale": "Severe demographic disparity leads models to exhibit disparate impact and accuracy gaps across protected groups.",
                "action": f"Collect additional samples for under-represented sub-groups in '{gap_attr}' to reach target parity before model training.",
                "trade_off_risk": "Target collection must reflect operational population distributions.",
            })

        # 7. Redundant Embedding Clusters (REQ-44, REQ-81)
        diversity = self.agg.get("diversity", {})
        prunable = int(diversity.get("total_prunable_samples", 0) or 0)
        if prunable > 0:
            candidates.append({
                "category": "Visual Diversity",
                "action_type": "PRUNE_REDUNDANT_CLUSTERS",
                "priority": "Low",
                "defect": f"{prunable} visually redundant samples identified in tight embedding clusters (cosine similarity >= 0.95).",
                "affected_sample_count": prunable,
                "projected_score_gain": 1.5,
                "estimated_effort": "Low",
                "machine_actionable": True,
                "rationale": "High visual redundancy within clusters increases training time without providing new semantic variation.",
                "action": "Prune redundant samples in tight clusters while preserving at least two exemplar samples per cluster.",
                "trade_off_risk": "Pruning reduces raw sample count.",
            })

        # 8. REQ-88: Conflict resolution & Contradiction avoidance
        # If dataset is small (< 200 samples), warn against undersampling and advocate class weighting
        total_samples = int(self.agg.get("sample_count", 0))
        for cand in candidates:
            if cand["action_type"] == "BALANCE_CLASSES" and total_samples < 300:
                cand["action"] = "Apply class-weighted loss (or focal loss) during model training. Avoid undersampling the majority class as the dataset has limited total sample count."
                cand["trade_off_risk"] = "Undersampling would remove critical training data from an already small dataset."

        # 9. REQ-83: Rank by projected gain per unit effort
        for cand in candidates:
            cost = self.EFFORT_MAP.get(cand["estimated_effort"], 2.0)
            cand["gain_per_effort"] = round(cand["projected_score_gain"] / cost, 2)

        candidates.sort(key=lambda c: (-c["gain_per_effort"], -c["projected_score_gain"]))

        # Mark top 3 as "Do these first"
        for i, cand in enumerate(candidates):
            cand["do_first"] = (i < 3)
            cand["rank"] = i + 1

        if not candidates:
            candidates.append({
                "rank": 1,
                "category": "Review",
                "action_type": "NO_ACTION_REQUIRED",
                "priority": "Info",
                "defect": "No severe integrity defects or threshold violations detected.",
                "affected_sample_count": 0,
                "projected_score_gain": 0.0,
                "estimated_effort": "Low",
                "gain_per_effort": 0.0,
                "do_first": False,
                "machine_actionable": False,
                "rationale": "The dataset satisfies configured health thresholds across evaluated dimensions.",
                "action": "Review sample coverage and unmeasured dimensions before certifying model production readiness.",
                "trade_off_risk": "None",
            })

        return candidates

    def generate_manifest(self) -> list[dict[str, Any]]:
        """
        Generate machine-actionable per-sample remediation actions (REQ-86).
        Returns a list of dicts suitable for CSV export or programmatic execution.
        """
        manifest: list[dict[str, Any]] = []
        sample_results = self.agg.get("sample_results", [])
        if not sample_results and self.df is not None:
            # Fallback to df
            records = self.df.to_dict(orient="records")
        else:
            records = sample_results

        # Track which duplicates to keep vs drop
        seen_duplicate_groups: set[int] = set()

        for row in records:
            metrics = row.get("metrics", row)
            ref = str(row.get("sample_ref", row.get("id", "")))
            ground_truth = str(row.get("ground_truth_class", metrics.get("ground_truth_class", "")))

            # A. Invalid or corrupt files
            if not metrics.get("is_valid", True) or metrics.get("flag_invalid_image"):
                manifest.append({
                    "sample_ref": ref,
                    "action": "REMOVE_CORRUPT",
                    "target_dimension": "Quality",
                    "reason": metrics.get("error_message") or "Unreadable or corrupt image file",
                    "current_label": ground_truth,
                    "suggested_value": "delete_sample",
                })
                continue

            # B. Duplicates
            dup_group = metrics.get("duplicate_group")
            if dup_group is not None and pd.notna(dup_group):
                gid = int(dup_group)
                if gid in seen_duplicate_groups:
                    manifest.append({
                        "sample_ref": ref,
                        "action": "REMOVE_DUPLICATE",
                        "target_dimension": "Uniqueness",
                        "reason": f"Redundant image belonging to duplicate group {gid}",
                        "current_label": ground_truth,
                        "suggested_value": "drop_duplicate",
                    })
                else:
                    seen_duplicate_groups.add(gid)

            # C. Suspected Mislabels from Confident Learning
            if metrics.get("flag_suspected_mislabel"):
                pred_c = metrics.get("predicted_class", "unknown")
                prob = metrics.get("label_issue_prob", 0.0)
                manifest.append({
                    "sample_ref": ref,
                    "action": "RELABEL_SAMPLE",
                    "target_dimension": "Label Integrity",
                    "reason": f"Confident learning disagreement (margin {prob:.2f})",
                    "current_label": ground_truth,
                    "suggested_value": str(pred_c),
                })

            # D. Severe Quality Defects
            severe_quality = []
            if metrics.get("quality_blur") is not None and float(metrics["quality_blur"]) < 30.0:
                severe_quality.append("extreme_blur")
            if metrics.get("flag_low_resolution"):
                severe_quality.append("under_resolution")
            if severe_quality:
                manifest.append({
                    "sample_ref": ref,
                    "action": "RECAPTURE_OR_FILTER",
                    "target_dimension": "Quality",
                    "reason": f"Severe image defects: {', '.join(severe_quality)}",
                    "current_label": ground_truth,
                    "suggested_value": "review_and_replace",
                })

        return manifest
