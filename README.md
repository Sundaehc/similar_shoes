# Shoe Image Similarity Detection System

AI-powered system for detecting and clustering similar shoe images using CLIP model and advanced computer vision techniques.

## Features

- **Deep Similarity Analysis**: Uses OpenAI's CLIP model to understand shoe styles, designs, and visual characteristics
- **Background Removal**: Automatically removes backgrounds to focus on shoe features
- **Smart Clustering**: Groups similar shoes with configurable thresholds
- **Organized Output**: Automatically organizes similar shoes into group folders
- **Detailed Reports**: Generates JSON reports with similarity scores and group information

## Installation

1. Install dependencies:
```bash
pip install torch torchvision transformers pillow rembg numpy scikit-learn tqdm
```

Note: First run will download the CLIP model (~350MB) and rembg model (~170MB).

## Usage

### Basic Usage

Process a folder of shoe images:

```bash
python main.py /path/to/shoe/images
```

### Advanced Options

```bash
python main.py /path/to/shoe/images \
  -o output_folder \
  --duplicate-threshold 0.95 \
  --similar-threshold 0.85 \
  --no-bg-removal
```

### Command Line Arguments

- `input_dir`: Input directory containing shoe images (required)
- `-o, --output`: Output directory (default: "output")
- `--duplicate-threshold`: Similarity threshold for duplicates, 0-1 (default: 0.95)
- `--similar-threshold`: Similarity threshold for similar images, 0-1 (default: 0.85)
- `--no-bg-removal`: Skip background removal step

## Output Structure

```
output/
├── similar_groups/              # All similarity groups
│   ├── duplicate_group_0000/    # Duplicate group (similarity ≥0.95)
│   │   ├── rep_shoe1.jpg        # Representative (with rep_ prefix)
│   │   ├── sim_0.972_shoe2.jpg  # Similar shoes (with similarity score)
│   │   ├── sim_0.968_shoe3.jpg
│   │   └── group_info.json      # Group metadata
│   ├── similar_group_0001/      # Similar group (similarity 0.85-0.95)
│   │   ├── rep_shoe5.jpg
│   │   ├── sim_0.891_shoe6.jpg
│   │   └── group_info.json
│   └── ...
├── unique/                      # Unique styles (not in any group)
│   ├── shoe10.jpg
│   └── shoe15.jpg
└── summary.json                 # Processing summary
```

### Key Points

- **Each group folder contains ALL similar shoes** (representative + similar ones)
- Representative images have `rep_` prefix
- Similar images have `sim_SCORE_` prefix showing similarity score
- Unique shoes (not similar to any others) are in the `unique/` folder

## How It Works

### 1. Background Removal (Optional)
Uses the `rembg` library to remove backgrounds, focusing analysis on the shoe itself rather than environmental factors.

### 2. Feature Extraction
Uses CLIP (Contrastive Language-Image Pre-training) to extract semantic features that capture:
- Overall shoe style and design
- Visual patterns and textures
- Shape and silhouette
- Color schemes

### 3. Similarity Analysis
Calculates cosine similarity between feature vectors:
- **Duplicates** (≥0.95): Nearly identical shoes, likely same model
- **Similar** (0.85-0.95): Similar style but with noticeable differences
- **Unique** (<0.85): Distinct designs

### 4. File Organization
Automatically organizes results:
- Groups all similar shoes together in one folder
- Marks representative with `rep_` prefix
- Stores unique shoes separately
- Generates JSON metadata with similarity scores

## Configuration

Edit `config.json` to customize default settings:

```json
{
  "similarity_thresholds": {
    "duplicate": 0.95,
    "similar": 0.85
  },
  "processing": {
    "remove_background": true,
    "clip_model": "openai/clip-vit-base-patch32"
  }
}
```

## Threshold Tuning Guide

- **0.95-1.0**: Extremely similar (same shoe, different angles/lighting)
- **0.85-0.95**: Similar style (same category, similar design elements)
- **0.75-0.85**: Loosely similar (same general type)
- **<0.75**: Different styles

Start with default values and adjust based on your specific needs.

## Performance Notes

- **GPU Recommended**: CLIP model runs much faster on GPU
- **Processing Time**: ~1-2 seconds per image on GPU, ~5-10 seconds on CPU
- **Memory**: Requires ~2GB RAM + model size (~500MB)

## Example Workflow

1. Organize shoes by factory into folders:
```
shoes/
├── factory_a/
│   ├── shoe1.jpg
│   ├── shoe2.jpg
│   └── ...
└── factory_b/
    ├── shoe1.jpg
    └── ...
```

2. Process each factory folder:
```bash
python main.py shoes/factory_a -o results/factory_a
python main.py shoes/factory_b -o results/factory_b
```

3. Review results:
   - Check `similar_groups/` to see grouped similar shoes
   - Each folder contains all shoes in that similarity group
   - Check `unique/` for distinctive designs

4. Adjust thresholds if needed:
   - Too many groups: Lower thresholds
   - Too few groups: Raise thresholds

## Troubleshooting

**Issue**: Out of memory errors
- Solution: Process smaller batches or use `--no-bg-removal`

**Issue**: Background removal too slow
- Solution: Use `--no-bg-removal` flag

**Issue**: Too many/few groups detected
- Solution: Adjust `--duplicate-threshold` and `--similar-threshold`

## Requirements

- Python 3.10+
- PyTorch 2.0+
- CUDA (optional, for GPU acceleration)

## License

MIT License
