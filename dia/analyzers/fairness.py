"""Descriptive, target-aware group representation audit."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency


def _wilson_interval(successes: int, total: int) -> tuple[float, float] | None:
    if total <= 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


class FairnessAnalyzer:
    """Summarize group representation and compare it with optional user targets."""

    def __init__(self, df: pd.DataFrame, targets: dict[str, dict[str, float]] | None = None,
                 class_targets: dict[str, dict[str, dict[str, float]]] | None = None,
                 gap_threshold: float = 0.10, minimum_group_size: int = 20):
        self.df = df
        self.targets = targets or {}
        self.class_targets = class_targets or {}
        self.gap_threshold = gap_threshold
        self.minimum_group_size = minimum_group_size

    def run(self) -> dict[str, Any]:
        reserved = {
            "id", "sample_id", "path", "file_path", "sample_ref", "ground_truth_class",
            "split", "is_valid", "content_sha256", "error_message", "name", "description",
            "anomaly_flags", "inferred_attributes", "attributes",
        }
        attributes = sorted(
            column for column in self.df.columns
            if column not in reserved
            and not column.startswith(("quality_", "flag_", "label_", "predicted_", "duplicate_", "embedding_", "metadata_source:", "attribute_confidence:"))
            and not self.df[column].apply(lambda x: isinstance(x, (list, dict, set))).any()
        )
        overall: dict[str, Any] = {}
        by_class: dict[str, Any] = {}
        findings: list[dict[str, Any]] = []
        all_gaps: list[float] = []
        class_associations: dict[str, Any] = {}
        class_group_parity: dict[str, Any] = {}
        intersectional: dict[str, Any] = {}
        for attribute in attributes:
            values = self.df[attribute]
            observed = values.dropna().astype(str)
            counts = observed.value_counts().to_dict()
            total = len(observed)
            target = self._validate_target(attribute, self.targets.get(attribute))
            overall[attribute] = self._summary(counts, total, target, int(values.isna().sum()))
            if target:
                all_gaps.extend(abs(counts.get(value, 0) / total - expected) for value, expected in target.items() if total)
                findings.extend(self._find_gaps(attribute, counts, total, target, scope="overall"))

            if "ground_truth_class" in self.df.columns:
                for label, group in self.df.groupby("ground_truth_class", dropna=True):
                    vals = group[attribute].dropna().astype(str)
                    group_counts = vals.value_counts().to_dict()
                    class_target = self._validate_target(attribute, self.class_targets.get(str(label), {}).get(attribute))
                    by_class.setdefault(str(label), {})[attribute] = self._summary(group_counts, len(vals), class_target, int(group[attribute].isna().sum()))
                    if class_target:
                        all_gaps.extend(abs(group_counts.get(value, 0) / len(vals) - expected) for value, expected in class_target.items() if len(vals))
                        findings.extend(self._find_gaps(attribute, group_counts, len(vals), class_target, scope=f"class:{label}"))
                table = pd.crosstab(self.df[attribute], self.df["ground_truth_class"]).astype(int)
                if table.shape[0] > 1 and table.shape[1] > 1:
                    chi2, p_value, _, _ = chi2_contingency(table, correction=False)
                    n = int(table.to_numpy().sum())
                    denominator = max(1, min(table.shape[0] - 1, table.shape[1] - 1))
                    class_associations[attribute] = {
                        "chi_square": float(chi2), "p_value": float(p_value),
                        "cramers_v": float((chi2 / (n * denominator)) ** 0.5) if n else None,
                        "sample_count": n,
                    }
                    row_totals = table.sum(axis=1).replace(0, np.nan)
                    rates = table.div(row_totals, axis=0)
                    class_group_parity[attribute] = {}
                    for label in table.columns:
                        group_rates = rates[label].dropna()
                        min_rate = float(group_rates.min()) if len(group_rates) else None
                        max_rate = float(group_rates.max()) if len(group_rates) else None
                        class_group_parity[attribute][str(label)] = {
                            "group_class_rates": {str(group): float(value) for group, value in group_rates.items()},
                            "demographic_parity_difference": max_rate - min_rate if min_rate is not None else None,
                            "disparate_impact_ratio": min_rate / max_rate if min_rate is not None and max_rate else None,
                            "low_support_groups": [str(group) for group in table.index if table.loc[group].sum() < self.minimum_group_size],
                            "sample_count": int(table[label].sum()),
                            "interpretation": "Dataset class representation proxy; this is not a model-output fairness metric.",
                        }
        available_attributes = [a for a in attributes if self.df[a].nunique(dropna=True) <= 20]
        if len(available_attributes) >= 2:
            combo = self.df[available_attributes].fillna("<missing>").astype(str).agg(" × ".join, axis=1)
            combo_counts = combo.value_counts()
            intersectional = {
                "attribute_names": available_attributes,
                "combination_count": int(len(combo_counts)),
                "low_coverage_combinations": [
                    {"combination": str(key), "count": int(value)}
                    for key, value in combo_counts[combo_counts < self.minimum_group_size].head(100).items()
                ],
                "minimum_group_size": self.minimum_group_size,
            }
        split_skew = self._split_skew(attributes)
        return {
            "targets_provided": bool(self.targets or self.class_targets),
            "attributes": overall,
            "by_class": by_class,
            "findings": findings,
            "worst_absolute_target_gap": round(max(all_gaps), 6) if all_gaps else None,
            "class_associations": class_associations,
            "class_group_parity": class_group_parity,
            "intersectional_coverage": intersectional,
            "split_skew": split_skew,
        }

    def _split_skew(self, attributes: list[str]) -> dict[str, Any]:
        if "split" not in self.df or self.df["split"].nunique(dropna=True) < 2:
            return {"status": "unavailable", "reason": "At least two named splits are required."}
        label_columns = [c for c in ("ground_truth_class", *attributes) if c in self.df and self.df[c].nunique(dropna=True) <= 50]
        comparisons = {}
        for column in label_columns:
            distributions = {}
            all_values = sorted(self.df[column].dropna().astype(str).unique())
            if len(all_values) < 2:
                continue
            for split, group in self.df.groupby("split", dropna=True):
                counts = group[column].dropna().astype(str).value_counts().reindex(all_values, fill_value=0)
                if counts.sum():
                    distributions[str(split)] = (counts / counts.sum()).to_numpy(dtype=float)
            if len(distributions) < 2:
                continue
            names = sorted(distributions)
            divergences = []
            for i, left in enumerate(names):
                for right in names[i + 1:]:
                    p, q = distributions[left], distributions[right]
                    midpoint = (p + q) / 2
                    def kl(x):
                        mask = x > 0
                        return float((x[mask] * np.log2(x[mask] / midpoint[mask])).sum())
                    divergences.append({"split_a": left, "split_b": right, "js_divergence": 0.5 * (kl(p) + kl(q))})
            comparisons[column] = {"comparisons": divergences, "threshold": 0.1,
                                   "flagged": any(item["js_divergence"] > 0.1 for item in divergences)}
        return {"status": "available" if comparisons else "unavailable", "dimensions": comparisons}

    @staticmethod
    def _validate_target(attribute: str, target: dict[str, float] | None) -> dict[str, float] | None:
        if target is None:
            return None
        target = {str(k): float(v) for k, v in target.items()}
        if not target or any(v < 0 or v > 1 for v in target.values()) or not 0.999 <= sum(target.values()) <= 1.001:
            raise ValueError(f"Fairness target for '{attribute}' must contain proportions that sum to 1.")
        return target

    @staticmethod
    def _summary(counts: dict[str, int], total: int, target: dict[str, float] | None, missing_count: int = 0) -> dict[str, Any]:
        groups = {}
        for value in sorted(set(counts) | set(target or {})):
            count = int(counts.get(value, 0))
            interval = _wilson_interval(count, total)
            groups[value] = {
                "count": count,
                "proportion": count / total if total else None,
                "target_proportion": (target or {}).get(value),
                "confidence_95": list(interval) if interval else None,
                "target_gap_percentage_points": (
                    100 * (count / total - target[value]) if total and target and value in target else None
                ),
                "low_support": count < 20,
            }
        return {"sample_count": total, "missing_count": missing_count, "groups": groups}

    def _find_gaps(self, attribute: str, counts: dict[str, int], total: int,
                   target: dict[str, float], scope: str) -> list[dict[str, Any]]:
        results = []
        for value, expected in target.items():
            count = int(counts.get(value, 0))
            observed = count / total if total else 0.0
            gap = observed - expected
            if abs(gap) >= self.gap_threshold:
                results.append({
                    "code": "GROUP_REPRESENTATION_GAP",
                    "severity": "review" if count < self.minimum_group_size else "warning",
                    "attribute": attribute,
                    "group": value,
                    "scope": scope,
                    "count": count,
                    "sample_count": total,
                    "observed_proportion": observed,
                    "target_proportion": expected,
                    "gap_percentage_points": round(100 * gap, 2),
                    "description": f"Observed representation of '{value}' differs from the supplied target in {scope}.",
                })
        return results
