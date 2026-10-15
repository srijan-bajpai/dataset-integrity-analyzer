"""Completeness and schema checks for user-supplied sample metadata."""

from __future__ import annotations

from typing import Any
import pandas as pd


class MetadataAnalyzer:
    SUPPORTED_TYPES = {"string", "category", "number", "integer", "boolean"}

    def __init__(self, df: pd.DataFrame, schema: dict[str, dict[str, Any]] | None = None):
        self.df = df
        self.schema = schema or {}

    def run(self) -> dict[str, Any]:
        reserved = {"id", "sample_id", "path", "file_path", "sample_ref", "ground_truth_class", "split", "is_valid", "content_sha256", "error_message", "name", "description"}
        attrs = {
            col for col in self.df.columns
            if col not in reserved and not col.startswith(("quality_", "flag_", "label_", "predicted_", "duplicate_", "embedding_", "metadata_source:", "attribute_confidence:"))
        }
        attrs.update(f"attribute:{name}" for name in self.schema)
        n = len(self.df)
        columns: dict[str, Any] = {}
        findings: list[dict[str, Any]] = []
        for col in sorted(attrs):
            display_name = col.removeprefix("attribute:")
            spec = self.schema.get(display_name, {})
            expected_type = spec.get("type")
            if expected_type and expected_type not in self.SUPPORTED_TYPES:
                raise ValueError(f"Unsupported metadata type '{expected_type}' for '{display_name}'.")
            if col not in self.df.columns:
                series = pd.Series([None] * n, index=self.df.index, dtype="object")
            else:
                series = self.df[col]

            nonblank = series.notna() & series.astype("string").str.strip().ne("").fillna(False)
            missing = int((~nonblank).sum())
            values = series.loc[nonblank].astype(str).str.strip()
            counts = values.value_counts()
            invalid_mask = pd.Series(False, index=series.index)
            usable = series.loc[nonblank]
            if expected_type in {"number", "integer"}:
                numeric = pd.to_numeric(usable, errors="coerce")
                invalid_mask.loc[usable.index] = numeric.isna() | ~numeric.map(lambda value: pd.notna(value) and abs(float(value)) != float("inf"))
                if expected_type == "integer":
                    invalid_mask.loc[usable.index] |= numeric.notna() & (numeric % 1 != 0)
            elif expected_type == "string":
                invalid_mask.loc[usable.index] = ~usable.map(lambda value: isinstance(value, str))
            elif expected_type == "boolean":
                accepted = {"true", "false", "0", "1"}
                invalid_mask.loc[usable.index] = ~usable.astype(str).str.lower().isin(accepted)
            allowed_values = spec.get("allowed_values")
            if allowed_values is not None:
                invalid_mask.loc[usable.index] |= ~usable.astype(str).isin({str(v) for v in allowed_values})
            invalid_count = int(invalid_mask.sum())
            columns[display_name] = {
                "present_count": n - missing,
                "missing_count": missing,
                "missing_rate": missing / n if n else 0.0,
                "distinct_values": int(counts.size),
                "value_counts": {str(k): int(v) for k, v in counts.items()},
                "expected_type": expected_type,
                "invalid_count": invalid_count,
                "allowed_values": allowed_values,
            }
            if missing:
                findings.append({
                    "code": "METADATA_MISSING_VALUES", "severity": "review",
                    "attribute": display_name, "count": missing,
                    "description": f"Attribute '{display_name}' is missing for {missing} of {n} samples.",
                })
            if invalid_count:
                bad_refs = self.df.loc[invalid_mask, "sample_ref"].astype(str).tolist()[:100] if "sample_ref" in self.df else []
                findings.append({
                    "code": "METADATA_INVALID_VALUES", "severity": "warning",
                    "attribute": display_name, "count": invalid_count, "sample_refs": bad_refs,
                    "description": f"Attribute '{display_name}' has {invalid_count} value(s) outside its declared type or allowed values.",
                })
            if not counts.size and not missing:
                findings.append({
                    "code": "METADATA_NO_VALID_VALUES", "severity": "warning", "attribute": display_name,
                    "description": f"Attribute '{display_name}' has no usable values.",
                })
        if "ground_truth_class" in self.df.columns:
            missing_labels = int(self.df["ground_truth_class"].isna().sum())
            if missing_labels:
                findings.append({
                    "code": "CLASS_LABELS_MISSING", "severity": "warning", "count": missing_labels,
                    "description": f"{missing_labels} samples have no class label.",
                })
        return {"sample_count": n, "attributes": columns, "findings": findings}
