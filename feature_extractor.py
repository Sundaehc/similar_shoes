"""
CLIP-based feature extraction for shoe images.
Extracts semantic features that capture style, design, and visual characteristics.
"""

import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from typing import Union, List
from pathlib import Path


class ShoeFeatureExtractor:
    """Extracts features from shoe images using CLIP model."""

    def __init__(self, model_name: str = "openai/clip-vit-large-patch14"):
        """
        Initialize the feature extractor.

        Args:
            model_name: Name of the CLIP model to use
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Load CLIP model and processor
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

    def extract_features(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        """
        Extract feature vector from an image.

        Args:
            image: Path to image file or PIL Image object

        Returns:
            Feature vector as numpy array
        """
        # Load image if path is provided
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        else:
            img = image

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Process image
        inputs = self.processor(images=img, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Extract features
        with torch.no_grad():
            out = self.model.get_image_features(**inputs)

        # get_image_features 可能返回张量或 BaseModelOutputWithPooling（因 transformers 版本不同）
        if not isinstance(out, torch.Tensor):
            image_features = (
                out.pooler_output
                if getattr(out, "pooler_output", None) is not None
                else out.last_hidden_state[:, 0]
            )
        else:
            image_features = out

        # Normalize features
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        return image_features.cpu().numpy().flatten()

    def extract_batch_features(self, images: List[Union[str, Path, Image.Image]]) -> np.ndarray:
        """
        Extract features from multiple images.

        Args:
            images: List of image paths or PIL Image objects

        Returns:
            Array of feature vectors (n_images, feature_dim)
        """
        features = []
        for img in images:
            feat = self.extract_features(img)
            features.append(feat)

        return np.array(features)
