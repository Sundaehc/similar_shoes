import streamlit as st
from PIL import Image
import io
from datetime import datetime

st.set_page_config(page_title="图片搜索", page_icon="🔍", layout="wide")

st.title("🔍 图片搜索")

# Check if search engine is loaded
if 'search_engine' not in st.session_state or st.session_state.search_engine is None:
    st.error("❌ 搜索引擎未加载，请先在主页加载索引文件")
    st.stop()

# Initialize search history in session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Upload image
uploaded_file = st.file_uploader("上传查询图片", type=['jpg', 'jpeg', 'png', 'bmp'])

if uploaded_file is not None:
    # Display uploaded image
    query_image = Image.open(uploaded_file)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("查询图片")
        st.image(query_image, use_container_width=True)

    with col2:
        st.subheader("搜索参数")
        top_k = st.slider("返回结果数量 (top_k)", min_value=1, max_value=50, value=10)
        min_similarity = st.slider("最小相似度阈值", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

        if st.button("🔍 开始搜索", type="primary"):
            with st.spinner("正在搜索..."):
                try:
                    # Perform search
                    results = st.session_state.search_engine.search(
                        query_image,
                        top_k=top_k,
                        min_similarity=min_similarity
                    )

                    if len(results) == 0:
                        st.warning("未找到符合条件的相似图片")
                    else:
                        # Save to history
                        search_record = {
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'query_image': uploaded_file.name,
                            'top_k': top_k,
                            'min_similarity': min_similarity,
                            'results': results
                        }
                        st.session_state.search_history.append(search_record)

                        st.success(f"✅ 找到 {len(results)} 个相似图片")

                        # Display results in grid
                        st.subheader("搜索结果")
                        cols_per_row = 5
                        for i in range(0, len(results), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                idx = i + j
                                if idx < len(results):
                                    img_path, score, metadata = results[idx]
                                    with col:
                                        try:
                                            img = Image.open(img_path)
                                            img.thumbnail((300, 300))
                                            st.image(img, use_container_width=True)
                                            st.caption(f"相似度: {score:.4f}")
                                            st.caption(f"{img_path.split('/')[-1] if '/' in img_path else img_path.split('\\\\')[-1]}")
                                        except Exception as e:
                                            st.error(f"无法加载图片: {str(e)}")

                except Exception as e:
                    st.error(f"搜索失败: {str(e)}")
