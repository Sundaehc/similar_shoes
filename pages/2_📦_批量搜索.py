import streamlit as st
from PIL import Image
import io
from datetime import datetime
import numpy as np

st.set_page_config(page_title="批量搜索", page_icon="📦", layout="wide")

st.title("📦 批量搜索")

# Custom CSS to change button text
st.markdown("""
<style>
[data-testid="stFileUploader"] section button {
    font-size: 0;
}
[data-testid="stFileUploader"] section button::after {
    content: "浏览文件";
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# Check if search engine is loaded
if 'search_engine' not in st.session_state or st.session_state.search_engine is None:
    st.error("❌ 搜索引擎未加载，请先在主页加载索引文件")
    st.stop()

# Initialize batch search results in session state
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []

st.info("📌 批量上传图片，系统将根据文件名前缀自动分组（例如：A_1.jpg, A_2.jpg 会归为一组），然后查找向量库中的同款，最多支持20张图片")

# Upload multiple images
uploaded_files = st.file_uploader(
    "上传多张查询图片",
    type=['jpg', 'jpeg', 'png', 'bmp', 'webp'],
    accept_multiple_files=True,
    label_visibility="visible"
)

if uploaded_files:
    if len(uploaded_files) > 20:
        st.error("❌ 最多只能上传20张图片")
        st.stop()

    st.success(f"✅ 已上传 {len(uploaded_files)} 张图片")

    # Add grouping method selection
    grouping_method = st.radio(
        "分组方式",
        options=["按文件名前缀分组", "按图片相似度自动分组"],
        help="文件名前缀：根据文件名中的前缀自动分组（如 A_1.jpg, A_2.jpg 归为 A 组）\n图片相似度：使用AI自动识别同款图片"
    )

    if grouping_method == "按文件名前缀分组":
        st.info("💡 提示：文件名格式示例：A_1.jpg, A_2.jpg, B_1.jpg, B_2.jpg")
        st.caption("系统会提取下划线或连字符前的部分作为组名")

    if st.button("🚀 开始批量检测", type="primary"):
        st.session_state.batch_results = []

        # Step 1: Extract features for all uploaded images
        st.info("📊 步骤 1/3: 提取上传图片的特征...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        uploaded_images = []
        uploaded_features = []

        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"正在提取特征: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")
            try:
                query_image = Image.open(uploaded_file)
                # Extract features
                features = st.session_state.search_engine.extractor.extract_features(query_image)
                uploaded_images.append({
                    'filename': uploaded_file.name,
                    'image': query_image,
                    'features': features
                })
                uploaded_features.append(features)
            except Exception as e:
                st.error(f"处理 {uploaded_file.name} 失败: {e}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        if not uploaded_images:
            st.error("没有成功处理的图片")
            st.stop()

        # Step 2: Group images
        st.info("📊 步骤 2/3: 对上传的图片进行分组...")

        if grouping_method == "按文件名前缀分组":
            # Group by filename prefix
            import re
            groups_dict = {}

            for idx, img_data in enumerate(uploaded_images):
                filename = img_data['filename']
                # Extract prefix before underscore, hyphen, or dot
                match = re.match(r'^([^_\-\.]+)', filename)
                if match:
                    prefix = match.group(1)
                else:
                    prefix = filename

                if prefix not in groups_dict:
                    groups_dict[prefix] = []
                groups_dict[prefix].append(idx)

            # Convert to list format
            groups = list(groups_dict.values())
            group_names = list(groups_dict.keys())

            st.success(f"✅ 根据文件名将 {len(uploaded_images)} 张图片分为 {len(groups)} 组")
            for name, group in zip(group_names, groups):
                st.caption(f"  - 组 '{name}': {len(group)} 张图片")

        else:
            # Group by image similarity (original method)
            uploaded_features_array = np.array(uploaded_features)

            # Normalize features for cosine similarity
            import faiss
            faiss.normalize_L2(uploaded_features_array)

            # Compute similarity matrix between uploaded images
            similarity_matrix = np.dot(uploaded_features_array, uploaded_features_array.T)

            # Group images by similarity (threshold: 0.88)
            groups = []
            assigned = set()

            for i in range(len(uploaded_images)):
                if i in assigned:
                    continue

                group = [i]
                assigned.add(i)

                for j in range(i + 1, len(uploaded_images)):
                    if j not in assigned and similarity_matrix[i][j] >= 0.88:
                        group.append(j)
                        assigned.add(j)

                groups.append(group)

            group_names = [f"自动分组{i+1}" for i in range(len(groups))]
            st.success(f"✅ 根据相似度将 {len(uploaded_images)} 张图片分为 {len(groups)} 组")

        # Step 3: Search vector database for each group
        st.info("📊 步骤 3/3: 在向量库中查找同款...")
        progress_bar = st.progress(0)

        group_results = []
        for group_idx, (group, group_name) in enumerate(zip(groups, group_names)):
            status_text.text(f"正在查询第 {group_idx + 1}/{len(groups)} 组 ({group_name})")

            # Use the first image in the group as representative
            representative_idx = group[0]
            representative_image = uploaded_images[representative_idx]

            try:
                # Search in vector database
                results = st.session_state.search_engine.search(
                    representative_image['image'],
                    top_k=20,
                    min_similarity=0.85
                )

                # Categorize results
                exact_matches = [(img_path, score, metadata) for img_path, score, metadata in results if score >= 0.90]
                similar_matches = [(img_path, score, metadata) for img_path, score, metadata in results if 0.85 <= score < 0.90]

                group_results.append({
                    'group_id': group_idx + 1,
                    'group_name': group_name,
                    'images': [uploaded_images[i] for i in group],
                    'representative': representative_image,
                    'results': results,
                    'exact_matches': exact_matches,
                    'similar_matches': similar_matches
                })

            except Exception as e:
                group_results.append({
                    'group_id': group_idx + 1,
                    'group_name': group_name,
                    'images': [uploaded_images[i] for i in group],
                    'representative': representative_image,
                    'error': str(e)
                })

            progress_bar.progress((group_idx + 1) / len(groups))

        st.session_state.batch_results = group_results
        status_text.text("✅ 批量搜索完成！")
        st.success(f"已完成 {len(groups)} 组图片的搜索")

# Display results by groups
if st.session_state.batch_results:
    st.subheader("搜索结果")

    for group_result in st.session_state.batch_results:
        group_name = group_result.get('group_name', f"第{group_result['group_id']}组")
        with st.expander(f"📦 {group_name} - {len(group_result['images'])} 张同款图片", expanded=True):
            # Show all images in this group
            st.markdown("**🖼️ 上传的同款图片：**")
            cols = st.columns(min(len(group_result['images']), 5))
            for idx, img_data in enumerate(group_result['images']):
                with cols[idx % 5]:
                    # Resize image for display
                    img = img_data['image'].copy()
                    img.thumbnail((150, 150))
                    st.image(img, caption=img_data['filename'], use_container_width=True)

            st.divider()

            # Show search results from vector database
            if 'error' in group_result:
                st.error(f"检测失败: {group_result['error']}")
            elif len(group_result.get('results', [])) == 0:
                st.warning("❌ 向量库中未找到同款")
                st.info("数据库中没有与此组图片相似度超过 85% 的商品")
            else:
                exact_matches = group_result.get('exact_matches', [])
                similar_matches = group_result.get('similar_matches', [])

                # Display summary
                st.markdown("**🔍 向量库查询结果：**")
                if exact_matches:
                    st.success(f"✅ 找到 {len(exact_matches)} 个同款！")
                    if similar_matches:
                        st.info(f"另外还有 {len(similar_matches)} 个相似款")
                else:
                    st.success(f"✅ 找到 {len(similar_matches)} 个相似款")
                    st.info("相似度在 85%-90% 之间")

                st.divider()

                # Display exact matches
                if exact_matches:
                    st.markdown("**🎯 同款商品**")
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
                                        img.thumbnail((200, 200))
                                        st.image(img, use_container_width=True)
                                        st.caption(f"✅ {score:.1%}")
                                    except Exception as e:
                                        st.error(f"无法加载")

                # Display similar matches
                if similar_matches:
                    if exact_matches:
                        st.divider()
                    st.markdown("**🔍 相似款**")
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
                                        img.thumbnail((200, 200))
                                        st.image(img, use_container_width=True)
                                        st.caption(f"📊 {score:.1%}")
                                    except Exception as e:
                                        st.error(f"无法加载")
