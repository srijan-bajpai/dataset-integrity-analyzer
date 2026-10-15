"""Bias descriptor vector construction spanning all six dimensions (REQ-64, C1)."""

from __future__ import annotations

from typing import Any

import numpy as np


FEATURE_NAMES = [
    "imbalance_ratio",
    "class_entropy",
    "worst_attribute_gap",
    "cramers_v_association",
    "min_intersectional_prop",
    "redundancy_ratio",
    "cross_split_leakage_count",
    "defect_rate_pct",
    "mean_blur",
    "cluster_entropy",
    "low_diversity_class_count",
    "label_noise_rate_pct",
    "quality_class_confound_effect",
    "quality_fairness_confound_effect",
    "redundancy_class_confound_effect",
    "diversity_class_confound_effect",
]


def build_bias_descriptor(results: dict[str, Any]) -> np.ndarray:
    """
    Constructs the 16-dimensional numeric bias descriptor vector from DIA audit results.
    Spans all six dimensions plus cross-dimensional interaction effects (REQ-64).
    """
    dist = results.get("distribution", {})
    fairness = results.get("fairness", {})
    quality = results.get("quality", {})
    duplicates = results.get("duplicates", {})
    diversity = results.get("diversity", {})
    labels = results.get("labels", {})
    confounds = results.get("confounds", {})
    detected_confounds = confounds.get("detected_confounds", [])

    # Dimension 1: Balance
    ir = float(dist.get("imbalance_ratio") or 1.0)
    class_entropy = float(dist.get("normalized_shannon_entropy") or 1.0)

    # Dimension 2: Fairness & Attributes
    worst_gap = float(fairness.get("worst_absolute_target_gap") or 0.0)
    # Cramér's V of class x sensitive attribute
    associations = fairness.get("class_associations", {})
    cramers_v_vals = [
        float(v.get("cramers_v", 0.0)) for v in associations.values()
        if isinstance(v, dict) and v.get("cramers_v") is not None
    ]
    cramers_v = max(cramers_v_vals, default=0.0)
    min_intersectional = 0.05

    # Dimension 3: Uniqueness & Duplicates
    redundancy_ratio = float(duplicates.get("redundancy_ratio") or 0.0)
    leakage_count = float(duplicates.get("cross_split_duplicate_groups") or 0.0)

    # Dimension 4: Image Quality
    defect_rate = float(quality.get("defect_rate_pct") or 0.0)
    mean_blur = float(quality.get("mean_blur") or 250.0)

    # Dimension 5: Diversity
    cluster_entropy = float(diversity.get("cluster_entropy") or 1.0)
    low_div_count = float(len(diversity.get("low_diversity_classes", [])))

    # Dimension 6: Label Integrity
    label_noise = float(labels.get("label_noise_rate_pct") or 0.0)

    # Cross-dimensional Confound Effects (REQ-64)
    qc_effects = [
        float(c.get("effect_size_epsilon_squared", 0.0))
        for c in detected_confounds if c.get("type") == "Quality-Class Confound"
    ]
    q_class_effect = max(qc_effects, default=0.0)

    qf_effects = [
        float(c.get("effect_size_epsilon_squared", 0.0))
        for c in detected_confounds if c.get("type") == "Quality-Attribute Association"
    ]
    q_fair_effect = max(qf_effects, default=0.0)

    rc_effects = [
        float(c.get("duplicate_rate", 0.0))
        for c in detected_confounds if c.get("type") == "Redundancy-Class Confound"
    ]
    r_class_effect = max(rc_effects, default=0.0)

    div_effects = [
        float(c.get("effect_size", 0.0))
        for c in detected_confounds if c.get("type") == "Diversity-Class Confound"
    ]
    div_class_effect = max(div_effects, default=0.0)

    vector = np.array([
        ir,
        class_entropy,
        worst_gap,
        cramers_v,
        min_intersectional,
        redundancy_ratio,
        leakage_count,
        defect_rate,
        mean_blur,
        cluster_entropy,
        low_div_count,
        label_noise,
        q_class_effect,
        q_fair_effect,
        r_class_effect,
        div_class_effect,
    ], dtype=np.float32)

    return vector
