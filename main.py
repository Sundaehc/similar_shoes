"""
Shoe Image Similarity Detection System
Main workflow for processing shoe images and finding similar styles.
"""

import argparse
from pathlib import Path
from typing import List
import json
from tqdm import tqdm

from background_remover import BackgroundRemover
from feature_extractor import ShoeFeatureExtractor
from similarity_analyzer import ShoeSimilarityAnalyzer
from file_organizer import FileOrganizer


def get_image_files(directory: Path) -> List[Path]:
    """
    Get all image files from a directory.

    Args:
        directory: Directory to search

    Returns:
        List of image file paths
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    image_files = []

    for ext in image_extensions:
        image_files.extend(directory.glob(f"*{ext}"))
        image_files.extend(directory.glob(f"*{ext.upper()}"))

    return sorted(image_files)


def process_folder(input_dir: Path, output_dir: Path,
                  remove_bg: bool = True,
                  duplicate_threshold: float = 0.95,
                  similar_threshold: float = 0.85):
    """
    Process a folder of shoe images.

    Args:
        input_dir: Input directory with shoe images
        output_dir: Output directory for organized results
        remove_bg: Whether to remove backgrounds
        duplicate_threshold: Threshold for duplicates
        similar_threshold: Threshold for similar images
    """
    print(f"\n{'='*60}")
    print(f"Processing folder: {input_dir}")
    print(f"{'='*60}\n")

    # Get all image files
    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"No image files found in {input_dir}")
        return

    print(f"Found {len(image_files)} images")

    # Step 1: Background removal (optional)
    processed_images = image_files
    if remove_bg:
        print("\nStep 1: Removing backgrounds...")
        bg_remover = BackgroundRemover()
        temp_dir = output_dir / "temp_nobg"
        temp_dir.mkdir(parents=True, exist_ok=True)

        processed_images = []
        for img_path in tqdm(image_files, desc="Removing backgrounds"):
            output_path = temp_dir / img_path.name
            try:
                bg_remover.process_and_save(img_path, output_path)
                processed_images.append(output_path)
            except Exception as e:
                print(f"Warning: Failed to process {img_path.name}: {e}")
                processed_images.append(img_path)  # Use original if processing fails

    # Step 2: Extract features
    print("\nStep 2: Extracting features with CLIP...")
    extractor = ShoeFeatureExtractor()
    features = []
    valid_images = []

    for img_path in tqdm(processed_images, desc="Extracting features"):
        try:
            feat = extractor.extract_features(img_path)
            features.append(feat)
            # Map back to original image path
            original_idx = processed_images.index(img_path)
            valid_images.append(image_files[original_idx])
        except Exception as e:
            print(f"Warning: Failed to extract features from {img_path.name}: {e}")

    if not features:
        print("No features extracted. Exiting.")
        return

    import numpy as np
    features = np.array(features)

    # Step 3: Find similar groups
    print("\nStep 3: Analyzing similarity and clustering...")
    analyzer = ShoeSimilarityAnalyzer(
        duplicate_threshold=duplicate_threshold,
        similar_threshold=similar_threshold
    )
    groups = analyzer.find_similar_groups(features, valid_images)

    print(f"\nFound {len(groups['duplicates'])} duplicate groups")
    print(f"Found {len(groups['similar'])} similar groups")

    # Step 4: Organize files
    print("\nStep 4: Organizing files...")
    organizer = FileOrganizer(output_dir)
    organizer.organize_groups(groups)

    # Copy unique shoes (not in any group)
    unique_shoes = analyzer.get_unique_shoes(features, valid_images)
    assigned_count = sum(len(g.similar_paths) + 1 for g in groups['duplicates'] + groups['similar'])
    unique_count = len(valid_images) - assigned_count

    if unique_count > 0:
        # Find which shoes are not in any group
        assigned_paths = set()
        for group in groups['duplicates'] + groups['similar']:
            assigned_paths.add(group.representative_path)
            assigned_paths.update(group.similar_paths)

        unique_paths = [path for path in valid_images if path not in assigned_paths]
        organizer.copy_unique_shoes(unique_paths)

    # Save summary
    summary = {
        "total_images": len(image_files),
        "processed_images": len(valid_images),
        "duplicate_groups": len(groups['duplicates']),
        "similar_groups": len(groups['similar']),
        "unique_shoes": unique_count,
        "settings": {
            "duplicate_threshold": duplicate_threshold,
            "similar_threshold": similar_threshold,
            "background_removal": remove_bg
        }
    }

    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("Processing complete!")
    print(f"Results saved to: {output_dir}")
    print(f"  - {len(groups['duplicates']) + len(groups['similar'])} similarity groups")
    print(f"  - {unique_count} unique shoes")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered shoe image similarity detection"
    )
    parser.add_argument(
        "input_dir",
        type=str,
        help="Input directory containing shoe images"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--no-bg-removal",
        action="store_true",
        help="Skip background removal"
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.80,
        help="Similarity threshold for duplicates (default: 0.80)"
    )
    parser.add_argument(
        "--similar-threshold",
        type=float,
        default=0.70,
        help="Similarity threshold for similar images (default: 0.70)"
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return

    output_dir = Path(args.output)

    process_folder(
        input_dir=input_dir,
        output_dir=output_dir,
        remove_bg=not args.no_bg_removal,
        duplicate_threshold=args.duplicate_threshold,
        similar_threshold=args.similar_threshold
    )


if __name__ == "__main__":
    main()
