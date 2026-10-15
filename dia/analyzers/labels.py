"""Confident learning label integrity audit and outlier detection (REQ-47..52)."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from .base import BaseAnalyzer


class LabelAuditAnalyzer(BaseAnalyzer):
    """
    Identifies probable mislabels using out-of-fold confident learning (Northcutt et al.)
    and detects embedding outliers via Isolation Forest.
    (REQ-47, REQ-48, REQ-49, REQ-50, REQ-51, REQ-52)
    """

    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray):
        super().__init__(df)
        self.embeddings = np.asarray(embeddings, dtype=np.float32)

    def run(self) -> Dict[str, Any]:
        y_true = self.df["ground_truth_class"].values
        classes = np.unique(y_true)

        counts = np.unique(y_true, return_counts=True)[1]
        min_samples = int(np.min(counts)) if len(counts) > 0 else 0
        n_samples = len(y_true)

        # Default columns
        self.df["label_issue_prob"] = np.nan
        self.df["flag_suspected_mislabel"] = False
        self.df["predicted_class"] = None
        self.df["flag_embedding_outlier"] = False
        self.df["embedding_outlier_score"] = 0.0

        if len(classes) < 2 or min_samples < 2:
            return {
                "status": "unavailable",
                "label_noise_rate": None,
                "label_noise_rate_pct": None,
                "suspected_count": 0,
                "sample_count": n_samples,
                "reason": "At least two classes with two samples each are required for out-of-fold review.",
            }

        n_splits = min(5, min_samples)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        model = LogisticRegression(max_iter=1000, class_weight="balanced")

        pred_probs = np.zeros((n_samples, len(classes)), dtype=np.float64)

        try:
            for train_idx, val_idx in cv.split(self.embeddings, y_true):
                X_train, X_val = self.embeddings[train_idx], self.embeddings[val_idx]
                y_train = y_true[train_idx]

                model.fit(X_train, y_train)
                probs = model.predict_proba(X_val)
                for i, c in enumerate(model.classes_):
                    c_idx = np.where(classes == c)[0][0]
                    pred_probs[val_idx, c_idx] = probs[:, i]
        except ValueError:
            return {
                "status": "unavailable",
                "label_noise_rate": None,
                "label_noise_rate_pct": None,
                "suspected_count": 0,
                "sample_count": n_samples,
                "reason": "The cross-validation model could not be fit for this class distribution.",
            }

        # 1. Confident Learning class thresholds t_j (mean predicted prob for given class)
        class_thresholds: dict[str, float] = {}
        for c_idx, c in enumerate(classes):
            mask = y_true == c
            if np.any(mask):
                class_thresholds[str(c)] = float(np.mean(pred_probs[mask, c_idx]))
            else:
                class_thresholds[str(c)] = 1.0 / len(classes)

        # 2. Confident Joint and suspected mislabel detection (REQ-48)
        suspected_mislabels: list[bool] = []
        issue_probs: list[float] = []
        predicted_classes: list[str] = []
        conf_joint_counts = np.zeros((len(classes), len(classes)), dtype=np.int64)

        for i in range(n_samples):
            true_label = y_true[i]
            true_c_idx = np.where(classes == true_label)[0][0]
            true_prob = pred_probs[i, true_c_idx]

            # Find competing class with highest probability
            probs_i = pred_probs[i]
            pred_c_idx = int(np.argmax(probs_i))
            max_prob = float(probs_i[pred_c_idx])
            pred_label = str(classes[pred_c_idx])

            # Confident learning criterion:
            # Predicted prob of competing class exceeds that class's threshold t_k
            # and max_prob > true_prob
            pred_thresh = class_thresholds[pred_label]
            is_mislabel = (
                (pred_c_idx != true_c_idx)
                and (max_prob >= pred_thresh)
                and (max_prob > true_prob)
            )

            suspected_mislabels.append(is_mislabel)
            # Confidence margin (excess probability of predicted class over given class)
            margin = max(0.0, max_prob - true_prob) if is_mislabel else 0.0
            issue_probs.append(float(round(margin, 4)))
            predicted_classes.append(pred_label)

            latent_k = pred_c_idx if (max_prob >= pred_thresh and max_prob > true_prob) else true_c_idx
            conf_joint_counts[true_c_idx, latent_k] += 1

        self.df["label_issue_prob"] = issue_probs
        self.df["flag_suspected_mislabel"] = suspected_mislabels
        self.df["predicted_class"] = predicted_classes

        # 3. Outlier detection using Isolation Forest (REQ-51)
        outlier_flags = np.zeros(n_samples, dtype=bool)
        outlier_scores = np.zeros(n_samples, dtype=np.float32)
        if n_samples >= 5:
            try:
                contamination = max(0.01, min(0.10, 5.0 / n_samples))
                iso = IsolationForest(
                    contamination=contamination,
                    random_state=42,
                    n_jobs=1,
                )
                iso.fit(self.embeddings)
                raw_scores = -iso.score_samples(self.embeddings)
                # Normalize outlier score to [0, 1]
                min_s, max_s = float(np.min(raw_scores)), float(np.max(raw_scores))
                if max_s > min_s:
                    outlier_scores = (raw_scores - min_s) / (max_s - min_s)
                else:
                    outlier_scores = np.zeros(n_samples, dtype=np.float32)
                outlier_flags = iso.predict(self.embeddings) == -1
            except Exception:
                pass

        self.df["flag_embedding_outlier"] = outlier_flags.tolist()
        self.df["embedding_outlier_score"] = [float(round(s, 4)) for s in outlier_scores]

        # 4. Per-class metrics and reliability (REQ-52, REQ-51)
        per_class_stats: dict[str, dict[str, Any]] = {}
        per_class_reliability: dict[str, float] = {}
        for c_idx, c in enumerate(classes):
            c_str = str(c)
            mask = y_true == c
            c_count = int(np.sum(mask))
            c_flagged = int(np.sum(np.array(suspected_mislabels)[mask]))
            c_outliers = int(np.sum(outlier_flags[mask]))

            flagged_rate = c_flagged / c_count if c_count else 0.0
            reliability = round(1.0 - flagged_rate, 4)
            per_class_reliability[c_str] = reliability

            per_class_stats[c_str] = {
                "sample_count": c_count,
                "suspected_mislabel_count": c_flagged,
                "suspected_mislabel_rate": round(flagged_rate, 4),
                "reliability_score": reliability,
                "confident_threshold": round(class_thresholds[c_str], 4),
                "outlier_count": c_outliers,
                "outlier_rate": round(c_outliers / c_count, 4) if c_count else 0.0,
            }

        # 5. Top ranked suspected mislabels by margin (REQ-49)
        ranked_indices = np.argsort(issue_probs)[::-1]
        top_candidates = []
        for idx in ranked_indices:
            if not suspected_mislabels[idx] or issue_probs[idx] <= 0:
                continue
            sample_ref = str(self.df.iloc[idx].get("sample_ref", f"sample_{idx}"))
            top_candidates.append({
                "sample_ref": sample_ref,
                "given_label": str(y_true[idx]),
                "predicted_label": predicted_classes[idx],
                "confidence_margin": issue_probs[idx],
                "predicted_prob": float(round(np.max(pred_probs[idx]), 4)),
                "given_label_prob": float(round(pred_probs[idx, np.where(classes == y_true[idx])[0][0]], 4)),
            })
            if len(top_candidates) >= 50:
                break

        # Estimated overall noise rate
        noise_rate = float(np.mean(suspected_mislabels))

        # Normalized noise matrix (estimated P(given=j, true=k))
        joint_matrix: dict[str, dict[str, float]] = {}
        total_counts = float(np.sum(conf_joint_counts)) or 1.0
        for i, c1 in enumerate(classes):
            joint_matrix[str(c1)] = {}
            for j, c2 in enumerate(classes):
                joint_matrix[str(c1)][str(c2)] = float(round(conf_joint_counts[i, j] / total_counts, 4))

        return {
            "status": "available",
            "label_noise_rate": round(noise_rate, 4),
            "label_noise_rate_pct": round(noise_rate * 100, 2),
            "suspected_count": int(np.sum(suspected_mislabels)),
            "sample_count": n_samples,
            "cross_validation_folds": int(n_splits),
            "class_thresholds": {k: round(v, 4) for k, v in class_thresholds.items()},
            "per_class": per_class_stats,
            "per_class_reliability": per_class_reliability,
            "estimated_noise_matrix": joint_matrix,
            "top_suspected_mislabels": top_candidates,
            "outlier_detection": {
                "method": "IsolationForest over ResNet-18 embeddings",
                "total_outliers": int(np.sum(outlier_flags)),
                "outlier_rate": round(float(np.mean(outlier_flags)), 4) if n_samples else 0.0,
            },
            "method": "Stratified out-of-fold confident learning (Northcutt et al.) with Isolation Forest outlier detection",
            "caveat": "Disagreements are review signals derived from a surrogate classifier, not verified ground truth; ambiguous imagery or overlapping classes can cause disagreements.",
        }
