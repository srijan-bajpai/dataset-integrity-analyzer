import pandas as pd
from typing import Dict, Any

class BaseAnalyzer:
    """
    Base class for all single-axis dataset analyzers.
    Each analyzer takes the shared Pandas DataFrame, runs its logic, 
    and writes its per-sample results back as new columns.
    It can also return dataset-level aggregate statistics.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def run(self) -> Dict[str, Any]:
        """
        Execute the analysis.
        Returns a dictionary of dataset-level or class-level aggregate metrics.
        The per-sample metrics should be added directly as new columns to self.df.
        """
        raise NotImplementedError
