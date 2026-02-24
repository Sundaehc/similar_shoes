"""
Simple Flask API for image search.
Provides REST endpoints for building index and searching images.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import tempfile
import os

from search_engine import ImageSearchEngine
from build_index import build_index as build_index_func

app = Flask(__name__)
CORS(app)  # Enable CORS for web frontend

# Configuration
INDEX_DIR = Path("index")
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}

# Global search engine instance
search_engine = None


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_search_engine():
    """Initialize search engine if index exists."""
    global search_engine
    if INDEX_DIR.exists() and (INDEX_DIR / "faiss.index").exists():
        try:
            search_engine = ImageSearchEngine(INDEX_DIR)
            print(f"Search engine initialized with {search_engine.index.get_stats()['total_images']} images")
        except Exception as e:
            print(f"Failed to initialize search engine: {e}")
            search_engine = None
    else:
        print("No index found. Please build an index first.")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'index_loaded': search_engine is not None,
        'total_images': search_engine.index.get_stats()['total_images'] if search_engine else 0
    })


@app.route('/search', methods=['POST'])
def search():
    """Search for similar images by uploading a query image."""
    if search_engine is None:
        return jsonify({'error': 'Search engine not initialized. Please build an index first.'}), 503

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, bmp, webp'}), 400

    # Get parameters
    top_k = int(request.form.get('top_k', 10))
    min_similarity = float(request.form.get('min_similarity', 0.5))

    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    temp_path = UPLOAD_FOLDER / filename
    file.save(temp_path)

    try:
        # Search
        results = search_engine.search(temp_path, top_k=top_k, min_similarity=min_similarity)

        # Format results
        formatted_results = []
        for img_path, score, metadata in results:
            formatted_results.append({
                'image_path': img_path,
                'similarity': float(score),
                'filename': Path(img_path).name,
                'metadata': metadata
            })

        return jsonify({
            'query_image': filename,
            'results': formatted_results,
            'total_results': len(formatted_results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@app.route('/stats', methods=['GET'])
def stats():
    """Get index statistics."""
    if search_engine is None:
        return jsonify({'error': 'Search engine not initialized'}), 503

    return jsonify(search_engine.index.get_stats())


@app.route('/image/<path:image_path>', methods=['GET'])
def get_image(image_path):
    """Serve an image file."""
    try:
        return send_file(image_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


if __name__ == '__main__':
    # Initialize search engine on startup
    init_search_engine()

    # Run server
    port = int(os.environ.get('PORT', 5000))
    print(f"\nStarting API server on http://localhost:{port}")
    print(f"API endpoints:")
    print(f"  GET  /health - Health check")
    print(f"  POST /search - Search similar images (upload image)")
    print(f"  GET  /stats  - Get index statistics")
    print(f"  GET  /image/<path> - Get image file\n")

    app.run(host='0.0.0.0', port=port, debug=True)
