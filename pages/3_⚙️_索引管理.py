import streamlit as st
from PIL import Image
import os
import random
import subprocess
import sys
from pathlib import Path
from tkinter import Tk, filedialog

st.set_page_config(page_title="索引管理", page_icon="⚙️", layout="wide")

st.title("⚙️ 索引管理")

# Display current index status
st.subheader("📊 当前索引状态")

search_engine = st.session_state.get('search_engine')
config = st.session_state.get('config', {})

if search_engine:
    try:
        stats = search_engine.index.get_stats()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("索引状态", "✅ 已加载")

        with col2:
            st.metric("图片数量", f"{stats['total_images']:,}")

        with col3:
            st.metric("特征维度", stats['dimension'])

        # Show index file info
        index_path = Path(config.get('index', {}).get('path', 'index'))
        if index_path.exists():
            index_size = sum(f.stat().st_size for f in index_path.rglob('*') if f.is_file())
            st.info(f"📁 索引路径: {index_path} | 大小: {index_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        st.error(f"获取索引信息失败: {e}")
else:
    st.warning("⚠️ 索引未加载")
    st.info("请在下方构建新索引，或修改 config.yaml 中的索引路径")

st.divider()

# Build new index section
st.subheader("🔨 构建新索引")

st.info("📌 选择包含鞋子图片的文件夹，系统将扫描所有图片并构建向量索引")

# Initialize session state for folder path
if 'selected_folder' not in st.session_state:
    st.session_state.selected_folder = ""

col1, col2 = st.columns([4, 1])

with col1:
    image_dir = st.text_input(
        "图片文件夹路径",
        value=st.session_state.selected_folder,
        placeholder="点击右侧按钮选择文件夹，或手动输入路径",
        help="包含鞋子图片的文件夹"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    if st.button("📁 浏览", help="打开文件夹选择对话框"):
        try:
            # Create a Tk root window (hidden)
            root = Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)

            # Open folder selection dialog
            folder_path = filedialog.askdirectory(
                title="选择图片文件夹",
                initialdir=os.path.expanduser("~")
            )

            root.destroy()

            if folder_path:
                st.session_state.selected_folder = folder_path
                st.rerun()
        except Exception as e:
            st.error(f"打开文件选择器失败: {e}")

output_dir = st.text_input(
    "输出目录",
    value="index",
    help="索引保存目录"
)

if st.button("🔨 开始构建索引", type="primary"):
    if not image_dir:
        st.error("请输入图片文件夹路径")
    elif not os.path.exists(image_dir):
        st.error(f"文件夹不存在: {image_dir}")
    else:
        with st.spinner("正在构建索引，这可能需要几分钟..."):
            try:
                # Run build_index.py script
                result = subprocess.run(
                    [sys.executable, "build_index.py", image_dir, "-o", output_dir],
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )

                if result.returncode == 0:
                    st.success("✅ 索引构建成功！")
                    st.code(result.stdout, language="text")

                    st.info("💡 请刷新页面以加载新索引")
                    if st.button("🔄 刷新页面"):
                        st.rerun()
                else:
                    st.error("❌ 索引构建失败")
                    st.code(result.stderr, language="text")

            except Exception as e:
                st.error(f"构建失败: {e}")

st.divider()

# View sample images
st.subheader("🖼️ 索引图片样本")

if search_engine:
    try:
        stats = search_engine.index.get_stats()
        image_paths = search_engine.index.image_paths

        if image_paths and len(image_paths) > 0:
            num_samples = st.slider("显示样本数量", min_value=5, max_value=50, value=20)

            # Randomly sample images
            sample_paths = random.sample(
                image_paths,
                min(num_samples, len(image_paths))
            )

            cols_per_row = 5
            for i in range(0, len(sample_paths), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(sample_paths):
                        with col:
                            try:
                                img = Image.open(sample_paths[idx])
                                # Resize to fixed size while maintaining aspect ratio
                                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                                st.image(img, use_container_width=True)
                                st.caption(os.path.basename(sample_paths[idx]))
                            except Exception as e:
                                st.error(f"无法加载: {e}")
        else:
            st.warning("索引中没有图片")

    except Exception as e:
        st.error(f"获取样本图片失败: {e}")
else:
    st.info("请先构建或加载索引以查看样本图片")
