import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from .base import BaseAnalyzer
from typing import Dict, Any

class QualityAnalyzer(BaseAnalyzer):
    """
    Computes no-reference image quality metrics per sample.
    (REQ-25)
    """
    def run(self) -> Dict[str, Any]:
        
        blur_scores = []
        brightness_scores = []
        contrast_scores = []
        resolutions = []
        aspect_ratios = []
        
        for path in self.df['path']:
            img = cv2.imread(path)
            if img is None:
                # Handle corrupt image (REQ-30)
                blur_scores.append(np.nan)
                brightness_scores.append(np.nan)
                contrast_scores.append(np.nan)
                resolutions.append(np.nan)
                aspect_ratios.append(np.nan)
                continue
                
            h, w = img.shape[:2]
            resolutions.append(h * w)
            aspect_ratios.append(w / h if h > 0 else 0)
            
            # Blur (Variance of Laplacian)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_scores.append(blur)
            
            # Brightness / Contrast using LAB L* channel
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel = lab[:,:,0]
            brightness = l_channel.mean()
            contrast = l_channel.std()
            
            brightness_scores.append(brightness)
            contrast_scores.append(contrast)
            
        self.df['quality_blur'] = blur_scores
        self.df['quality_brightness'] = brightness_scores
        self.df['quality_contrast'] = contrast_scores
        self.df['quality_resolution'] = resolutions
        self.df['quality_aspect_ratio'] = aspect_ratios
        
        # Flags (REQ-27)
        self.df['flag_blurred'] = self.df['quality_blur'] < 100
        self.df['flag_underexposed'] = self.df['quality_brightness'] < 40
        self.df['flag_overexposed'] = self.df['quality_brightness'] > 215
        self.df['flag_low_contrast'] = self.df['quality_contrast'] < 20
        
        return {
            'mean_blur': np.nanmean(blur_scores),
            'mean_brightness': np.nanmean(brightness_scores),
            'pct_blurred': self.df['flag_blurred'].mean() * 100,
            'pct_underexposed': self.df['flag_underexposed'].mean() * 100
        }
