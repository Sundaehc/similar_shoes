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
