import streamlit as st
from PIL import Image
import io
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="图片搜索", page_icon="🔍", layout="wide")

st.title("🔍 同款检测")

# Check if search engine is loaded
if 'search_engine' not in st.session_state or st.session_state.search_engine is None:
    st.error("❌ 搜索引擎未加载，请先在索引管理页面构建索引")
    st.stop()

# Initialize search history in session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.info("📌 上传图片，系统将自动检测是否有同款")

# Upload image
uploaded_file = st.file_uploader("上传查询图片", type=['jpg', 'jpeg', 'png', 'bmp', 'webp'])

if uploaded_file is not None:
    # Display uploaded image
    query_image = Image.open(uploaded_file)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("查询图片")
        st.image(query_image, use_container_width=True)

    with col2:
        st.subheader("检测结果")

        with st.spinner("正在检测同款..."):
            try:
                # Save uploaded file temporarily
                config = st.session_state.config
                upload_dir = Path(config['storage']['upload_dir'])
                temp_dir = upload_dir / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = temp_dir / f"{timestamp}_{uploaded_file.name}"

                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Search with optimized parameters for duplicate detection
                # High similarity threshold (0.85) to find near-duplicates
                # Top 20 to ensure we find all potential matches
                results = st.session_state.search_engine.search(
                    temp_path,
                    top_k=20,
                    min_similarity=0.85
                )

                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()

                # Analyze and display results
                if len(results) == 0:
                    st.warning("❌ 未找到同款")
                    st.info("数据库中没有与此图片相似度超过 85% 的商品")
                else:
                    # Separate exact matches and similar matches
                    exact_matches = [(img_path, score, metadata) for img_path, score, metadata in results if score >= 0.90]
                    similar_matches = [(img_path, score, metadata) for img_path, score, metadata in results if 0.85 <= score < 0.90]

                    # Display summary
                    if exact_matches:
                        st.success(f"✅ 找到 {len(exact_matches)} 个同款！")
                        if similar_matches:
                            st.info(f"另外还有 {len(similar_matches)} 个相似款")
                    else:
                        st.success(f"✅ 找到 {len(similar_matches)} 个相似款")
                        st.info("相似度在 85%-90% 之间，可能是同款的不同角度或颜色")

                    st.divider()

                    # Display exact matches
                    if exact_matches:
                        st.subheader(f"🎯 同款商品 ({len(exact_matches)} 个)")
                        st.caption("相似度 ≥ 90%")

                        cols_per_row = 5
                        for i in range(0, len(exact_matches), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                idx = i + j
                                if idx < len(exact_matches):
                                    img_path, score, metadata = exact_matches[idx]
                                    with col:
                                        try:
                                            img = Image.open(img_path)
                                            img.thumbnail((300, 300))
                                            st.image(img, use_container_width=True)
                                            st.caption(f"✅ {score:.1%}")
                                            st.caption(f"{Path(img_path).name}")
                                        except Exception as e:
                                            st.error(f"无法加载")

                    # Display similar matches
                    if similar_matches:
                        if exact_matches:
                            st.divider()
                        st.subheader(f"🔍 相似款 ({len(similar_matches)} 个)")
                        st.caption("相似度 85%-90%")

                        cols_per_row = 5
                        for i in range(0, len(similar_matches), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                idx = i + j
                                if idx < len(similar_matches):
                                    img_path, score, metadata = similar_matches[idx]
                                    with col:
                                        try:
                                            img = Image.open(img_path)
                                            img.thumbnail((300, 300))
                                            st.image(img, use_container_width=True)
                                            st.caption(f"📊 {score:.1%}")
                                            st.caption(f"{Path(img_path).name}")
                                        except Exception as e:
                                            st.error(f"无法加载")

                # Save to history
                search_record = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'query_image': uploaded_file.name,
                    'top_k': 20,
                    'min_similarity': 0.85,
                    'results': results
                }
                st.session_state.search_history.append(search_record)

            except Exception as e:
                st.error(f"检测失败: {str(e)}")
