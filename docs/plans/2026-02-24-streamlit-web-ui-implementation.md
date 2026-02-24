# Streamlit Web UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete Streamlit web application for the shoe image search system with search, batch search, index management, and result comparison features.

**Architecture:** Single Streamlit application with multi-page navigation. Direct integration with existing search_engine.py and vector_index.py. SQLite for search history, file system for uploads.

**Tech Stack:** Streamlit, SQLite, existing CLIP + Faiss backend

---

## Task 1: Setup Project Structure and Configuration

**Files:**
- Create: `utils/__init__.py`
- Create: `utils/history_db.py`
- Create: `config.yaml`
- Create: `data/.gitkeep`
- Create: `uploads/.gitkeep`

**Step 1: Create utils directory and __init__.py**

```bash
mkdir -p utils
touch utils/__init__.py
```

**Step 2: Create data and uploads directories**

```bash
mkdir -p data uploads/temp uploads/history
touch data/.gitkeep uploads/.gitkeep
```

**Step 3: Create config.yaml**

```yaml
app:
  title: "鞋子图片搜索系统"
  port: 8501
  max_upload_size: 200

index:
  path: "index"
  auto_load: true

search:
  default_top_k: 10
  default_min_similarity: 0.5
  max_batch_size: 20

storage:
  upload_dir: "uploads"
  history_db: "data/search_history.db"
  temp_file_retention_days: 7
```

**Step 4: Commit**

```bash
git add utils/ config.yaml data/.gitkeep uploads/.gitkeep
git commit -m "feat: add project structure and configuration"
```

---

## Task 2: Create Search History Database Module

**Files:**
- Create: `utils/history_db.py`

**Step 1: Write history_db.py**

```python
"""Search history database management."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class SearchHistoryDB:
    """Manages search history in SQLite database."""

    def __init__(self, db_path: str = "data/search_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_image_path TEXT NOT NULL,
                query_image_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                top_k INTEGER NOT NULL,
                min_similarity REAL NOT NULL,
                results_json TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_search(self, query_image_path: str, query_image_name: str,
                   top_k: int, min_similarity: float, results: List[Dict]) -> int:
        """Add a search record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_history
            (query_image_path, query_image_name, timestamp, top_k, min_similarity, results_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (query_image_path, query_image_name, datetime.now(),
              top_k, min_similarity, json.dumps(results)))
        search_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return search_id

    def get_recent_searches(self, limit: int = 100) -> List[Dict]:
        """Get recent search records."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'query_image_path': row['query_image_path'],
                'query_image_name': row['query_image_name'],
                'timestamp': row['timestamp'],
                'top_k': row['top_k'],
                'min_similarity': row['min_similarity'],
                'results': json.loads(row['results_json'])
            })
        return results

    def get_search_by_id(self, search_id: int) -> Optional[Dict]:
        """Get a specific search record."""
        searches = self.get_recent_searches(limit=1000)
        for search in searches:
            if search['id'] == search_id:
                return search
        return None

    def cleanup_old_records(self, keep_recent: int = 100):
        """Keep only recent N records."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM search_history
            WHERE id NOT IN (
                SELECT id FROM search_history
                ORDER BY timestamp DESC
                LIMIT ?
            )
        """, (keep_recent,))
        conn.commit()
        conn.close()
```

**Step 2: Commit**

```bash
git add utils/history_db.py
git commit -m "feat: add search history database module"
```

---

## Task 3: Create Main Streamlit App

**Files:**
- Create: `streamlit_app.py`

**Step 1: Write streamlit_app.py**

```python
"""Main Streamlit application for shoe image search system."""
import streamlit as st
import yaml
from pathlib import Path
from search_engine import ImageSearchEngine
from utils.history_db import SearchHistoryDB
import shutil
from datetime import datetime, timedelta


# Load configuration
@st.cache_resource
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# Load search engine
@st.cache_resource
def load_search_engine(index_path: str):
    """Load search engine with caching."""
    try:
        engine = ImageSearchEngine(Path(index_path))
        return engine
    except Exception as e:
        st.error(f"Failed to load search engine: {e}")
        return None


# Initialize database
@st.cache_resource
def get_history_db(db_path: str):
    """Get history database instance."""
    return SearchHistoryDB(db_path)


def cleanup_temp_files(upload_dir: Path, retention_days: int):
    """Clean up old temporary files."""
    temp_dir = upload_dir / "temp"
    if not temp_dir.exists():
        return

    cutoff_time = datetime.now() - timedelta(days=retention_days)
    for file in temp_dir.iterdir():
        if file.is_file() and datetime.fromtimestamp(file.stat().st_mtime) < cutoff_time:
            try:
                file.unlink()
            except Exception:
                pass


def main():
    # Page config
    st.set_page_config(
        page_title="鞋子图片搜索系统",
        page_icon="👟",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Load config
    config = load_config()

    # Cleanup temp files on startup
    upload_dir = Path(config['storage']['upload_dir'])
    cleanup_temp_files(upload_dir, config['storage']['temp_file_retention_days'])

    # Load search engine
    index_path = config['index']['path']
    search_engine = load_search_engine(index_path) if config['index']['auto_load'] else None

    # Store in session state
    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = search_engine
    if 'config' not in st.session_state:
        st.session_state.config = config
    if 'history_db' not in st.session_state:
        st.session_state.history_db = get_history_db(config['storage']['history_db'])

    # Main page
    st.title("👟 鞋子图片搜索系统")
    st.markdown("---")

    # System status
    col1, col2, col3 = st.columns(3)

    with col1:
        if search_engine:
            stats = search_engine.index.get_stats()
            st.metric("索引状态", "✅ 已加载")
            st.metric("图片总数", f"{stats['total_images']:,}")
        else:
            st.metric("索引状态", "❌ 未加载")
            st.warning("请先到索引管理页面构建或加载索引")

    with col2:
        history_db = st.session_state.history_db
        recent_searches = history_db.get_recent_searches(limit=10)
        st.metric("最近搜索", len(recent_searches))

    with col3:
        st.metric("系统版本", "1.0.0")

    st.markdown("---")

    # Quick search
    st.subheader("🔍 快速搜索")

    if search_engine:
        uploaded_file = st.file_uploader(
            "上传图片进行搜索",
            type=['png', 'jpg', 'jpeg', 'bmp', 'webp'],
            help="支持拖拽上传"
        )

        if uploaded_file:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(uploaded_file, caption="查询图片", use_container_width=True)

            with col2:
                if st.button("🔍 搜索", type="primary"):
                    st.info("请前往 '图片搜索' 页面进行详细搜索")
    else:
        st.info("请先加载索引才能使用搜索功能")

    # Navigation guide
    st.markdown("---")
    st.subheader("📖 功能导航")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.page_link("pages/1_🔍_图片搜索.py", label="🔍 图片搜索", help="上传图片搜索相似商品")

    with col2:
        st.page_link("pages/2_📦_批量搜索.py", label="📦 批量搜索", help="一次搜索多张图片")

    with col3:
        st.page_link("pages/3_⚙️_索引管理.py", label="⚙️ 索引管理", help="管理图片索引")

    with col4:
        st.page_link("pages/4_📊_结果对比.py", label="📊 结果对比", help="对比多个搜索结果")


if __name__ == "__main__":
    main()
```

**Step 2: Test the main app**

```bash
streamlit run streamlit_app.py
```

Expected: App launches, shows system status (index not loaded warning is OK)

**Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add main streamlit app with system status"
```

---

## Task 4: Create Image Search Page

**Files:**
- Create: `pages/1_🔍_图片搜索.py`

**Step 1: Write image search page**

