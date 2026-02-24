"""
File organization module for managing output structure.
Organizes similar shoes into grouped folders.
"""

import shutil
from pathlib import Path
from typing import List, Dict
import json
from similarity_analyzer import SimilarityGroup


class FileOrganizer:
    """Organizes shoe images based on similarity analysis."""

    def __init__(self, output_dir: Path):
        """
        Initialize the file organizer.

        Args:
            output_dir: Base directory for organized output
        """
        self.output_dir = Path(output_dir)
        self.similar_groups_dir = self.output_dir / "similar_groups"
        self.unique_dir = self.output_dir / "unique"

    def setup_directories(self):
        """Create necessary output directories."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.similar_groups_dir.mkdir(exist_ok=True)
        self.unique_dir.mkdir(exist_ok=True)

    def organize_groups(self, groups: Dict[str, List[SimilarityGroup]]):
        """
        Organize images based on similarity groups.
        Each group folder contains ALL similar shoes (including representative).

        Args:
            groups: Dictionary with 'duplicates' and 'similar' groups
        """
        self.setup_directories()

        group_counter = 0

        # Process duplicate groups (very high similarity)
        for group in groups['duplicates']:
            group_folder = self.similar_groups_dir / f"duplicate_group_{group_counter:04d}"
            group_folder.mkdir(exist_ok=True)

            # Copy representative (marked as rep)
            rep_dest = group_folder / f"rep_{group.representative_path.name}"
            shutil.copy2(group.representative_path, rep_dest)

            # Copy all similar images
            for path, score in zip(group.similar_paths, group.similarity_scores):
                dest_name = f"sim_{score:.3f}_{path.name}"
                shutil.copy2(path, group_folder / dest_name)

            # Save group info
            self._save_group_info(group_folder, group, "duplicate", group_counter)
            group_counter += 1

        # Process similar groups (moderate similarity)
        for group in groups['similar']:
            group_folder = self.similar_groups_dir / f"similar_group_{group_counter:04d}"
            group_folder.mkdir(exist_ok=True)

            # Copy representative (marked as rep)
            rep_dest = group_folder / f"rep_{group.representative_path.name}"
            shutil.copy2(group.representative_path, rep_dest)

            # Copy all similar images
            for path, score in zip(group.similar_paths, group.similarity_scores):
                dest_name = f"sim_{score:.3f}_{path.name}"
                shutil.copy2(path, group_folder / dest_name)

            # Save group info
            self._save_group_info(group_folder, group, "similar", group_counter)
            group_counter += 1

        print(f"\nCreated {group_counter} similarity groups")

    def _save_group_info(self, folder: Path, group: SimilarityGroup,
                        group_type: str, group_id: int):
        """
        Save group information to JSON file.

        Args:
            folder: Folder to save info in
            group: Similarity group
            group_type: Type of group ('duplicate' or 'similar')
            group_id: Group ID number
        """
        info = {
            "group_id": group_id,
            "type": group_type,
            "total_images": len(group.similar_paths) + 1,
            "representative": {
                "path": str(group.representative_path),
                "filename": group.representative_path.name
            },
            "similar_images": [
                {
                    "path": str(path),
                    "filename": path.name,
                    "similarity_score": float(score)
                }
                for path, score in zip(group.similar_paths, group.similarity_scores)
            ]
        }

        with open(folder / "group_info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

    def copy_unique_shoes(self, unique_paths: List[Path]):
        """
        Copy unique shoes that don't belong to any group.

        Args:
            unique_paths: List of paths to unique shoes
        """
        self.unique_dir.mkdir(exist_ok=True)

        for path in unique_paths:
            shutil.copy2(path, self.unique_dir / path.name)

        print(f"Copied {len(unique_paths)} unique shoes")