from typing import Dict, List

class RecommendationEngine:
    """
    Generates actionable recommendations based on the aggregated metrics and confounds.
    (REQ-68, REQ-69, REQ-70)
    """
    def __init__(self, agg_results: dict):
        self.agg = agg_results
        
    def generate(self) -> List[Dict[str, str]]:
        recs = []
        
        # 1. Imbalance
        ir = self.agg.get('distribution', {}).get('imbalance_ratio', 1.0)
        if ir > 3.0:
            recs.append({
                'priority': 'High',
                'category': 'Balance',
                'action': f"Rebalance classes. The dataset is heavily imbalanced (ratio {ir:.1f}:1). Consider collecting more minority class samples or applying severe undersampling.",
            })
            
        # 2. Quality
        pct_blur = self.agg.get('quality', {}).get('pct_blurred', 0)
        if pct_blur > 5.0:
            recs.append({
                'priority': 'Medium',
                'category': 'Quality',
                'action': f"Remove or enhance blurry images. {pct_blur:.1f}% of samples fail the variance of Laplacian threshold."
            })
            
        # 3. Duplicates
        redundancy = self.agg.get('duplicates', {}).get('redundancy_ratio', 0)
        if redundancy > 0.05:
            recs.append({
                'priority': 'High',
                'category': 'Uniqueness',
                'action': f"Deduplicate dataset. Found a {redundancy*100:.1f}% redundancy rate which will leak train/test data or cause overfitting."
            })
            
        # 4. Labels
        noise = self.agg.get('labels', {}).get('label_noise_rate', 0)
        if noise > 0.05:
            recs.append({
                'priority': 'High',
                'category': 'Label Integrity',
                'action': f"Review suspected mislabels. Confident learning flagged {noise*100:.1f}% of labels as highly suspicious."
            })
            
        # 5. Confounds
        confounds = self.agg.get('confounds', {}).get('detected_confounds', [])
        for c in confounds:
            recs.append({
                'priority': 'Critical',
                'category': 'Cross-Dimensional Confound',
                'action': f"Investigate Confound: {c['description']}. This is a critical structural issue that standard metric tracking will not catch."
            })
            
        # 6. Overall Readiness fallback
        if not recs:
            recs.append({
                'priority': 'Low',
                'category': 'General',
                'action': "Dataset appears healthy across all standard checks. Proceed to training."
            })
            
        return recs
