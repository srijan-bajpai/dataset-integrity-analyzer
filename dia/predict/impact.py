"""Accuracy-impact estimation remains unavailable until validated on held-out variants."""

from typing import Any


class BiasImpactPredictor:
    def __init__(self, agg_results: dict[str, Any]):
        self.agg = agg_results

    def predict(self) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "reason": "No impact model has passed the SRS validation protocol on controlled training and held-out dataset variants.",
            "is_validated": False,
            "required_validation": {
                "baseline_and_perturbed_datasets": True,
                "train_and_evaluate_models": True,
                "held_out_variant_error_threshold": "must be documented before enabling estimates",
            },
        }
