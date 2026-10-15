"""Embedding-based visual coverage, cluster redundancy, and within-class diversity checks."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import pairwise_distances, silhouette_score
from sklearn.preprocessing import normalize

from .base import BaseAnalyzer


class DiversityAnalyzer(BaseAnalyzer):
    """
    Analyzes visual diversity, embedding clustering, cluster redundancy, and outliers.
    (REQ-40, REQ-41, REQ-42, REQ-43, REQ-44, REQ-46)
    """

    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray, n_clusters: int = 10,
                 redundancy_cosine_threshold: float = 0.95):
        super().__init__(df)
        self.embeddings = normalize(np.asarray(embeddings, dtype=np.float32))
        self.n_clusters = n_clusters
        self.redundancy_cosine_threshold = redundancy_cosine_threshold

    def run(self) -> dict[str, Any]:
        n = len(self.embeddings)
        if n != len(self.df) or n < 2:
            raise ValueError("At least two aligned image embeddings are required.")

        max_k = min(self.n_clusters, n - 1, 10)
        rng = np.random.default_rng(42)
        sample_indices = rng.choice(n, min(n, 1000), replace=False)
        candidates = []

        for k in range(2, max_k + 1):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(self.embeddings)
            if len(np.unique(labels)) < 2:
                continue
            sampled_labels = labels[sample_indices]
            if len(np.unique(sampled_labels)) < 2:
                continue
            score = float(silhouette_score(self.embeddings[sample_indices], sampled_labels, metric="cosine"))
            candidates.append((score, k, labels, km))

        if candidates:
            best_silhouette, selected_k, cluster_labels, best_km = max(candidates, key=lambda item: (item[0], -item[1]))
            silhouette_status = "available"
        else:
            selected_k = min(2, n)
            best_km = KMeans(n_clusters=selected_k, random_state=42, n_init=10)
            cluster_labels = best_km.fit_predict(self.embeddings)
            best_silhouette, silhouette_status = None, "unavailable"

        self.df["cluster_id"] = cluster_labels
        counts = pd.Series(cluster_labels).value_counts().sort_index()
        probs = counts / counts.sum()
        cluster_entropy = float(entropy(probs) / np.log(selected_k)) if selected_k > 1 else 0.0

        # Cluster redundancy analysis (REQ-44)
        redundant_clusters: list[dict[str, Any]] = []
        total_prunable_samples = 0
        sparse_clusters: list[dict[str, Any]] = []

        for cid in range(selected_k):
            c_indices = np.flatnonzero(cluster_labels == cid)
            c_size = len(c_indices)
            if c_size > 1:
                c_embs = self.embeddings[c_indices]
                # Cosine similarities within cluster
                pw_dist = pairwise_distances(c_embs, metric="cosine")
                triu_idx = np.triu_indices(c_size, k=1)
                mean_cos_dist = float(pw_dist[triu_idx].mean())
                mean_cos_sim = 1.0 - mean_cos_dist

                if mean_cos_sim >= self.redundancy_cosine_threshold:
                    # Estimate samples prunable while keeping at least 2 exemplar samples
                    prunable = max(0, c_size - 2)
                    total_prunable_samples += prunable
                    redundant_clusters.append({
                        "cluster_id": int(cid),
                        "sample_count": int(c_size),
                        "mean_cosine_similarity": round(float(mean_cos_sim), 4),
                        "estimated_prunable_samples": int(prunable),
                    })
                elif c_size < max(3, int(round(0.02 * n))):
                    sparse_clusters.append({
                        "cluster_id": int(cid),
                        "sample_count": int(c_size),
                        "mean_cosine_similarity": round(float(mean_cos_sim), 4),
                    })
            elif c_size == 1:
                sparse_clusters.append({
                    "cluster_id": int(cid),
                    "sample_count": 1,
                    "mean_cosine_similarity": 1.0,
                })

        # Per-class diversity (REQ-43)
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
                    "cluster_entropy": round(normalized_entropy, 4),
                    "mean_pairwise_cosine_distance": round(mean_distance, 4),
                    "low_diversity": len(indices) < 5 or normalized_entropy < 0.2,
                }

        # DBSCAN density and visual outlier detection (REQ-41)
        dbscan = DBSCAN(eps=0.5, min_samples=min(5, max(2, n // 20)), metric="cosine", n_jobs=-1)
        dbscan_labels = dbscan.fit_predict(self.embeddings)
        dbscan_clusters = sorted(set(int(v) for v in dbscan_labels if v >= 0))
        is_visual_outlier = (dbscan_labels == -1)

        self.df["flag_visual_outlier"] = is_visual_outlier

        distances = pairwise_distances(self.embeddings[sample_indices], metric="cosine")
        mean_pairwise = float(distances[np.triu_indices(len(sample_indices), k=1)].mean()) if len(sample_indices) > 1 else 0.0

        return {
            "status": "available",
            "cluster_entropy": round(cluster_entropy, 4),
            "selected_k": int(selected_k),
            "k_selection": "maximum cosine silhouette over k=2..min(10,n-1)",
            "silhouette_score": round(best_silhouette, 4) if best_silhouette is not None else None,
            "silhouette_status": silhouette_status,
            "dbscan": {
                "eps_cosine": 0.5,
                "min_samples": min(5, max(2, n // 20)),
                "cluster_count": len(dbscan_clusters),
                "noise_count": int(np.sum(is_visual_outlier)),
                "noise_rate": round(float(np.mean(is_visual_outlier)), 4) if n else 0.0,
            },
            "redundant_clusters": redundant_clusters,
            "total_prunable_samples": int(total_prunable_samples),
            "sparse_clusters": sparse_clusters,
            "mean_pairwise_cosine_distance": round(mean_pairwise, 4),
            "per_class": class_results,
            "low_diversity_classes": [key for key, value in class_results.items() if value["low_diversity"]],
        }
