"""Dataset-conditioned attribute suggestions for human metadata review."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold


class AttributeSuggestionAnalyzer:
    """Suggest supplied attribute values from image features, without overwriting labels."""

    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray, minimum_per_value: int = 3,
                 review_confidence: float = 0.80):
        self.df = df
        self.embeddings = embeddings
        self.minimum_per_value = minimum_per_value
        self.review_confidence = review_confidence

    def run(self, attributes: list[str] | None = None) -> dict[str, Any]:
        metadata_columns = [
            column for column in self.df.columns
            if column.startswith("attribute:") and (attributes is None or column.removeprefix("attribute:") in attributes)
        ]
        suggestions: list[dict[str, Any]] = []
        summaries: dict[str, Any] = {}
        for column in metadata_columns:
            name = column.removeprefix("attribute:")
            raw = self.df[column]
            known_mask = raw.notna() & raw.astype("string").str.strip().ne("").fillna(False)
            known_indices = np.flatnonzero(known_mask.to_numpy())
            values = raw.loc[known_mask].astype(str).to_numpy()
            counts = pd.Series(values).value_counts()
            if len(counts) < 2 or int(counts.min()) < self.minimum_per_value:
                summaries[name] = {
                    "status": "insufficient_labels",
                    "label_counts": {str(k): int(v) for k, v in counts.items()},
                    "minimum_per_value": self.minimum_per_value,
                }
                continue

            splits = min(5, int(counts.min()))
            cv = StratifiedKFold(n_splits=splits, shuffle=True, random_state=42)
            probabilities = np.zeros((len(known_indices), len(counts)), dtype=float)
            known_classes = np.unique(values)
            try:
                for train_rows, test_rows in cv.split(self.embeddings[known_indices], values):
                    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
                    model.fit(self.embeddings[known_indices[train_rows]], values[train_rows])
                    probs = model.predict_proba(self.embeddings[known_indices[test_rows]])
                    for model_col, label in enumerate(model.classes_):
                        output_col = int(np.flatnonzero(known_classes == label)[0])
                        probabilities[test_rows, output_col] = probs[:, model_col]
            except (ValueError, FloatingPointError) as exc:
                summaries[name] = {"status": "unavailable", "reason": str(exc)}
                continue

            disagreements = 0
            for local_index, row_index in enumerate(known_indices):
                predicted_index = int(np.argmax(probabilities[local_index]))
                predicted = str(known_classes[predicted_index])
                confidence = float(probabilities[local_index, predicted_index])
                actual = str(values[local_index])
                if predicted != actual and confidence >= self.review_confidence:
                    disagreements += 1
                    suggestions.append({
                        "sample_ref": str(self.df.iloc[row_index].get("sample_ref", row_index)),
                        "attribute": name, "supplied_value": actual,
                        "suggested_value": predicted, "confidence": confidence,
                        "reason": "image-feature model disagrees with held-out supplied metadata",
                    })

            missing_indices = np.flatnonzero(~known_mask.to_numpy())
            missing_suggestions = 0
            if len(missing_indices):
                model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
                try:
                    model.fit(self.embeddings[known_indices], values)
                    probs = model.predict_proba(self.embeddings[missing_indices])
                    for offset, row_index in enumerate(missing_indices):
                        class_col = int(np.argmax(probs[offset]))
                        confidence = float(probs[offset, class_col])
                        if confidence >= self.review_confidence:
                            missing_suggestions += 1
                            suggestions.append({
                                "sample_ref": str(self.df.iloc[row_index].get("sample_ref", row_index)),
                                "attribute": name, "supplied_value": None,
                                "suggested_value": str(model.classes_[class_col]),
                                "confidence": confidence,
                                "reason": "image-feature model suggestion for missing metadata",
                            })
                except (ValueError, FloatingPointError):
                    missing_suggestions = 0

            summaries[name] = {
                "status": "available",
                "labeled_count": int(len(known_indices)),
                "missing_count": int(len(missing_indices)),
                "high_confidence_disagreements": disagreements,
                "missing_value_suggestions": missing_suggestions,
                "review_confidence_threshold": self.review_confidence,
                "label_counts": {str(k): int(v) for k, v in counts.items()},
            }
        return {
            "method": "dataset-conditioned out-of-fold logistic regression on pretrained image embeddings",
            "suggestions": suggestions,
            "attributes": summaries,
            "warning": "Suggestions reflect patterns in this dataset and may repeat its existing bias. They are review leads, not ground truth.",
        }
