import streamlit as st
from PIL import Image
import io
from datetime import datetime

st.set_page_config(page_title="批量搜索", page_icon="📦", layout="wide")

st.title("📦 批量搜索")

# Check if search engine is loaded
if 'search_engine' not in st.session_state or st.session_state.search_engine is None:
    st.error("❌ 搜索引擎未加载，请先在主页加载索引文件")
    st.stop()

# Initialize batch search results in session state
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []

st.info("📌 批量上传图片进行搜索，最多支持20张图片")

# Upload multiple images
uploaded_files = st.file_uploader(
    "上传多张查询图片",
    type=['jpg', 'jpeg', 'png', 'bmp'],
    accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) > 20:
        st.error("❌ 最多只能上传20张图片")
        st.stop()

    st.success(f"✅ 已上传 {len(uploaded_files)} 张图片")

    # Search parameters
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("每张图片返回结果数量 (top_k)", min_value=1, max_value=20, value=5)
    with col2:
        min_similarity = st.slider("最小相似度阈值", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

    if st.button("🚀 开始批量搜索", type="primary"):
        st.session_state.batch_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"正在处理: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")

            try:
                query_image = Image.open(uploaded_file)
                results = st.session_state.search_engine.search(
                    query_image,
                    top_k=top_k,
                    min_similarity=min_similarity
                )

                st.session_state.batch_results.append({
                    'filename': uploaded_file.name,
                    'query_image': query_image,
                    'results': results
                })

            except Exception as e:
                st.session_state.batch_results.append({
                    'filename': uploaded_file.name,
                    'query_image': None,
                    'results': [],
                    'error': str(e)
                })

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.text("✅ 批量搜索完成！")
        st.success(f"已完成 {len(uploaded_files)} 张图片的搜索")

# Display results in tabs
if st.session_state.batch_results:
    st.subheader("搜索结果")

    tabs = st.tabs([f"{r['filename']}" for r in st.session_state.batch_results])

    for tab, batch_result in zip(tabs, st.session_state.batch_results):
        with tab:
            col1, col2 = st.columns([1, 3])

            with col1:
                st.subheader("查询图片")
                if batch_result['query_image'] is not None:
                    st.image(batch_result['query_image'], use_container_width=True)
                else:
                    st.error("图片加载失败")

            with col2:
                if 'error' in batch_result:
                    st.error(f"搜索失败: {batch_result['error']}")
                elif len(batch_result['results']) == 0:
                    st.warning("未找到符合条件的相似图片")
                else:
                    st.success(f"找到 {len(batch_result['results'])} 个相似图片")

                    # Display results in grid
                    cols_per_row = 4
                    for i in range(0, len(batch_result['results']), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            idx = i + j
                            if idx < len(batch_result['results']):
                                img_path, score, metadata = batch_result['results'][idx]
                                with col:
                                    try:
                                        img = Image.open(img_path)
                                        img.thumbnail((200, 200))
                                        st.image(img, use_container_width=True)
                                        st.caption(f"相似度: {score:.4f}")
                                    except Exception as e:
                                        st.error(f"无法加载: {str(e)}")
