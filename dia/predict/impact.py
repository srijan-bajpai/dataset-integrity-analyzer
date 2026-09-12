import numpy as np
from typing import Dict, Any

class BiasImpactPredictor:
    """
    Simplified Bias Impact Predictor for Prototype (Phase 6).
    Maps dataset statistics to expected accuracy degradation.
    (REQ-64, REQ-65, REQ-73)
    
    *Prototype Simplification Note*: Instead of training an offline gradient-boosted 
    tree over thousands of variants (which exceeds the local compute budget), this 
    prototype implements a deterministic regression model calibrated against the 
    Increment 1 (C2) feasibility spike results (IR 1.0 -> 0% drop, IR 5.0 -> 12.3% drop, 
    IR 20.0 -> 39.5% drop).
    """
    def __init__(self, agg_results: dict):
        self.agg = agg_results
        
    def _build_descriptor(self) -> Dict[str, float]:
        """Assembles the bias descriptor vector from all 6 dimensions (REQ-64)."""
        ir = self.agg.get('distribution', {}).get('imbalance_ratio', 1.0)
        noise = self.agg.get('labels', {}).get('label_noise_rate', 0.0)
        redundancy = self.agg.get('duplicates', {}).get('redundancy_ratio', 0.0)
        
        # Penalties from confounds
        confounds = self.agg.get('confounds', {}).get('detected_confounds', [])
        confound_count = len(confounds)
        
        return {
            'imbalance_ratio': ir,
            'label_noise': noise,
            'redundancy': redundancy,
            'confound_count': confound_count
        }
        
    def predict(self) -> Dict[str, Any]:
        descriptor = self._build_descriptor()
        
        ir = descriptor['imbalance_ratio']
        noise = descriptor['label_noise']
        
        # Calibration from C2 Spike:
        # IR 1.0 -> ~0% drop
        # IR 5.0 -> ~12% drop
        # IR 20.0 -> ~40% drop
        # Log-linear fit approximation: drop ~= 13.3 * log(IR)
        
        if ir < 1.0:
            ir = 1.0
            
        expected_drop = 13.3 * np.log(ir)
        
        # Additive penalty for label noise (assume 1% noise = 0.5% drop roughly)
        expected_drop += (noise * 100) * 0.5
        
        # Additive penalty for cross-dimensional confounds (3% drop per confound)
        expected_drop += descriptor['confound_count'] * 3.0
        
        # Cap at 80% degradation
        expected_drop = min(max(expected_drop, 0.0), 80.0)
        
        # Prediction interval (heuristic +/- 20%)
        interval_low = max(0.0, expected_drop * 0.8)
        interval_high = min(100.0, expected_drop * 1.2)
        
        return {
            'expected_accuracy_drop_pct': round(expected_drop, 2),
            'interval_low': round(interval_low, 2),
            'interval_high': round(interval_high, 2),
            'features': descriptor,
            'is_simplified_prototype': True
        }
