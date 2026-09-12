import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.stats import entropy
from sklearn.metrics import pairwise_distances
from .base import BaseAnalyzer
from typing import Dict, Any

class DiversityAnalyzer(BaseAnalyzer):
    """
    Measures visual diversity using embeddings clustering.
    (REQ-41, REQ-42)
    """
    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray, n_clusters: int = 10):
        super().__init__(df)
        self.embeddings = embeddings
        self.n_clusters = n_clusters
        
    def run(self) -> Dict[str, Any]:
        if len(self.embeddings) < self.n_clusters:
            self.n_clusters = max(1, len(self.embeddings))
            
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(self.embeddings)
        
        self.df['cluster_id'] = cluster_labels
        
        # Calculate cluster entropy
        cluster_counts = pd.Series(cluster_labels).value_counts()
        probs = cluster_counts / cluster_counts.sum()
        h_norm = entropy(probs) / np.log(self.n_clusters) if self.n_clusters > 1 else 0.0
        
        # Calculate per-class diversity (variance of cluster assignments or embedding variance)
        class_diversity = {}
        for c in self.df['ground_truth_class'].unique():
            idx = self.df['ground_truth_class'] == c
            if idx.sum() > 1:
                class_embs = self.embeddings[idx]
                variance = np.var(class_embs, axis=0).mean()
                class_diversity[c] = variance
            else:
                class_diversity[c] = 0.0
                
        # Mean pairwise distance over a random sample (for performance)
        sample_size = min(1000, len(self.embeddings))
        sampled_embs = self.embeddings[np.random.choice(len(self.embeddings), sample_size, replace=False)]
        distances = pairwise_distances(sampled_embs, metric='cosine')
        mean_pairwise_dist = np.mean(distances[np.triu_indices(sample_size, k=1)]) if sample_size > 1 else 0.0
        
        return {
            'cluster_entropy': h_norm,
            'mean_pairwise_distance': mean_pairwise_dist,
            'per_class_embedding_variance': class_diversity
        }
