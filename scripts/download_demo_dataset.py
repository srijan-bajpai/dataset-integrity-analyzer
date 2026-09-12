import os
import torchvision
import cv2
import numpy as np

def create_demo_dataset(root_dir="data/demo_dataset"):
    print("Downloading CIFAR-10...")
    dataset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True)
    
    classes = dataset.classes
    # We will only extract 3 classes to keep it fast
    target_classes = ['airplane', 'automobile', 'bird']
    
    print("Creating folder structure and injecting defects...")
    os.makedirs(root_dir, exist_ok=True)
    for c in target_classes:
        os.makedirs(os.path.join(root_dir, c), exist_ok=True)
        
    counts = {c: 0 for c in target_classes}
    # Deliberate imbalance: 200 airplane, 50 automobile, 50 bird
    target_counts = {'airplane': 200, 'automobile': 50, 'bird': 50}
    
    for idx, (img, label_idx) in enumerate(dataset):
        c_name = classes[label_idx]
        
        if c_name in target_classes:
            if counts[c_name] < target_counts[c_name]:
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Defect 1: Blur all birds to create a Quality x Class confound
                if c_name == 'bird':
                    img_cv = cv2.GaussianBlur(img_cv, (5, 5), 3.0)
                    
                path = os.path.join(root_dir, c_name, f"{c_name}_{idx}.jpg")
                cv2.imwrite(path, img_cv)
                
                # Defect 2: Duplicate some automobiles
                if c_name == 'automobile' and counts[c_name] < 10:
                    dup_path = os.path.join(root_dir, c_name, f"{c_name}_{idx}_dup.jpg")
                    cv2.imwrite(dup_path, img_cv)
                    
                counts[c_name] += 1
                
        if all(counts[c] >= target_counts[c] for c in target_classes):
            break
            
    print(f"Created demo dataset at {root_dir}")
    print(f"Final counts: {counts}")

if __name__ == "__main__":
    create_demo_dataset()
