"""
Similarity calculation and clustering for shoe images.
Groups similar shoes together and identifies representative styles.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from typing import List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SimilarityGroup:
    """Represents a group of similar shoe images."""
    representative_idx: int  # Index of the representative image
    representative_path: Path  # Path to representative image
    similar_indices: List[int]  # Indices of similar images
    similar_paths: List[Path]  # Paths to similar images
    similarity_scores: List[float]  # Similarity scores to representative


class ShoeSimilarityAnalyzer:
    """Analyzes similarity between shoe images and creates clusters."""

    def __init__(self, duplicate_threshold: float = 0.95,
                 similar_threshold: float = 0.85):
        """
        Initialize the similarity analyzer.

        Args:
            duplicate_threshold: Threshold for considering shoes as duplicates (0-1)
            similar_threshold: Threshold for considering shoes as similar (0-1)
        """
        self.duplicate_threshold = duplicate_threshold
        self.similar_threshold = similar_threshold

    def calculate_similarity_matrix(self, features: np.ndarray) -> np.ndarray:
        """
        Calculate pairwise similarity matrix.

        Args:
            features: Feature vectors (n_images, feature_dim)

        Returns:
            Similarity matrix (n_images, n_images)
        """
        return cosine_similarity(features)

    def find_similar_groups(self, features: np.ndarray,
                           image_paths: List[Path]) -> Dict[str, List[SimilarityGroup]]:
        """
        Find groups of similar shoes.

        Args:
            features: Feature vectors (n_images, feature_dim)
            image_paths: List of image paths corresponding to features

        Returns:
            Dictionary with 'duplicates' and 'similar' groups
        """
        similarity_matrix = self.calculate_similarity_matrix(features)
        n_images = len(image_paths)

        # Track which images have been assigned to groups
        assigned = set()
        duplicate_groups = []
        similar_groups = []

        for i in range(n_images):
            if i in assigned:
                continue

            # Find images similar to current image
            similarities = similarity_matrix[i]

            # Find duplicates (very high similarity)
            duplicate_mask = (similarities >= self.duplicate_threshold) & (np.arange(n_images) != i)
            duplicate_indices = np.where(duplicate_mask)[0].tolist()

            # Find similar but not duplicate
            similar_mask = (similarities >= self.similar_threshold) & \
                          (similarities < self.duplicate_threshold) & \
                          (np.arange(n_images) != i)
            similar_indices = np.where(similar_mask)[0].tolist()

            # Create duplicate group if found
            if duplicate_indices:
                duplicate_indices_filtered = [idx for idx in duplicate_indices if idx not in assigned]
                if duplicate_indices_filtered:
                    group = SimilarityGroup(
                        representative_idx=i,
                        representative_path=image_paths[i],
                        similar_indices=duplicate_indices_filtered,
                        similar_paths=[image_paths[idx] for idx in duplicate_indices_filtered],
                        similarity_scores=[similarities[idx] for idx in duplicate_indices_filtered]
                    )
                    duplicate_groups.append(group)
                    assigned.add(i)
                    assigned.update(duplicate_indices_filtered)

            # Create similar group if found
            elif similar_indices:
                similar_indices_filtered = [idx for idx in similar_indices if idx not in assigned]
                if similar_indices_filtered:
                    group = SimilarityGroup(
                        representative_idx=i,
                        representative_path=image_paths[i],
                        similar_indices=similar_indices_filtered,
                        similar_paths=[image_paths[idx] for idx in similar_indices_filtered],
                        similarity_scores=[similarities[idx] for idx in similar_indices_filtered]
                    )
                    similar_groups.append(group)
                    assigned.add(i)
                    assigned.update(similar_indices_filtered)

        return {
            'duplicates': duplicate_groups,
            'similar': similar_groups
        }

    def get_unique_shoes(self, features: np.ndarray,
                        image_paths: List[Path]) -> List[Path]:
        """
        Get list of unique shoe images (one per group).

        Args:
            features: Feature vectors
            image_paths: List of image paths

        Returns:
            List of paths to unique/representative shoes
        """
        groups = self.find_similar_groups(features, image_paths)
        assigned_indices = set()

        # Collect representative images
        unique_paths = []

        for group in groups['duplicates'] + groups['similar']:
            unique_paths.append(group.representative_path)
            assigned_indices.add(group.representative_idx)
            assigned_indices.update(group.similar_indices)

        # Add images that weren't grouped
        for i, path in enumerate(image_paths):
            if i not in assigned_indices:
                unique_paths.append(path)

        return unique_paths
