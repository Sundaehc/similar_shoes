"""
Build vector index from a folder of shoe images.
This script extracts features and creates a searchable index.
"""

import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np
import hashlib
from PIL import Image
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


def get_image_hash(image_path: Path) -> str:
    """Calculate MD5 hash of image file."""
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_image_files(directory: Path):
    """Get all image files from directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.glob(f"*{ext}"))
        image_files.extend(directory.glob(f"*{ext.upper()}"))
    return sorted(image_files)


def deduplicate_images(image_files):
    """Remove duplicate images based on file hash."""
    print("\nChecking for duplicate images...")
    seen_hashes = {}
    unique_images = []
    duplicates = []

    for img_path in tqdm(image_files, desc="Deduplicating"):
        try:
            img_hash = get_image_hash(img_path)
            if img_hash not in seen_hashes:
                seen_hashes[img_hash] = img_path
                unique_images.append(img_path)
            else:
                duplicates.append((img_path, seen_hashes[img_hash]))
        except Exception as e:
            print(f"\nWarning: Failed to hash {img_path.name}: {e}")
            unique_images.append(img_path)  # Keep it if we can't hash

    if duplicates:
        print(f"\nFound {len(duplicates)} duplicate images:")
        for dup, original in duplicates[:10]:  # Show first 10
            print(f"  - {dup.name} (duplicate of {original.name})")
        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more")

    print(f"\nUnique images: {len(unique_images)} (removed {len(duplicates)} duplicates)")
    return unique_images


def build_index(image_dir: Path, index_dir: Path, use_gpu: bool = False, skip_dedup: bool = False, model_name: str = None):
    """
    Build a searchable index from images.

    Args:
        image_dir: Directory containing shoe images
        index_dir: Directory to save the index
        use_gpu: Whether to use GPU for indexing
        skip_dedup: Skip deduplication step
        model_name: CLIP model name (if None, uses config or default)
    """
    print(f"\n{'='*60}")
    print(f"Building Vector Index")
    print(f"{'='*60}\n")

    # Get all images
    image_files = get_image_files(image_dir)
    if not image_files:
        print(f"No images found in {image_dir}")
        return

    print(f"Found {len(image_files)} images")

    # Deduplicate images
    if not skip_dedup:
        image_files = deduplicate_images(image_files)
    else:
        print("\nSkipping deduplication (--skip-dedup flag set)")

    if not image_files:
        print("No images to process after deduplication.")
        return

    # Load model name from config if not specified
    if model_name is None:
        config = load_config()
        model_name = config.get('model', {}).get('name', 'openai/clip-vit-large-patch14')

    # Extract features
    print(f"\nExtracting features with CLIP model: {model_name}")
    extractor = ShoeFeatureExtractor(model_name=model_name)
    features = []
    valid_images = []

    for img_path in tqdm(image_files, desc="Processing"):
        try:
            feat = extractor.extract_features(img_path)
            features.append(feat)
            valid_images.append(img_path)
        except Exception as e:
            print(f"\nWarning: Failed to process {img_path.name}: {e}")

    if not features:
        print("No features extracted. Exiting.")
        return

    features = np.array(features)
    print(f"\nExtracted features from {len(features)} images")

    # Build index
    print("\nBuilding Faiss index...")
    index = VectorIndex(dimension=features.shape[1])

    # Create metadata (optional: add product info, price, etc.)
    metadata = [{'filename': img.name, 'path': str(img)} for img in valid_images]

    index.build_index(features, valid_images, metadata=metadata, use_gpu=use_gpu)

    # Save index
    print(f"\nSaving index to {index_dir}...")
    index.save(index_dir)

    # Print stats
    stats = index.get_stats()
    print(f"\n{'='*60}")
    print("Index built successfully!")
    print(f"{'='*60}")
    print(f"Total images indexed: {stats['total_images']}")
    print(f"Feature dimension: {stats['dimension']}")
    print(f"Index saved to: {index_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a searchable vector index from shoe images"
    )
    parser.add_argument(
        "image_dir",
        type=str,
        help="Directory containing shoe images"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="index",
        help="Output directory for index (default: index)"
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU for indexing (faster for large datasets)"
    )
    parser.add_argument(
        "--skip-dedup",
        action="store_true",
        help="Skip deduplication step (keep all images including duplicates)"
    )

    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    if not image_dir.exists():
        print(f"Error: Directory '{image_dir}' does not exist")
        exit(1)

    index_dir = Path(args.output)
    build_index(image_dir, index_dir, use_gpu=args.gpu, skip_dedup=args.skip_dedup)
