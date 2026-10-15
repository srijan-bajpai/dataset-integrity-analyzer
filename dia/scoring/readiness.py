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

    @staticmethod
    def _scale(value: float | None, low: float, high: float, reverse: bool = False) -> float | None:
        if value is None or not math.isfinite(float(value)):
            return None
        normalized = 100 * (min(max(float(value), low), high) - low) / (high - low)
        return 100 - normalized if reverse else normalized

    def compute(self, results: dict[str, Any]) -> dict[str, Any]:
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
        verdict = None
        if score is not None:
            verdict = "Critical / Not Usable" if score < 40 else "Needs Remediation" if score < 70 else "Acceptable" if score < 85 else "Production Ready"
        return {
            "version": self.VERSION,
            "overall_score": round(score, 1) if score is not None else None,
            "sub_scores": scores,
            "unavailable_dimensions": sorted(set(candidates) - set(scores)),
            "coverage_pct": round(100 * total_weight, 1),
            "verdict": verdict,
            "weights": {name: self.WEIGHTS[name] for name in scores},
        }
