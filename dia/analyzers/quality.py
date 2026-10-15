"""Deterministic no-reference image quality measurements."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .base import BaseAnalyzer


class QualityAnalyzer(BaseAnalyzer):
    def run(self) -> dict[str, Any]:
        metrics: dict[str, list[Any]] = {name: [] for name in (
            "blur", "brightness", "contrast", "resolution", "aspect_ratio", "noise_mad",
            "file_size_bytes", "min_side",
        )}
        lighting: list[str | None] = []
        for path in self.df["path"]:
            try:
                image = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError("Unreadable image")
                height, width = image.shape[:2]
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                lab_l = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
                brightness, contrast = float(lab_l.mean()), float(lab_l.std())
                high_pass = gray.astype(np.float32) - cv2.medianBlur(gray, 3).astype(np.float32)
                noise_mad = float(np.median(np.abs(high_pass - np.median(high_pass))))
                metrics["blur"].append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
                metrics["brightness"].append(brightness)
                metrics["contrast"].append(contrast)
                metrics["resolution"].append(int(width * height))
                metrics["aspect_ratio"].append(float(width / height) if height else None)
                metrics["noise_mad"].append(noise_mad)
                metrics["file_size_bytes"].append(Path(path).stat().st_size)
                metrics["min_side"].append(min(width, height))
                lighting.append("low" if brightness < 40 else "high" if brightness > 215 else "normal")
            except (OSError, ValueError, cv2.error):
                for values in metrics.values():
                    values.append(None)
                lighting.append(None)

        for name, values in metrics.items():
            self.df[f"quality_{name}"] = values
        self.df["quality_lighting_condition"] = lighting
        self.df["flag_blurred"] = self.df.quality_blur.lt(100).fillna(False)
        self.df["flag_underexposed"] = self.df.quality_brightness.lt(40).fillna(False)
        self.df["flag_overexposed"] = self.df.quality_brightness.gt(215).fillna(False)
        self.df["flag_low_contrast"] = self.df.quality_contrast.lt(20).fillna(False)
        self.df["flag_low_resolution"] = self.df.quality_min_side.lt(32).fillna(False)

        def mean(values: list[Any]) -> float | None:
            finite = [float(value) for value in values if value is not None and np.isfinite(value)]
            return float(np.mean(finite)) if finite else None

        flags = ["flag_blurred", "flag_underexposed", "flag_overexposed", "flag_low_contrast", "flag_low_resolution"]
        result = {f"mean_{name}": mean(values) for name, values in metrics.items()}
        result.update({f"pct_{flag.removeprefix('flag_')}": float(self.df[flag].mean() * 100) if len(self.df) else 0.0 for flag in flags})
        result["defect_rate_pct"] = float(self.df[flags].any(axis=1).mean() * 100) if len(self.df) else 0.0
        result["lighting_condition_counts"] = self.df.quality_lighting_condition.value_counts(dropna=True).to_dict()
        result["brisque"] = {"status": "unavailable", "reason": "No validated BRISQUE model is configured; deterministic image metrics are reported instead."}
        return result
