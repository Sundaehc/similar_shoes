"""
Background removal module for shoe images.
Uses rembg to remove backgrounds and focus on shoe features.
"""

from PIL import Image
from rembg import remove
import io
import numpy as np
from typing import Union
from pathlib import Path


class BackgroundRemover:
    """Handles background removal from shoe images."""

    def __init__(self):
        """Initialize the background remover."""
        pass

    def remove_background(self, image: Union[str, Path, Image.Image]) -> Image.Image:
        """
        Remove background from an image.

        Args:
            image: Path to image file or PIL Image object

        Returns:
            PIL Image with background removed
        """
        # Load image if path is provided
        if isinstance(image, (str, Path)):
            input_image = Image.open(image)
        else:
            input_image = image

        # Convert to RGB if necessary
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')

        # Remove background
        output_image = remove(input_image)

        return output_image

    def process_and_save(self, input_path: Union[str, Path],
                        output_path: Union[str, Path]) -> None:
        """
        Process an image and save the result.

        Args:
            input_path: Path to input image
            output_path: Path to save output image
        """
        output_image = self.remove_background(input_path)
        output_image.save(output_path)
