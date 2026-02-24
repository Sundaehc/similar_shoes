import streamlit as st
from PIL import Image

st.set_page_config(page_title="结果对比", page_icon="📊", layout="wide")

st.title("📊 结果对比")

# Check if search history exists
if 'search_history' not in st.session_state or len(st.session_state.search_history) == 0:
    st.warning("⚠️ 暂无搜索历史记录，请先在图片搜索页面进行搜索")
    st.stop()

st.info("📌 从历史记录中选择多个搜索结果进行对比分析")

# Display search history
st.subheader("搜索历史")

# Create selection checkboxes
selected_indices = []
for idx, record in enumerate(st.session_state.search_history):
    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])

    with col1:
        if st.checkbox(f"选择", key=f"select_{idx}"):
            selected_indices.append(idx)

    with col2:
        st.text(f"时间: {record['timestamp']}")

    with col3:
        st.text(f"查询图片: {record['query_image']}")

    with col4:
        st.text(f"结果数: {len(record['results'])}")

st.divider()

# Compare selected results
if len(selected_indices) == 0:
    st.info("请至少选择一个搜索记录进行对比")
elif len(selected_indices) == 1:
    st.warning("请选择至少2个搜索记录进行对比")
else:
    st.subheader(f"对比分析 (已选择 {len(selected_indices)} 个搜索)")

    # Display side-by-side comparison
    cols = st.columns(len(selected_indices))

    for col_idx, search_idx in enumerate(selected_indices):
        record = st.session_state.search_history[search_idx]

        with cols[col_idx]:
            st.markdown(f"**搜索 {col_idx + 1}**")
            st.caption(f"时间: {record['timestamp']}")
            st.caption(f"查询: {record['query_image']}")
            st.caption(f"Top-K: {record['top_k']}")
            st.caption(f"最小相似度: {record['min_similarity']}")

            st.markdown("---")

            # Display top results
            for i, result in enumerate(record['results'][:5]):  # Show top 5
                try:
                    # Handle both tuple and dict formats
                    if isinstance(result, tuple):
                        img_path, score, metadata = result
                    else:
                        img_path = result['path']
                        score = result['similarity']

                    img = Image.open(img_path)
                    img.thumbnail((200, 200))
                    st.image(img, use_container_width=True)
                    st.caption(f"#{i+1} - 相似度: {score:.4f}")
                except Exception as e:
                    st.error(f"无法加载图片")

    st.divider()

    # Find common results
    st.subheader("🔍 共同结果分析")

    # Extract all result paths from selected searches
    all_results = []
    for search_idx in selected_indices:
        record = st.session_state.search_history[search_idx]
        # Handle both tuple and dict formats
        result_paths = []
        for r in record['results']:
            if isinstance(r, tuple):
                result_paths.append(r[0])  # img_path is first element
            else:
                result_paths.append(r['path'])
        all_results.append(set(result_paths))

    # Find intersection (common results)
    if len(all_results) > 0:
        common_paths = set.intersection(*all_results)

        if len(common_paths) > 0:
            st.success(f"✅ 找到 {len(common_paths)} 个共同结果")

            # Display common results
            cols_per_row = 5
            common_list = list(common_paths)
            for i in range(0, len(common_list), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(common_list):
                        with col:
                            try:
                                img = Image.open(common_list[idx])
                                st.image(img, use_container_width=True)
                                st.caption(common_list[idx])
                            except Exception as e:
                                st.error("无法加载图片")
        else:
            st.warning("⚠️ 所选搜索结果之间没有共同的图片")

        # Display unique results for each search
        st.divider()
        st.subheader("🎯 独特结果")

        for col_idx, search_idx in enumerate(selected_indices):
            record = st.session_state.search_history[search_idx]
            result_paths = set([r['path'] for r in record['results']])

            # Find unique results (not in common)
            unique_paths = result_paths - common_paths

            with st.expander(f"搜索 {col_idx + 1} 的独特结果 ({len(unique_paths)} 个)"):
                if len(unique_paths) > 0:
                    cols_per_row = 5
                    unique_list = list(unique_paths)
                    for i in range(0, len(unique_list), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            idx = i + j
                            if idx < len(unique_list):
                                with col:
                                    try:
                                        img = Image.open(unique_list[idx])
                                        st.image(img, use_container_width=True)
                                        st.caption(unique_list[idx])
                                    except Exception as e:
                                        st.error("无法加载")
                else:
                    st.info("没有独特结果")
