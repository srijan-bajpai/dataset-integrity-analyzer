import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from .base import BaseAnalyzer
from typing import Dict, Any

class LabelAuditAnalyzer(BaseAnalyzer):
    """
    Identifies probable mislabels by training a surrogate classifier on embeddings.
    (REQ-47, REQ-48)
    """
    def __init__(self, df: pd.DataFrame, embeddings: np.ndarray):
        super().__init__(df)
        self.embeddings = embeddings
        
    def run(self) -> Dict[str, Any]:
        y_true = self.df['ground_truth_class'].values
        classes = np.unique(y_true)
        
        counts = np.unique(y_true, return_counts=True)[1]
        min_samples = np.min(counts) if len(counts) > 0 else 0
        
        if len(classes) < 2 or min_samples < 2:
            self.df['label_issue_prob'] = np.nan
            self.df['flag_suspected_mislabel'] = False
            self.df['predicted_class'] = None
            return {'status': 'unavailable', 'label_noise_rate': None,
                    'reason': 'At least two classes with two samples each are required for out-of-fold review.'}
            
        n_splits = min(5, min_samples)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        model = LogisticRegression(max_iter=1000, class_weight='balanced')
        
        pred_probs = np.zeros((len(y_true), len(classes)))
        
        try:
            for train_idx, val_idx in cv.split(self.embeddings, y_true):
                X_train, X_val = self.embeddings[train_idx], self.embeddings[val_idx]
                y_train = y_true[train_idx]
                
                model.fit(X_train, y_train)
                # Map to correct columns in pred_probs based on model.classes_
                probs = model.predict_proba(X_val)
                for i, c in enumerate(model.classes_):
                    c_idx = np.where(classes == c)[0][0]
                    pred_probs[val_idx, c_idx] = probs[:, i]
        except ValueError:
            # Fails if some classes have too few samples for k-fold
            self.df['label_issue_prob'] = np.nan
            self.df['flag_suspected_mislabel'] = False
            self.df['predicted_class'] = None
            return {'status': 'unavailable', 'label_noise_rate': None,
                    'reason': 'The cross-validation model could not be fit for this class distribution.'}
            
        # Confident learning simplified approximation:
        # Flag if predicted probability of another class > probability of given class
        suspected_mislabels = []
        issue_probs = []
        predicted_classes = []
        
        for i in range(len(y_true)):
            true_c_idx = np.where(classes == y_true[i])[0][0]
            true_prob = pred_probs[i, true_c_idx]
            max_prob = np.max(pred_probs[i])
            pred_c_idx = np.argmax(pred_probs[i])
            
            is_mislabel = (max_prob > true_prob) and (pred_c_idx != true_c_idx)
            
            suspected_mislabels.append(is_mislabel)
            issue_probs.append(max_prob - true_prob)
            predicted_classes.append(classes[pred_c_idx])
            
        self.df['label_issue_prob'] = issue_probs
        self.df['flag_suspected_mislabel'] = suspected_mislabels
        self.df['predicted_class'] = predicted_classes
        
        noise_rate = np.mean(suspected_mislabels)
        
        return {
            'status': 'available', 'label_noise_rate': noise_rate,
            'suspected_count': int(np.sum(suspected_mislabels)),
            'sample_count': int(len(y_true)), 'cross_validation_folds': int(n_splits),
            'method': 'stratified out-of-fold logistic regression on ResNet-18 embeddings',
            'caveat': 'Disagreements are review signals, not verified label errors; model representation and class ambiguity can cause them.',
        }
