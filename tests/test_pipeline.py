import os
import cv2
import numpy as np
from pathlib import Path

def create_dummy_dataset(root="test_data"):
    """Create a tiny dummy dataset for testing the pipeline."""
    os.makedirs(os.path.join(root, "class_A"), exist_ok=True)
    os.makedirs(os.path.join(root, "class_B"), exist_ok=True)
    
    # Create 5 images for A, 2 for B (imbalanced)
    for i in range(5):
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        cv2.imwrite(os.path.join(root, "class_A", f"img_{i}.jpg"), img)
        
    for i in range(2):
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        cv2.imwrite(os.path.join(root, "class_B", f"img_{i}.jpg"), img)
        
    # Create one exact duplicate in A
    cv2.imwrite(os.path.join(root, "class_A", "img_dup.jpg"), img)
        
if __name__ == "__main__":
    from dia.core.orchestrator import DIAOrchestrator
    
    print("Creating dummy dataset...")
    create_dummy_dataset()
    
    print("Running DIA Orchestrator...")
    orchestrator = DIAOrchestrator("test_data")
    agg_res, df = orchestrator.run_all()
    
    print("\n--- Pipeline Completed ---")
    print(f"Readiness Score: {agg_res['readiness']['overall_score']}")
    print(f"Verdict: {agg_res['readiness']['verdict']}")
    print("\nDimension Sub-Scores:")
    for k, v in agg_res['readiness']['sub_scores'].items():
        print(f"  {k}: {v}")
