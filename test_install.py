"""
Quick test script to verify the installation
"""

print("Testing imports...")

try:
    import torch
    print(f"✓ PyTorch {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")

    import torchvision
    print(f"✓ TorchVision {torchvision.__version__}")

    from transformers import CLIPModel, CLIPProcessor
    print("✓ Transformers (CLIP)")

    from PIL import Image
    print("✓ Pillow")

    from rembg import remove
    print("✓ Rembg")

    import numpy as np
    print(f"✓ NumPy {np.__version__}")

    from sklearn.metrics.pairwise import cosine_similarity
    print("✓ Scikit-learn")

    from tqdm import tqdm
    print("✓ tqdm")

    print("\n" + "="*50)
    print("All dependencies installed successfully!")
    print("="*50)
    print("\nYou can now run:")
    print("  python main.py <your_image_folder>")

except ImportError as e:
    print(f"✗ Error: {e}")
    print("Please run: pip install -e .")
