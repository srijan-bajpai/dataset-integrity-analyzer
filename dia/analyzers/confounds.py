import pandas as pd
import numpy as np
from scipy.stats import kruskal
from .base import BaseAnalyzer
from typing import Dict, Any

class ConfoundAnalyzer(BaseAnalyzer):
    """
    Detects cross-dimensional confounds (Phase 4).
    (REQ-54, REQ-55, REQ-56, REQ-57, REQ-60)
    """
    def __init__(self, df: pd.DataFrame):
        super().__init__(df)
        self.quality_metrics = ['quality_blur', 'quality_brightness', 'quality_contrast', 'quality_resolution']
        
    def run(self) -> Dict[str, Any]:
        confounds = []
        
        # 1. Quality x Class Confound (REQ-55)
        classes = self.df['ground_truth_class'].unique()
        if len(classes) >= 2:
            for metric in self.quality_metrics:
                groups = [self.df[self.df['ground_truth_class'] == c][metric].dropna().values for c in classes]
                
                # Check if all groups have at least 5 valid samples for KW test
                if all(len(g) >= 5 for g in groups):
                    stat, p_val = kruskal(*groups)
                    
                    if p_val < 0.05: # Simple threshold, no Benjamini-Hochberg for prototype simplicity unless requested
                        confounds.append({
                            'type': 'Quality-Class Confound',
                            'dimension_a': metric,
                            'dimension_b': 'class',
                            'p_value': p_val,
                            'description': f"Image {metric} varies significantly across classes."
                        })
                        
        # 2. Redundancy x Class Confound (REQ-56)
        if 'duplicate_group' in self.df.columns:
            for c in classes:
                class_df = self.df[self.df['ground_truth_class'] == c]
                raw_count = len(class_df)
                unique_count = len(class_df.drop_duplicates(subset=['duplicate_group']))
                
                if raw_count > 0:
                    redundancy = (raw_count - unique_count) / raw_count
                    if redundancy > 0.1: # If more than 10% of the class is redundant
                        confounds.append({
                            'type': 'Redundancy-Class Confound',
                            'dimension_a': 'duplicates',
                            'dimension_b': 'class',
                            'affected_group': c,
                            'description': f"Class '{c}' is highly redundant (effective count {unique_count} vs raw {raw_count})."
                        })
                        
        # 3. Label Noise x Class Confound (REQ-58)
        if 'flag_suspected_mislabel' in self.df.columns:
            for c in classes:
                class_df = self.df[self.df['ground_truth_class'] == c]
                noise_rate = class_df['flag_suspected_mislabel'].mean()
                if noise_rate > 0.1: # If more than 10% noise
                    confounds.append({
                        'type': 'LabelNoise-Class Confound',
                        'dimension_a': 'labels',
                        'dimension_b': 'class',
                        'affected_group': c,
                        'description': f"Class '{c}' has unusually high label noise ({noise_rate*100:.1f}%)."
                    })
                    
        return {
            'detected_confounds': confounds
        }
