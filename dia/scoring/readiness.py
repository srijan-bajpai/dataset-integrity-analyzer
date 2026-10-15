"""Versioned, coverage-aware dataset readiness score."""

import math
from typing import Any


class ReadinessScorer:
    VERSION = "readiness-v2"
    WEIGHTS = {
        "Balance": 0.20,
        "Fairness": 0.20,
        "Quality": 0.15,
        "Uniqueness": 0.15,
        "Diversity": 0.15,
        "Label Integrity": 0.15,
    }

    def __init__(self, agg_results: dict[str, Any] | None = None):
        self.agg_results = agg_results or {}

    @staticmethod
    def _scale(value: float | None, low: float, high: float, reverse: bool = False) -> float | None:
        if value is None or not math.isfinite(float(value)):
            return None
        normalized = 100 * (min(max(float(value), low), high) - low) / (high - low)
        return 100 - normalized if reverse else normalized

    def compute(self, results: dict[str, Any] | None = None) -> dict[str, Any]:
        results = results if results is not None else self.agg_results
        distribution = results.get("distribution", {})
        quality = results.get("quality", {})
        duplicates = results.get("duplicates", {})
        diversity = results.get("diversity", {})
        labels = results.get("labels", {})
        fairness = results.get("fairness", {})

        candidates = {
            "Balance": self._scale(distribution.get("imbalance_ratio"), 1.0, 10.0, reverse=True),
            "Fairness": self._scale(fairness.get("worst_absolute_target_gap"), 0.0, 0.5, reverse=True),
            "Quality": self._scale(quality.get("defect_rate_pct"), 0.0, 20.0, reverse=True),
            "Uniqueness": self._scale(duplicates.get("redundancy_ratio"), 0.0, 0.1, reverse=True),
            "Diversity": self._scale(diversity.get("cluster_entropy"), 0.0, 1.0),
            "Label Integrity": self._scale(labels.get("label_noise_rate_pct"), 0.0, 10.0, reverse=True),
        }
        scores = {name: round(value, 1) for name, value in candidates.items() if value is not None}
        total_weight = sum(self.WEIGHTS[name] for name in scores)
        score = (
            sum(scores[name] * self.WEIGHTS[name] for name in scores) / total_weight
            if total_weight else None
        )
        confounds = results.get("confounds", {}).get("detected_confounds", [])
        effect_sizes = [
            float(item.get("effect_size_epsilon_squared", 0.0))
            for item in confounds if item.get("effect_size_epsilon_squared") is not None
        ]
        confound_penalty = min(20.0, max(effect_sizes, default=0.0) * 20.0)
        if score is not None:
            score = max(0.0, score - confound_penalty)
        duplicates = results.get("duplicates", {})
        leakage = int(duplicates.get("cross_split_duplicate_groups", 0) or 0) > 0
        hard_gate = leakage or any(value < 30 for value in scores.values())
        verdict = None
        coverage_pct = round(100 * total_weight, 1)
        if score is not None:
            verdict = "Not Ready" if hard_gate else "Insufficient Coverage" if coverage_pct < 70 else "Critical / Not Usable" if score < 40 else "Needs Remediation" if score < 70 else "Acceptable" if score < 85 else "Production Ready"
        return {
            "version": self.VERSION,
            "overall_score": round(score, 1) if score is not None else None,
            "sub_scores": scores,
            "unavailable_dimensions": sorted(set(candidates) - set(scores)),
            "coverage_pct": coverage_pct,
            "verdict": verdict,
            "weights": {name: self.WEIGHTS[name] for name in scores},
            "formula": "Weighted mean of available dimension scores using SRS weights, renormalized by measured weight; subtract min(20, 20 × largest Kruskal epsilon-squared confound effect). A sub-score below 30 or cross-split duplicate group forces verdict Not Ready without changing the numeric score.",
            "confound_penalty_points": round(confound_penalty, 2),
            "hard_gate": {"triggered": hard_gate, "cross_split_duplicate_leakage": leakage,
                          "sub_score_below_30": any(value < 30 for value in scores.values())},
        }
