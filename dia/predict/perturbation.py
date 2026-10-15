"""Synthetic perturbation benchmark harness for dataset degradation and C2 validation (REQ-66, OR-9)."""

from __future__ import annotations

import copy
from typing import Any

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


class DatasetPerturbationHarness:
    """
    Reusable synthetic-perturbation benchmark harness (REQ-66, OR-9).
    Injects controlled, analytically known defects and interactions:
    - Class imbalance (imbalance_ratio in [1.0, 20.0])
    - Near and exact duplicates
    - Image quality degradation (Gaussian blur, contrast reduction, noise)
    - Label noise (random or class-conditional label flips)
    - Interacting confounds (e.g. quality degradation applied preferentially to one sub-group or minority class)
    """

    def __init__(self, rng_seed: int = 42):
        self.rng = np.random.default_rng(rng_seed)

    def apply_class_imbalance(
        self,
        samples: list[dict[str, Any]],
        imbalance_ratio: float = 3.0,
        minority_class: str | None = None,
    ) -> list[dict[str, Any]]:
        """Subsamples one class to achieve target majority:minority imbalance ratio."""
        if imbalance_ratio <= 1.0 or not samples:
            return copy.deepcopy(samples)

        by_class: dict[str, list[dict[str, Any]]] = {}
        for s in samples:
            c = str(s.get("ground_truth_class", "unknown"))
            by_class.setdefault(c, []).append(s)

        if len(by_class) < 2:
            return copy.deepcopy(samples)

        classes = sorted(by_class.keys())
        target_minority = minority_class or classes[-1]

        result = []
        maj_len = max(len(by_class[c]) for c in classes if c != target_minority)
        desired_minority_len = max(2, int(round(maj_len / imbalance_ratio)))

        for c, items in by_class.items():
            if c == target_minority:
                keep_n = min(len(items), desired_minority_len)
                chosen = self.rng.choice(len(items), size=keep_n, replace=False)
                result.extend([items[i] for i in sorted(chosen)])
            else:
                result.extend(items)

        return result

    def inject_label_noise(
        self,
        samples: list[dict[str, Any]],
        noise_rate: float = 0.10,
        target_class: str | None = None,
    ) -> list[dict[str, Any]]:
        """Flips labels for a controlled proportion of samples (random or class-conditional)."""
        perturbed = copy.deepcopy(samples)
        if noise_rate <= 0 or not perturbed:
            return perturbed

        classes = sorted({str(s.get("ground_truth_class")) for s in perturbed if s.get("ground_truth_class")})
        if len(classes) < 2:
            return perturbed

        for s in perturbed:
            curr_c = str(s.get("ground_truth_class"))
            if target_class is not None and curr_c != target_class:
                continue

            if self.rng.random() < noise_rate:
                other_classes = [c for c in classes if c != curr_c]
                s["ground_truth_class"] = str(self.rng.choice(other_classes))
                s["injected_defect"] = "label_flip"

        return perturbed

    def inject_duplicates(
        self,
        samples: list[dict[str, Any]],
        redundancy_rate: float = 0.10,
        cross_split: bool = False,
    ) -> list[dict[str, Any]]:
        """Duplicates existing samples to create exact/near duplicates, optionally crossing splits."""
        perturbed = copy.deepcopy(samples)
        if redundancy_rate <= 0 or not perturbed:
            return perturbed

        n_to_duplicate = max(1, int(round(len(perturbed) * redundancy_rate)))
        chosen_indices = self.rng.choice(len(perturbed), size=n_to_duplicate, replace=True)

        for gid, idx in enumerate(chosen_indices):
            original = perturbed[idx]
            clone = copy.deepcopy(original)
            clone["id"] = f"{original.get('id', 'sample')}_dup_{gid}"
            clone["sample_ref"] = f"dup_{gid}_{original.get('sample_ref', 'img')}"
            clone["duplicate_group"] = gid
            original["duplicate_group"] = gid
            clone["injected_defect"] = "duplicate"

            if cross_split:
                curr_split = original.get("split", "train")
                clone["split"] = "test" if curr_split == "train" else "train"

            perturbed.append(clone)

        return perturbed

    def inject_quality_defects(
        self,
        samples: list[dict[str, Any]],
        defect_rate: float = 0.15,
        target_class: str | None = None,
        target_attribute_value: tuple[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Applies controlled quality defects (blur, low contrast, noise).
        Can be targeted to one class or sub-group to inject a deliberate confound (REQ-66).
        """
        perturbed = copy.deepcopy(samples)
        if defect_rate <= 0 or not perturbed:
            return perturbed

        for s in perturbed:
            # Check target conditions for interacting confound
            if target_class and str(s.get("ground_truth_class")) != target_class:
                continue
            if target_attribute_value:
                attr_name, attr_val = target_attribute_value
                s_attrs = s.get("attributes", {})
                if str(s_attrs.get(attr_name)) != attr_val:
                    continue

            if self.rng.random() < defect_rate:
                defect_type = self.rng.choice(["blur", "low_contrast", "noise"])
                s["injected_quality_defect"] = defect_type
                # Adjust metrics or mark defect
                metrics = s.setdefault("metrics", {})
                if defect_type == "blur":
                    metrics["quality_blur"] = 15.0  # severely blurred
                    metrics["flag_blurred"] = True
                elif defect_type == "low_contrast":
                    metrics["quality_contrast"] = 8.0  # low contrast
                    metrics["flag_low_contrast"] = True
                elif defect_type == "noise":
                    metrics["quality_noise_mad"] = 45.0  # heavy noise

        return perturbed
