"""
Image search functionality - find similar shoes by uploading an image.
Supports both command-line and programmatic usage.
"""

import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import shutil
import yaml

from feature_extractor import ShoeFeatureExtractor
from vector_index import VectorIndex


def load_config():
    """Load configuration from config.yaml."""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load config.yaml: {e}")
        return {}


class ImageSearchEngine:
    """Search engine for finding similar shoe images."""

    def __init__(self, index_dir: Path, use_gpu: bool = False, model_name: str = None):
        """
        Initialize search engine.

        Args:
            index_dir: Directory containing the pre-built index
            use_gpu: Whether to use GPU for search
            model_name: CLIP model name (if None, uses config or default)
        """
        # Load model name from config if not specified
        if model_name is None:
            config = load_config()
            model_name = config.get('model', {}).get('name', 'openai/clip-vit-large-patch14')

        self.extractor = ShoeFeatureExtractor(model_name=model_name)
        self.index = VectorIndex()
        self.index.load(index_dir, use_gpu=use_gpu)

        print(f"Search engine loaded with {self.index.get_stats()['total_images']} images")

    def search(self, query_image: Path, top_k: int = 10,
               min_similarity: float = 0.5) -> List[Tuple[str, float, dict]]:
        """
        Search for similar images.

        Args:
            query_image: Path to query image
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of (image_path, similarity_score, metadata) tuples
        """
        # Extract features from query image
        query_features = self.extractor.extract_features(query_image)

        # Search in index
        results = self.index.search(query_features, k=top_k, min_similarity=min_similarity)

        # Add metadata
        results_with_meta = []
        for img_path, score in results:
            metadata = self.index.metadata.get(img_path, {})
            results_with_meta.append((img_path, score, metadata))

        return results_with_meta

    def search_and_display(self, query_image: Path, top_k: int = 10,
                          min_similarity: float = 0.5, output_dir: Optional[Path] = None):
        """
        Search and optionally save results.

        Args:
            query_image: Path to query image
            top_k: Number of results
            min_similarity: Minimum similarity
            output_dir: Optional directory to save results
        """
        print(f"\nSearching for images similar to: {query_image.name}")
        print(f"{'='*60}\n")

        results = self.search(query_image, top_k, min_similarity)

        if not results:
            print("No similar images found.")
            return

        print(f"Found {len(results)} similar images:\n")

        for i, (img_path, score, metadata) in enumerate(results, 1):
            print(f"{i}. {Path(img_path).name}")
            print(f"   Similarity: {score:.3f}")
            if metadata:
                print(f"   Metadata: {metadata}")
            print()

        # Save results if output directory specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Copy query image
            query_dest = output_dir / f"query_{query_image.name}"
            shutil.copy2(query_image, query_dest)

            # Copy result images
            for i, (img_path, score, _) in enumerate(results, 1):
                src = Path(img_path)
                dest = output_dir / f"result_{i:02d}_sim{score:.3f}_{src.name}"
                shutil.copy2(src, dest)

            print(f"Results saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Search for similar shoe images"
    )
    parser.add_argument(
        "query_image",
        type=str,
        help="Path to query image"
    )
    parser.add_argument(
        "-i", "--index",
        type=str,
        default="index",
        help="Index directory (default: index)"
    )
    parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )
    parser.add_argument(
        "-s", "--min-similarity",
        type=float,
        default=0.5,
        help="Minimum similarity threshold 0-1 (default: 0.5)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output directory to save results (optional)"
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU for search"
    )

    args = parser.parse_args()

    query_image = Path(args.query_image)
    if not query_image.exists():
        print(f"Error: Query image '{query_image}' does not exist")
        exit(1)

    index_dir = Path(args.index)
    if not index_dir.exists():
        print(f"Error: Index directory '{index_dir}' does not exist")
        print("Please build an index first using: python build_index.py <image_dir>")
        exit(1)

    # Initialize search engine
    engine = ImageSearchEngine(index_dir, use_gpu=args.gpu)

    # Search
    output_dir = Path(args.output) if args.output else None
    engine.search_and_display(query_image, args.top_k, args.min_similarity, output_dir)


if __name__ == "__main__":
    main()
