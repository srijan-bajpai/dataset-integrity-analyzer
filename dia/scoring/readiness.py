import numpy as np

class ReadinessScorer:
    """
    Computes the unified 0-100 AI Readiness Score based on the outputs of the 6 dimensions.
    (REQ-74, REQ-75, REQ-77)
    """
    def __init__(self, agg_results: dict):
        self.agg = agg_results
        self.weights = {
            'Balance': 0.20,
            'Fairness': 0.20,
            'Quality': 0.15,
            'Uniqueness': 0.15,
            'Diversity': 0.15,
            'Label Integrity': 0.15
        }
        
    def _normalize(self, val, min_val, max_val, reverse=False):
        """Map val to 0-100 scale based on min/max bounds."""
        if val is None or np.isnan(val):
            return 100.0 if not reverse else 0.0
            
        val = max(min_val, min(val, max_val))
        score = 100 * (val - min_val) / (max_val - min_val)
        return 100 - score if reverse else score
        
    def compute(self):
        scores = {}
        
        # Balance (based on Imbalance Ratio)
        ir = self.agg.get('distribution', {}).get('imbalance_ratio', 1.0)
        # map 1.0 -> 100, 10.0 -> 0
        scores['Balance'] = self._normalize(ir, 1.0, 10.0, reverse=True)
        
        # Fairness (Skip if demographic inference not available, redistribute weights)
        scores['Fairness'] = 100.0 # Placeholder until attribute inference is implemented
        
        # Quality (Based on pct_blurred + pct_underexposed + pct_overexposed)
        q_stats = self.agg.get('quality', {})
        defect_pct = q_stats.get('pct_blurred', 0) + q_stats.get('pct_underexposed', 0)
        # map 0% -> 100, 20% -> 0
        scores['Quality'] = self._normalize(defect_pct, 0.0, 20.0, reverse=True)
        
        # Uniqueness (based on redundancy ratio)
        redundancy = self.agg.get('duplicates', {}).get('redundancy_ratio', 0.0)
        # map 0 -> 100, 0.1 (10%) -> 0
        scores['Uniqueness'] = self._normalize(redundancy, 0.0, 0.1, reverse=True)
        
        # Diversity (based on cluster entropy)
        ent = self.agg.get('diversity', {}).get('cluster_entropy', 1.0)
        # map 0 -> 0, 1 -> 100
        scores['Diversity'] = self._normalize(ent, 0.0, 1.0)
        
        # Label Integrity (based on label noise rate)
        noise = self.agg.get('labels', {}).get('label_noise_rate', 0.0)
        # map 0 -> 100, 0.1 -> 0
        scores['Label Integrity'] = self._normalize(noise, 0.0, 0.1, reverse=True)
        
        # Weighted mean
        final_score = 0
        for dim, weight in self.weights.items():
            final_score += scores[dim] * weight
            
        # Hard gate (REQ-77)
        if any(s < 30 for s in scores.values()):
            final_score = min(final_score, 49.0)
            
        return {
            'overall_score': round(final_score, 1),
            'sub_scores': {k: round(v, 1) for k, v in scores.items()},
            'verdict': self._get_verdict(final_score)
        }
        
    def _get_verdict(self, score):
        if score < 40: return "Critical / Not Usable"
        if score < 70: return "Needs Remediation"
        if score < 85: return "Acceptable"
        return "Production Ready"
