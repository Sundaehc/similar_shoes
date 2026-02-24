"""
Faiss-based vector index for fast similarity search.
Supports building, saving, loading, and searching image feature vectors.
"""

import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import json


class VectorIndex:
    """Manages a Faiss index for fast similarity search."""

    def __init__(self, dimension: int = 768):
        """
        Initialize the vector index.

        Args:
            dimension: Dimension of feature vectors (CLIP-ViT-Large: 768)
        """
        self.dimension = dimension
        self.index = None
        self.image_paths = []  # Store image paths corresponding to vectors
        self.metadata = {}  # Store additional metadata for each image

    def build_index(self, features: np.ndarray, image_paths: List[Path],
                   metadata: Optional[List[Dict]] = None, use_gpu: bool = False):
        """
        Build a Faiss index from feature vectors.

        Args:
            features: Feature vectors (n_images, dimension)
            image_paths: List of image file paths
            metadata: Optional metadata for each image
            use_gpu: Whether to use GPU for indexing (faster for large datasets)
        """
        if features.shape[1] != self.dimension:
            raise ValueError(f"Feature dimension {features.shape[1]} doesn't match {self.dimension}")

        # Normalize features for cosine similarity
        faiss.normalize_L2(features)

        # Create index (using Inner Product for normalized vectors = cosine similarity)
        if use_gpu and faiss.get_num_gpus() > 0:
            # GPU index for faster search
            res = faiss.StandardGpuResources()
            self.index = faiss.GpuIndexFlatIP(res, self.dimension)
        else:
            # CPU index
            self.index = faiss.IndexFlatIP(self.dimension)

        # Add vectors to index
        self.index.add(features.astype('float32'))
        self.image_paths = [str(p) for p in image_paths]

        if metadata:
            self.metadata = {str(path): meta for path, meta in zip(image_paths, metadata)}

        print(f"Built index with {self.index.ntotal} vectors")

    def search(self, query_features: np.ndarray, k: int = 10,
               min_similarity: float = 0.0) -> List[Tuple[str, float]]:
        """
        Search for similar images.

        Args:
            query_features: Query feature vector (1, dimension) or (dimension,)
            k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of (image_path, similarity_score) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Ensure query is 2D
        if query_features.ndim == 1:
            query_features = query_features.reshape(1, -1)

        # Normalize query
        faiss.normalize_L2(query_features)

        # Search
        similarities, indices = self.index.search(query_features.astype('float32'), k)

        # Filter and format results
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx != -1 and sim >= min_similarity:  # -1 means no result
                results.append((self.image_paths[idx], float(sim)))

        return results

    def save(self, save_dir: Path):
        """
        Save index and metadata to disk.

        Args:
            save_dir: Directory to save index files
        """
        if self.index is None:
            raise ValueError("No index to save")

        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save Faiss index
        index_path = save_dir / "faiss.index"
        faiss.write_index(faiss.index_gpu_to_cpu(self.index) if hasattr(self.index, 'getDevice')
                         else self.index, str(index_path))

        # Save image paths and metadata
        data = {
            'image_paths': self.image_paths,
            'metadata': self.metadata,
            'dimension': self.dimension
        }
        with open(save_dir / "index_data.pkl", 'wb') as f:
            pickle.dump(data, f)

        print(f"Index saved to {save_dir}")

    def load(self, save_dir: Path, use_gpu: bool = False):
        """
        Load index and metadata from disk.

        Args:
            save_dir: Directory containing index files
            use_gpu: Whether to load index to GPU
        """
        save_dir = Path(save_dir)

        # Load Faiss index
        index_path = save_dir / "faiss.index"
        self.index = faiss.read_index(str(index_path))

        if use_gpu and faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)

        # Load image paths and metadata
        with open(save_dir / "index_data.pkl", 'rb') as f:
            data = pickle.load(f)

        self.image_paths = data['image_paths']
        self.metadata = data['metadata']
        self.dimension = data['dimension']

        print(f"Loaded index with {self.index.ntotal} vectors")

    def add_images(self, features: np.ndarray, image_paths: List[Path],
                   metadata: Optional[List[Dict]] = None):
        """
        Add new images to existing index.

        Args:
            features: Feature vectors to add
            image_paths: Image paths
            metadata: Optional metadata
        """
        if self.index is None:
            raise ValueError("Index not initialized. Call build_index() first.")

        faiss.normalize_L2(features)
        self.index.add(features.astype('float32'))

        self.image_paths.extend([str(p) for p in image_paths])

        if metadata:
            for path, meta in zip(image_paths, metadata):
                self.metadata[str(path)] = meta

        print(f"Added {len(image_paths)} images. Total: {self.index.ntotal}")

    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'total_images': len(self.image_paths)
        }
