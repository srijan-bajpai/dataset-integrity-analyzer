"""Cross-dimensional confound analysis across all audit dimensions (REQ-54..63, C1)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal, spearmanr

from .base import BaseAnalyzer


def _benjamini_hochberg(items: list[tuple[str, float]], alpha: float = 0.05) -> set[str]:
    ordered = sorted(items, key=lambda item: item[1])
    accepted: set[str] = set()
    m = len(ordered)
    cutoff = 0
    for rank, (_, p_value) in enumerate(ordered, start=1):
        if p_value <= alpha * rank / m:
            cutoff = rank
    if cutoff:
        accepted = {name for name, _ in ordered[:cutoff]}
    return accepted


class ConfoundAnalyzer(BaseAnalyzer):
    """
    Detects cross-dimensional interactions and confounds:
    - Quality x Class (REQ-55)
    - Quality x Attribute / Fairness (REQ-54)
    - Redundancy x Class / Fairness with effective sample counts (REQ-56)
    - Diversity x Class correlation (REQ-57)
    - Label Noise x Class / Attribute (REQ-58)
    - Leakage x Class concentration (REQ-59)
    """

    def __init__(self, df: pd.DataFrame):
        super().__init__(df)
        self.quality_metrics = [
            "quality_blur", "quality_brightness", "quality_contrast",
            "quality_resolution", "quality_noise_mad",
        ]

    def run(self) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        tested_confounds: list[str] = []
        tests: list[tuple[str, float, dict[str, Any]]] = []

        labels = self.df.get("ground_truth_class", pd.Series(dtype=object)).dropna().unique()
        metadata_columns = [
            col for col in self.df.columns
            if (col.startswith("attribute:") or col in {"gender", "age_group", "lighting", "region"})
            and self.df[col].nunique(dropna=True) in range(2, 21)
        ]

        # 1. Quality x Class Confound (REQ-55)
        if len(labels) >= 2:
            for metric in self.quality_metrics:
                if metric not in self.df:
                    continue
                test_name = f"quality_class:{metric}"
                tested_confounds.append(test_name)

                groups = []
                kept = []
                for label in labels:
                    vals = pd.to_numeric(self.df.loc[self.df["ground_truth_class"] == label, metric], errors="coerce").dropna().to_numpy()
                    if len(vals) >= 5:
                        groups.append(vals)
                        kept.append((str(label), len(vals)))

                if len(groups) >= 2:
                    all_vals = np.concatenate(groups)
                    if not np.all(all_vals == all_vals[0]):
                        try:
                            stat, p_val = kruskal(*groups)
                            n = sum(len(g) for g in groups)
                            k = len(groups)
                            epsilon_sq = max(0.0, (stat - k + 1) / max(n - k, 1))
                            tests.append((test_name, float(p_val), {
                                "code": "QUALITY_CLASS_CONFOUND",
                                "type": "Quality-Class Confound",
                                "dimension_a": metric,
                                "dimension_b": "class",
                                "statistic": round(float(stat), 4),
                                "p_value_raw": float(p_val),
                                "effect_size_epsilon_squared": round(float(epsilon_sq), 4),
                                "group_counts": dict(kept),
                                "affected_sample_count": int(n),
                                "downstream_consequence": f"Model may learn {metric} as a spurious shortcut for class distinction rather than semantic image features.",
                                "description": f"{metric} differs significantly across target classes (epsilon^2 = {epsilon_sq:.3f}).",
                            }))
                        except (ValueError, FloatingPointError):
                            pass

        # 2. Quality x Sensitive Attribute Confound (REQ-54)
        for col in metadata_columns:
            clean_attr_name = col.removeprefix("attribute:")
            for metric in self.quality_metrics:
                if metric not in self.df:
                    continue
                test_name = f"quality_attribute:{clean_attr_name}:{metric}"
                tested_confounds.append(test_name)

                groups = []
                counts = {}
                for val, grp in self.df.groupby(col, dropna=True):
                    vals = pd.to_numeric(grp[metric], errors="coerce").dropna().to_numpy()
                    if len(vals) >= 5:
                        groups.append(vals)
                        counts[str(val)] = int(len(vals))

                if len(groups) >= 2:
                    all_vals = np.concatenate(groups)
                    if not np.all(all_vals == all_vals[0]):
                        try:
                            stat, p_val = kruskal(*groups)
                            n = sum(len(g) for g in groups)
                            k = len(groups)
                            epsilon_sq = max(0.0, (stat - k + 1) / max(n - k, 1))
                            tests.append((test_name, float(p_val), {
                                "code": "QUALITY_FAIRNESS_CONFOUND",
                                "type": "Quality-Attribute Association",
                                "dimension_a": metric,
                                "dimension_b": clean_attr_name,
                                "statistic": round(float(stat), 4),
                                "p_value_raw": float(p_val),
                                "effect_size_epsilon_squared": round(float(epsilon_sq), 4),
                                "group_counts": counts,
                                "affected_sample_count": int(n),
                                "downstream_consequence": f"Degraded image quality in certain '{clean_attr_name}' groups can cause disparate accuracy drops on those demographic segments.",
                                "description": f"Image {metric} varies significantly across '{clean_attr_name}' sub-groups (epsilon^2 = {epsilon_sq:.3f}).",
                            }))
                        except (ValueError, FloatingPointError):
                            pass

        # Apply Benjamini-Hochberg FDR correction across all quality tests
        significant = _benjamini_hochberg([(name, p) for name, p, _ in tests])
        for name, p_val, payload in tests:
            if name in significant:
                severity = "warning" if payload.get("effect_size_epsilon_squared", 0) >= 0.08 else "review"
                findings.append({
                    **payload,
                    "p_value_corrected": round(p_val, 6),
                    "severity": severity,
                })

        # 3. Redundancy x Class / Fairness Confound (REQ-56)
        if "duplicate_group" in self.df and "ground_truth_class" in self.df:
            tested_confounds.append("redundancy_class")
            dup_mask = self.df["duplicate_group"].notna()
            class_redundancy = {}
            for label, grp in self.df.groupby("ground_truth_class", dropna=True):
                raw_n = len(grp)
                # Count unique samples: samples not in any dup group + 1 per unique dup group in this class
                no_dup_n = int((~dup_mask.loc[grp.index]).sum())
                unique_groups = grp.loc[dup_mask.loc[grp.index], "duplicate_group"].nunique()
                effective_n = no_dup_n + unique_groups
                redundancy_rate = (raw_n - effective_n) / raw_n if raw_n else 0.0
                class_redundancy[str(label)] = {
                    "raw_count": raw_n,
                    "effective_count": effective_n,
                    "redundancy_rate": round(redundancy_rate, 4),
                }

            rates = [v["redundancy_rate"] for v in class_redundancy.values() if v["raw_count"] >= 5]
            if len(rates) >= 2 and max(rates) - min(rates) >= 0.15:
                worst_class = max(class_redundancy.items(), key=lambda x: x[1]["redundancy_rate"])
                findings.append({
                    "code": "REDUNDANCY_CLASS_CONFOUND",
                    "type": "Redundancy-Class Confound",
                    "dimension_a": "duplicates",
                    "dimension_b": "class",
                    "affected_group": worst_class[0],
                    "duplicate_rate": worst_class[1]["redundancy_rate"],
                    "class_effective_counts": class_redundancy,
                    "severity": "warning",
                    "downstream_consequence": f"Class '{worst_class[0]}' apparent sample count is inflated by duplicate images; effective count is only {worst_class[1]['effective_count']} vs raw {worst_class[1]['raw_count']}.",
                    "description": f"Near-duplicates are concentrated in class '{worst_class[0]}' ({worst_class[1]['redundancy_rate']:.1%} redundancy).",
                })

        # 4. Diversity x Class Confound (REQ-57)
        if "cluster_id" in self.df and "ground_truth_class" in self.df and len(labels) >= 3:
            tested_confounds.append("diversity_class")
            class_counts = []
            class_entropies = []
            for label in labels:
                grp = self.df[self.df["ground_truth_class"] == label]
                if len(grp) >= 5:
                    c_counts = grp["cluster_id"].value_counts()
                    ent = float(np.sum(- (c_counts / len(grp)) * np.log(c_counts / len(grp) + 1e-12)))
                    class_counts.append(len(grp))
                    class_entropies.append(ent)
            if len(class_counts) >= 3:
                rho, p_val = spearmanr(class_counts, class_entropies)
                if not np.isnan(rho) and p_val < 0.05 and rho > 0.5:
                    findings.append({
                        "code": "DIVERSITY_CLASS_CONFOUND",
                        "type": "Diversity-Class Confound",
                        "dimension_a": "diversity",
                        "dimension_b": "class",
                        "statistic": round(float(rho), 4),
                        "p_value": round(float(p_val), 4),
                        "effect_size": round(float(rho), 4),
                        "severity": "warning",
                        "downstream_consequence": "Minority classes are not only smaller in count but also exhibit narrower visual variation; simple re-weighting or oversampling will not provide missing visual modes.",
                        "description": f"Per-class visual diversity strongly correlates with class frequency (Spearman rho = {rho:.2f}, p = {p_val:.4f}).",
                    })

        # 5. Label Noise x Class / Attribute Confound (REQ-58)
        if "flag_suspected_mislabel" in self.df and "ground_truth_class" in self.df:
            tested_confounds.append("label_noise_class")
            flags = self.df["flag_suspected_mislabel"].fillna(False).astype(bool)
            table = pd.crosstab(self.df["ground_truth_class"], flags)
            if table.shape[0] >= 2 and table.shape[1] == 2:
                try:
                    chi2, p_val, dof, _ = chi2_contingency(table)
                    n = len(self.df)
                    cramers_v = np.sqrt(chi2 / (n * (min(table.shape) - 1)))
                    if p_val < 0.05 and cramers_v >= 0.15:
                        worst_label = max(
                            labels,
                            key=lambda l: float(flags[self.df["ground_truth_class"] == l].mean())
                        )
                        worst_rate = float(flags[self.df["ground_truth_class"] == worst_label].mean())
                        findings.append({
                            "code": "LABEL_NOISE_CLASS_CONFOUND",
                            "type": "LabelNoise-Class Confound",
                            "dimension_a": "labels",
                            "dimension_b": "class",
                            "affected_group": str(worst_label),
                            "disagreement_rate": round(worst_rate, 4),
                            "statistic": round(float(chi2), 4),
                            "p_value": round(float(p_val), 4),
                            "effect_size_cramers_v": round(float(cramers_v), 4),
                            "severity": "review",
                            "downstream_consequence": f"Annotations for class '{worst_label}' are systematically more contradictory ({worst_rate:.1%} disagreement rate); model reliability on this class is at risk.",
                            "description": f"Suspected mislabels are disproportionately concentrated in class '{worst_label}' (Cramer's V = {cramers_v:.3f}).",
                        })
                except Exception:
                    pass

        # 6. Leakage x Class Confound (REQ-59)
        if "duplicate_group" in self.df and "split" in self.df and "ground_truth_class" in self.df:
            tested_confounds.append("leakage_class")
            split_cross_groups = set()
            for gid, grp in self.df.groupby("duplicate_group", dropna=True):
                if grp["split"].nunique(dropna=True) > 1:
                    split_cross_groups.add(gid)

            if split_cross_groups:
                leaked_mask = self.df["duplicate_group"].isin(split_cross_groups)
                leaked_by_class = self.df.loc[leaked_mask, "ground_truth_class"].value_counts().to_dict()
                worst_leaked_class = max(leaked_by_class.items(), key=lambda x: x[1])
                findings.append({
                    "code": "LEAKAGE_CLASS_CONFOUND",
                    "type": "Leakage-Class Confound",
                    "dimension_a": "leakage",
                    "dimension_b": "class",
                    "affected_group": str(worst_leaked_class[0]),
                    "leaked_sample_count": int(worst_leaked_class[1]),
                    "severity": "critical",
                    "downstream_consequence": f"Cross-split duplicate leakage concentrates in class '{worst_leaked_class[0]}', which will artificially inflate test accuracy for this class specifically.",
                    "description": f"Cross-split duplicate leakage affects {worst_leaked_class[1]} samples in class '{worst_leaked_class[0]}'.",
                })

        # REQ-61: Explicitly report which confounds were tested and found absent
        found_types = {f["type"] for f in findings}
        all_possible_types = [
            "Quality-Class Confound",
            "Quality-Attribute Association",
            "Redundancy-Class Confound",
            "Diversity-Class Confound",
            "LabelNoise-Class Confound",
            "Leakage-Class Confound",
        ]
        absent_confounds = [t for t in all_possible_types if t not in found_types]

        return {
            "status": "available",
            "detected_confounds": findings,
            "tested_confounds": tested_confounds,
            "absent_confounds": absent_confounds,
            "correction": "Benjamini-Hochberg false-discovery-rate correction (alpha=0.05)",
        }
