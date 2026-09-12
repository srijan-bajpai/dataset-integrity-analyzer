import os
import pandas as pd
from pathlib import Path
from typing import Optional, List

class DatasetRecord:
    """
    The unified per-sample record manager for the DIA framework.
    All analyzers read from and write to this shared representation.
    """
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.df: Optional[pd.DataFrame] = None
        self.classes: List[str] = []
        
    def ingest_folder_per_class(self):
        """
        Ingest a dataset organized in folder-per-class layout.
        Example:
        root/
          class_A/
            img1.jpg
          class_B/
            img2.jpg
        """
        records = []
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
        
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Dataset root {self.root_dir} not found.")
            
        for class_dir in self.root_dir.iterdir():
            if class_dir.is_dir():
                class_name = class_dir.name
                if class_name not in self.classes:
                    self.classes.append(class_name)
                    
                for file_path in class_dir.iterdir():
                    if file_path.suffix.lower() in valid_extensions:
                        records.append({
                            'sample_id': str(file_path.relative_to(self.root_dir)),
                            'path': str(file_path.absolute()),
                            'ground_truth_class': class_name,
                            'split': 'train' # Default to train, can be updated later
                        })
                        
        self.df = pd.DataFrame(records)
        if len(self.classes) < 2:
            raise ValueError(f"Dataset must contain at least two classes. Found: {self.classes}")
        
        print(f"Ingested {len(self.df)} samples across {len(self.classes)} classes.")
        return self.df

    def save_to_sqlite(self, db_path: str = "dia_run.db"):
        import sqlite3
        conn = sqlite3.connect(db_path)
        self.df.to_sql('samples', conn, if_exists='replace', index=False)
        conn.close()
