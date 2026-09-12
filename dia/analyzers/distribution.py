import pandas as pd
import numpy as np
from scipy.stats import entropy
from .base import BaseAnalyzer

class DistributionAnalyzer(BaseAnalyzer):
    """
    Computes class and demographic distribution statistics.
    (REQ-17, REQ-18)
    """
    def run(self):
        class_counts = self.df['ground_truth_class'].value_counts()
        n_majority = class_counts.max()
        n_minority = class_counts.min()
        
        # Imbalance Ratio
        ir = n_majority / n_minority if n_minority > 0 else float('inf')
        
        # Shannon Entropy (normalized)
        k = len(class_counts)
        probs = class_counts / class_counts.sum()
        h_norm = entropy(probs) / np.log(k) if k > 1 else 0.0
        
        # Gini Coefficient for categorical inequality
        # G = 1 - sum(p_i^2) is the Gini impurity.
        gini = 1.0 - np.sum(probs**2)
        
        # Severity
        if ir <= 1.5:
            severity = 'Balanced'
        elif ir <= 3.0:
            severity = 'Mild'
        elif ir <= 10.0:
            severity = 'Moderate'
        else:
            severity = 'Severe'
            
        return {
            'class_counts': class_counts.to_dict(),
            'imbalance_ratio': ir,
            'normalized_entropy': h_norm,
            'gini_coefficient': gini,
            'imbalance_severity': severity
        }
