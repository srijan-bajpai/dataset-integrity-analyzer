import pandas as pd
import imagehash
from PIL import Image
from collections import defaultdict
from .base import BaseAnalyzer
from typing import Dict, Any

class DuplicatesAnalyzer(BaseAnalyzer):
    """
    Detects exact and near-duplicates using perceptual hashing.
    (REQ-32, REQ-33, REQ-36)
    """
    def run(self) -> Dict[str, Any]:
        hashes = []
        
        # Compute hashes
        for path in self.df['path']:
            try:
                img = Image.open(path)
                h = imagehash.phash(img)
                hashes.append(str(h))
            except Exception:
                hashes.append(None)
                
        self.df['phash'] = hashes
        
        # Detect exact duplicates
        duplicate_groups = {}
        group_id = 0
        
        # Group by hash
        hash_to_indices = defaultdict(list)
        for idx, h in enumerate(hashes):
            if h is not None:
                hash_to_indices[h].append(idx)
                
        exact_dups = 0
        dup_group_column = [None] * len(self.df)
        
        for h, indices in hash_to_indices.items():
            if len(indices) > 1:
                exact_dups += len(indices) - 1
                for idx in indices:
                    dup_group_column[idx] = group_id
                group_id += 1
                
        self.df['duplicate_group'] = dup_group_column
        
        redundancy_ratio = exact_dups / len(self.df) if len(self.df) > 0 else 0
        
        return {
            'exact_duplicates': exact_dups,
            'redundancy_ratio': redundancy_ratio,
            'duplicate_groups': group_id
        }
