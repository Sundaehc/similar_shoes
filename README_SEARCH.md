# 鞋子图片搜索系统 - 使用指南

## 功能概述

这是一个基于 CLIP + Faiss 的"以图搜图"系统，类似淘宝的"搜同款"功能。

**核心功能：**
- 上传一张鞋子图片，快速找到相似的商品
- 支持大规模图片库（10万+ 图片）
- 毫秒级搜索响应
- 提供 REST API 接口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果有 NVIDIA GPU，建议安装 GPU 版本以获得更快速度：
```bash
pip install faiss-gpu
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. 构建图片索引

首先需要从你的商品图片库构建索引：

```bash
python build_index.py <图片文件夹> -o index
```

示例：
```bash
python build_index.py ./shoes_dataset -o index
```

参数说明：
- `<图片文件夹>`: 包含所有商品图片的文件夹
- `-o, --output`: 索引保存目录（默认: index）
- `--gpu`: 使用 GPU 加速（如果可用）

### 3. 搜索相似图片

#### 方式 A: 命令行搜索

```bash
python search_engine.py <查询图片> -k 10 -s 0.5
```

示例：
```bash
python search_engine.py query.jpg -k 10 -s 0.5 -o results
```

参数说明：
- `<查询图片>`: 要搜索的图片路径
- `-i, --index`: 索引目录（默认: index）
- `-k, --top-k`: 返回结果数量（默认: 10）
- `-s, --min-similarity`: 最低相似度阈值 0-1（默认: 0.5）
- `-o, --output`: 保存结果到文件夹（可选）
- `--gpu`: 使用 GPU 加速

#### 方式 B: Web API

启动 API 服务器：
```bash
python api_server.py
```

服务器将在 `http://localhost:5000` 启动

**API 端点：**

1. **健康检查**
   ```
   GET /health
   ```

2. **搜索相似图片**
   ```
   POST /search
   Content-Type: multipart/form-data

   参数：
   - image: 图片文件
   - top_k: 返回数量（可选，默认10）
   - min_similarity: 最低相似度（可选，默认0.5）
   ```

3. **获取索引统计**
   ```
   GET /stats
   ```

**使用示例（curl）：**
```bash
curl -X POST http://localhost:5000/search \
  -F "image=@query.jpg" \
  -F "top_k=10" \
  -F "min_similarity=0.5"
```

**使用示例（Python）：**
```python
import requests

url = "http://localhost:5000/search"
files = {'image': open('query.jpg', 'rb')}
data = {'top_k': 10, 'min_similarity': 0.5}

response = requests.post(url, files=files, data=data)
results = response.json()

for item in results['results']:
    print(f"{item['filename']}: {item['similarity']:.3f}")
```

## 项目结构

```
shoes/
├── vector_index.py       # Faiss 向量索引管理
├── build_index.py        # 构建索引脚本
├── search_engine.py      # 搜索引擎
├── api_server.py         # Flask API 服务器
├── feature_extractor.py  # CLIP 特征提取
├── main.py              # 原批量处理脚本
└── requirements.txt     # 依赖包
```

## 性能与成本

### 小规模（1万-10万张图片）
- **硬件**: 普通笔记本或云服务器（8GB RAM）
- **成本**: 几乎为 0（使用 CPU）
- **搜索速度**: 10-50ms
- **索引构建**: 10-30分钟

### 中规模（10万-100万张图片）
- **硬件**: 16GB+ RAM，建议使用 GPU
- **成本**: 云服务器约 500-2000元/月
- **搜索速度**: 50-200ms
- **索引构建**: 1-3小时

### 大规模（100万+张图片）
- **硬件**: 32GB+ RAM，GPU 集群
- **成本**: 需要专业部署方案
- **搜索速度**: 需要分布式架构
- **建议**: 考虑使用 Milvus 或云服务（如 Pinecone）

## 技术栈

- **特征提取**: CLIP (OpenAI) - 768维向量
- **向量搜索**: Faiss - 高性能相似度搜索
- **Web 框架**: Flask + CORS
- **深度学习**: PyTorch + Transformers

## 常见问题

**Q: 如何提高搜索准确度？**
A:
1. 使用更大的 CLIP 模型（如 clip-vit-large-patch14）
2. 对图片进行预处理（背景移除、裁剪等）
3. 调整 min_similarity 阈值

**Q: 如何加快搜索速度？**
A:
1. 使用 GPU 版本的 Faiss
2. 使用更小的 CLIP 模型
3. 减少索引中的图片数量

**Q: 如何更新索引？**
A:
1. 重新构建完整索引（推荐）
2. 使用 `VectorIndex.add_images()` 增量添加

**Q: 支持哪些图片格式？**
A: PNG, JPG, JPEG, BMP, WEBP

## 下一步优化

1. **添加目标检测**: 使用 YOLOv8 精确定位鞋子区域
2. **分布式部署**: 使用 Milvus 替代 Faiss
3. **前端界面**: 添加 Web UI（Streamlit 或 React）
4. **缓存优化**: 添加 Redis 缓存热门查询
5. **批量搜索**: 支持一次上传多张图片

## 许可证

MIT License
