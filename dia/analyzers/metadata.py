"""Checks completeness and basic consistency of supplied sample metadata."""

from __future__ import annotations

from typing import Any
import pandas as pd


class MetadataAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self) -> dict[str, Any]:
        reserved = {"sample_id", "path", "sample_ref", "ground_truth_class", "split", "is_valid"}
        attrs = [
            col for col in self.df.columns
            if col not in reserved and not col.startswith(("quality_", "flag_", "label_", "predicted_", "duplicate_", "embedding_"))
        ]
        n = len(self.df)
        columns: dict[str, Any] = {}
        findings = []
        for col in attrs:
            series = self.df[col]
            missing = int(series.isna().sum() + series.astype("string").str.strip().eq("").fillna(False).sum())
            values = series.dropna().astype(str).str.strip()
            blank_unique = int((values == "").sum())
            counts = values[values != ""].value_counts()
            columns[col] = {
                "present_count": n - missing,
                "missing_count": missing,
                "missing_rate": missing / n if n else 0.0,
                "distinct_values": int(counts.size),
                "value_counts": {str(k): int(v) for k, v in counts.items()},
                "blank_values": blank_unique,
            }
            if missing:
                findings.append({
                    "code": "METADATA_MISSING_VALUES", "severity": "review",
                    "attribute": col, "count": missing,
                    "description": f"Attribute '{col}' is missing for {missing} of {n} samples.",
                })
            if counts.empty:
                findings.append({
                    "code": "METADATA_NO_VALID_VALUES", "severity": "warning", "attribute": col,
                    "description": f"Attribute '{col}' has no usable values.",
                })
        if "ground_truth_class" in self.df.columns:
            missing_labels = int(self.df["ground_truth_class"].isna().sum())
            if missing_labels:
                findings.append({
                    "code": "CLASS_LABELS_MISSING", "severity": "warning", "count": missing_labels,
                    "description": f"{missing_labels} samples have no class label.",
                })
        return {"sample_count": n, "attributes": columns, "findings": findings}
