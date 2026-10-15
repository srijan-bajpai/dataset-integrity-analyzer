"""Cross-dimensional comparisons with small-sample safeguards."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal

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
    """Detect large quality/class and representation/class associations."""

    def __init__(self, df: pd.DataFrame):
        super().__init__(df)
        self.quality_metrics = ["quality_blur", "quality_brightness", "quality_contrast", "quality_resolution"]

    def run(self) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        labels = self.df.get("ground_truth_class", pd.Series(dtype=object)).dropna().unique()
        tests: list[tuple[str, float, dict[str, Any]]] = []
        if len(labels) >= 2:
            for metric in self.quality_metrics:
                if metric not in self.df:
                    continue
                groups = [
                    pd.to_numeric(self.df.loc[self.df["ground_truth_class"] == label, metric], errors="coerce").dropna().to_numpy()
                    for label in labels
                ]
                kept = [(str(label), group) for label, group in zip(labels, groups) if len(group) >= 5]
                groups = [group for _, group in kept]
                if len(groups) < 2 or np.all(np.concatenate(groups) == np.concatenate(groups)[0]):
                    continue
                try:
                    statistic, p_value = kruskal(*groups)
                    n = sum(map(len, groups))
                    # Epsilon-squared is a rank-based effect size estimate.
                    effect = max(0.0, (statistic - len(groups) + 1) / max(n - len(groups), 1))
                    tests.append((metric, float(p_value), {
                        "type": "Quality-Class Confound", "dimension_a": metric,
                        "dimension_b": "class", "statistic": float(statistic),
                        "effect_size_epsilon_squared": effect,
                        "group_counts": {label: int(len(group)) for label, group in kept},
                        "description": f"{metric} differs across class groups; inspect the effect size and group summaries.",
                    }))
                except (ValueError, FloatingPointError):
                    continue
        # Compare quality by sensitive/user-supplied groups too. Keep these as
        # associations that need review, not causal claims.
        metadata_columns = [
            column for column in self.df.columns
            if column.startswith("attribute:") and self.df[column].nunique(dropna=True) in range(2, 21)
        ]
        for column in metadata_columns:
            for metric in self.quality_metrics:
                if metric not in self.df:
                    continue
                groups = []
                counts = {}
                for value, group in self.df.groupby(column, dropna=True):
                    values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy()
                    if len(values) >= 5:
                        groups.append(values)
                        counts[str(value)] = int(len(values))
                if len(groups) < 2 or np.all(np.concatenate(groups) == np.concatenate(groups)[0]):
                    continue
                try:
                    statistic, p_value = kruskal(*groups)
                    n = sum(map(len, groups))
                    effect = max(0.0, (statistic - len(groups) + 1) / max(n - len(groups), 1))
                    name = f"{column}:{metric}"
                    tests.append((name, float(p_value), {
                        "type": "Quality-Attribute Association", "dimension_a": metric,
                        "dimension_b": column, "statistic": float(statistic),
                        "effect_size_epsilon_squared": effect, "group_counts": counts,
                        "description": f"{metric} differs across '{column}' groups; inspect the group summaries and effect size.",
                    }))
                except (ValueError, FloatingPointError):
                    continue
        significant = _benjamini_hochberg([(name, p) for name, p, _ in tests])
        for name, p_value, payload in tests:
            if name in significant:
                findings.append({**payload, "p_value": p_value, "severity": "review"})

        if "duplicate_group" in self.df and "ground_truth_class" in self.df:
            duplicate = self.df["duplicate_group"].notna()
            for label, group in self.df.groupby("ground_truth_class", dropna=True):
                ratio = float(duplicate.loc[group.index].mean()) if len(group) else 0.0
                if ratio >= 0.10 and len(group) >= 5:
                    findings.append({
                        "type": "Duplicate-Class Confound", "dimension_a": "duplicates",
                        "dimension_b": "class", "affected_group": str(label),
                        "duplicate_rate": ratio, "sample_count": int(len(group)),
                        "severity": "warning",
                        "description": f"Class '{label}' has a higher duplicate rate ({ratio:.1%}) than expected; review split leakage.",
                    })

        if "flag_suspected_mislabel" in self.df and "ground_truth_class" in self.df:
            flags = self.df["flag_suspected_mislabel"].fillna(False).astype(bool)
            for label, group in self.df.groupby("ground_truth_class", dropna=True):
                rate = float(flags.loc[group.index].mean()) if len(group) else 0.0
                if rate >= 0.10 and len(group) >= 5:
                    findings.append({
                        "type": "PossibleLabelDisagreement-Class Confound", "dimension_a": "labels",
                        "dimension_b": "class", "affected_group": str(label),
                        "disagreement_rate": rate, "sample_count": int(len(group)),
                        "severity": "review",
                        "description": f"Embedding suggestions disagree more often for class '{label}' ({rate:.1%}); this is not confirmation of wrong labels.",
                    })

        return {"detected_confounds": findings, "correction": "Benjamini-Hochberg false-discovery-rate correction"}
