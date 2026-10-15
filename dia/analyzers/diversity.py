"""Embedding-based visual coverage and within-class diversity checks."""

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import pairwise_distances, silhouette_score
from sklearn.preprocessing import normalize

from .base import BaseAnalyzer


class DiversityAnalyzer(BaseAnalyzer):
    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray, n_clusters: int = 10):
        super().__init__(df)
        self.embeddings = normalize(np.asarray(embeddings, dtype=np.float32))
        self.n_clusters = n_clusters

    def run(self) -> dict[str, Any]:
        n = len(self.embeddings)
        if n != len(self.df) or n < 2:
            raise ValueError("At least two aligned image embeddings are required.")
        max_k = min(self.n_clusters, n - 1, 10)
        rng = np.random.default_rng(42)
        sample_indices = rng.choice(n, min(n, 1000), replace=False)
        candidates = []
        for k in range(2, max_k + 1):
            labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(self.embeddings)
            if len(np.unique(labels)) < 2:
                continue
            sampled_labels = labels[sample_indices]
            if len(np.unique(sampled_labels)) < 2:
                continue
            score = float(silhouette_score(self.embeddings[sample_indices], sampled_labels, metric="cosine"))
            candidates.append((score, k, labels))
        if candidates:
            best_silhouette, selected_k, cluster_labels = max(candidates, key=lambda item: (item[0], -item[1]))
            silhouette_status = "available"
        else:
            selected_k = min(2, n)
            cluster_labels = KMeans(n_clusters=selected_k, random_state=42, n_init=10).fit_predict(self.embeddings)
            best_silhouette, silhouette_status = None, "unavailable"
        self.df["cluster_id"] = cluster_labels
        counts = pd.Series(cluster_labels).value_counts().sort_index()
        probs = counts / counts.sum()
        cluster_entropy = float(entropy(probs) / np.log(selected_k)) if selected_k > 1 else 0.0

        class_results: dict[str, Any] = {}
        if "ground_truth_class" in self.df:
            for label in sorted(self.df["ground_truth_class"].dropna().astype(str).unique()):
                indices = np.flatnonzero(self.df["ground_truth_class"].astype(str).to_numpy() == label)
                class_embs = self.embeddings[indices]
                class_clusters = cluster_labels[indices]
                class_counts = pd.Series(class_clusters).value_counts()
                normalized_entropy = float(entropy(class_counts / len(indices)) / np.log(selected_k)) if len(indices) > 1 and selected_k > 1 else 0.0
                pairwise = pairwise_distances(class_embs, metric="cosine")
                mean_distance = float(pairwise[np.triu_indices(len(indices), k=1)].mean()) if len(indices) > 1 else 0.0
                class_results[label] = {
                    "sample_count": int(len(indices)),
                    "cluster_entropy": normalized_entropy,
                    "mean_pairwise_cosine_distance": mean_distance,
                    "low_diversity": len(indices) < 5 or normalized_entropy < 0.2,
                }
        dbscan_labels = DBSCAN(eps=0.5, min_samples=5, metric="cosine", n_jobs=-1).fit_predict(self.embeddings)
        dbscan_clusters = sorted(set(int(v) for v in dbscan_labels if v >= 0))
        distances = pairwise_distances(self.embeddings[sample_indices], metric="cosine")
        mean_pairwise = float(distances[np.triu_indices(len(sample_indices), k=1)].mean()) if len(sample_indices) > 1 else 0.0
        return {
            "status": "available",
            "cluster_entropy": cluster_entropy,
            "selected_k": int(selected_k),
            "k_selection": "maximum cosine silhouette over k=2..min(10,n-1)",
            "silhouette_score": best_silhouette,
            "silhouette_status": silhouette_status,
            "dbscan": {"eps_cosine": 0.5, "min_samples": 5, "cluster_count": len(dbscan_clusters),
                       "noise_count": int(np.sum(dbscan_labels == -1))},
            "mean_pairwise_cosine_distance": mean_pairwise,
            "per_class": class_results,
            "low_diversity_classes": [key for key, value in class_results.items() if value["low_diversity"]],
        }
