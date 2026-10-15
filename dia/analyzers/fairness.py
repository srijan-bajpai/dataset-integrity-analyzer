"""Descriptive, target-aware group representation audit."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd


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
                 gap_threshold: float = 0.10, minimum_group_size: int = 20):
        self.df = df
        self.targets = targets or {}
        self.gap_threshold = gap_threshold
        self.minimum_group_size = minimum_group_size

    def run(self) -> dict[str, Any]:
        reserved = {"sample_id", "path", "sample_ref", "ground_truth_class", "split", "is_valid"}
        attributes = sorted(
            column for column in self.df.columns
            if column not in reserved and not column.startswith(("quality_", "flag_", "label_", "predicted_", "duplicate_", "embedding_"))
        )
        overall: dict[str, Any] = {}
        by_class: dict[str, Any] = {}
        findings: list[dict[str, Any]] = []
        for attribute in attributes:
            values = self.df[attribute]
            observed = values.dropna().astype(str)
            counts = observed.value_counts().to_dict()
            total = len(observed)
            target = self.targets.get(attribute)
            target_sums_to_one = False
            if target is not None:
                target = {str(k): float(v) for k, v in target.items()}
                if any(v < 0 or v > 1 for v in target.values()) or not 0.999 <= sum(target.values()) <= 1.001:
                    raise ValueError(f"Fairness target for '{attribute}' must contain proportions that sum to 1.")
                target_sums_to_one = True
            overall[attribute] = self._summary(counts, total, target)
            if target_sums_to_one:
                findings.extend(self._find_gaps(attribute, counts, total, target, scope="overall"))

            if "ground_truth_class" in self.df.columns:
                for label, group in self.df.groupby("ground_truth_class", dropna=True):
                    vals = group[attribute].dropna().astype(str)
                    group_counts = vals.value_counts().to_dict()
                    by_class.setdefault(str(label), {})[attribute] = self._summary(group_counts, len(vals), target)
                    if target_sums_to_one:
                        findings.extend(self._find_gaps(attribute, group_counts, len(vals), target, scope=f"class:{label}"))
        return {
            "targets_provided": bool(self.targets),
            "attributes": overall,
            "by_class": by_class,
            "findings": findings,
        }

    @staticmethod
    def _summary(counts: dict[str, int], total: int, target: dict[str, float] | None) -> dict[str, Any]:
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
        return {"sample_count": total, "missing_count": None, "groups": groups}

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
