import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import pandas as pd
import numpy as np
from pathlib import Path

class FeatureExtractor:
    """
    Extracts embeddings for the dataset using a pre-trained ResNet-18.
    These embeddings are used by Diversity, Duplicates (cosine sim), and Label Audit analyzers.
    (REQ-40)
    """
    def __init__(self, df: pd.DataFrame, batch_size=32):
        self.df = df
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load pre-trained model and remove the classification head
        base_model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        self.model = torch.nn.Sequential(*(list(base_model.children())[:-1]))
        self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
    def extract(self, output_path: str = "embeddings.npy", progress_callback=None) -> np.ndarray:
        embeddings = []
        paths = self.df['path'].tolist()
        
        print(f"Extracting embeddings for {len(paths)} samples on {self.device}...")
        
        with torch.no_grad():
            for i in range(0, len(paths), self.batch_size):
                if progress_callback:
                    progress_callback(45 + int(25 * i / max(len(paths), 1)), f"Extracting image embeddings ({min(i + self.batch_size, len(paths))}/{len(paths)})")
                batch_paths = paths[i:i+self.batch_size]
                batch_tensors = []
                valid_indices = []
                
                for idx, p in enumerate(batch_paths):
                    try:
                        img = Image.open(p).convert('RGB')
                        batch_tensors.append(self.transform(img))
                        valid_indices.append(idx)
                    except Exception:
                        # Fallback for corrupt images
                        batch_tensors.append(torch.zeros(3, 224, 224))
                        
                if not batch_tensors:
                    continue
                    
                batch_tensors = torch.stack(batch_tensors).to(self.device)
                out = self.model(batch_tensors)
                out = out.view(out.size(0), -1) # Flatten to (batch_size, 512)
                
                embeddings.append(out.cpu().numpy())
                
        all_embeddings = np.vstack(embeddings)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        np.save(output, all_embeddings)
        self.df['embedding_ref'] = str(output)
        if progress_callback:
            progress_callback(70, "Image embeddings complete")
        
        return all_embeddings
