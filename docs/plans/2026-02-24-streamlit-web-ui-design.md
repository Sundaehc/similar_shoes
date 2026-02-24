# 鞋子图片搜索系统 - Streamlit Web UI 设计文档

**日期：** 2026-02-24
**状态：** 已批准
**类型：** 功能设计

## 概述

为现有的鞋子图片搜索系统（基于 CLIP + Faiss）构建一个完整的 Streamlit Web 应用，用于内网团队使用。

## 需求

### 功能需求
- **图片搜索**：上传图片，显示相似结果
- **索引管理**：查看索引状态、重建索引、添加新图片
- **批量搜索**：一次上传多张图片（最多 20 张）
- **结果对比**：并排对比多个搜索结果

### 非功能需求
- 部署方式：内网部署，团队内部使用
- 用户规模：10-50 人并发
- 响应时间：搜索 < 1 秒
- 易用性：简单直观的界面

## 架构设计

### 方案选择

**选定方案：纯 Streamlit 单体应用**

理由：
- 内网团队使用，不需要复杂架构
- 开发快速，部署简单
- 性能足够（支持几十人同时使用）
- 易于维护和迭代

### 技术栈

- **前端**：Streamlit（单页应用，多标签页导航）
- **后端逻辑**：直接调用现有的 `search_engine.py`、`vector_index.py`、`build_index.py`
- **数据存储**：SQLite（搜索历史）+ 文件系统（上传图片）
- **缓存**：Streamlit 内置 `@st.cache_resource` 缓存索引加载

### 文件结构

```
shoes/
├── streamlit_app.py          # 主应用入口
├── pages/
│   ├── 1_🔍_图片搜索.py      # 单图搜索页面
│   ├── 2_📦_批量搜索.py      # 批量搜索页面
│   ├── 3_⚙️_索引管理.py      # 索引管理页面
│   └── 4_📊_结果对比.py      # 结果对比页面
├── utils/
│   └── history_db.py         # 搜索历史数据库
├── config.yaml               # 配置文件
├── search_engine.py          # 现有代码
├── vector_index.py           # 现有代码
└── build_index.py            # 现有代码
```

## 页面功能设计

### 主页（streamlit_app.py）

- 显示系统状态：索引是否加载、图片总数、最近搜索次数
- 快速搜索入口
- 导航到各个功能页面

### 页面 1 - 图片搜索

**功能：**
- 上传图片（支持拖拽）
- 参数设置：
  - 返回结果数量（滑块 1-50，默认 10）
  - 最低相似度（滑块 0-1，默认 0.5）
- 搜索按钮
- 结果展示：网格布局，每个结果显示图片、相似度、文件名
- 点击结果可查看大图
- 保存搜索到历史记录

### 页面 2 - 批量搜索

**功能：**
- 上传多张图片（最多 20 张）
- 批量搜索，显示进度条
- 结果以标签页形式展示，每个查询图片一个标签
- 可以导出所有结果为 CSV

### 页面 3 - 索引管理

**功能：**
- 显示当前索引信息：图片数量、索引大小、创建时间
- 重建索引：选择图片文件夹，点击构建，显示进度
- 添加图片到现有索引
- 查看索引中的随机样本图片

### 页面 4 - 结果对比

**功能：**
- 从搜索历史中选择 2-4 个查询
- 并排显示它们的搜索结果
- 高亮显示共同出现的结果

## 数据存储设计

### 搜索引擎缓存

```python
@st.cache_resource
def load_search_engine():
    return ImageSearchEngine(Path("index"))
```

- 应用启动时加载一次，所有用户共享
- 避免重复加载索引，节省内存

### 搜索历史数据库（SQLite）

```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY,
    query_image_path TEXT,
    query_image_name TEXT,
    timestamp DATETIME,
    top_k INTEGER,
    min_similarity FLOAT,
    results_json TEXT  -- 存储搜索结果的 JSON
);
```

### 上传文件管理

- 临时文件夹：`uploads/temp/` - 存储用户上传的查询图片
- 历史文件夹：`uploads/history/{timestamp}_{filename}` - 保存搜索历史
- 定期清理超过 7 天的临时文件

### Session State 管理

- `st.session_state.current_results` - 当前搜索结果
- `st.session_state.comparison_queries` - 对比页面选中的查询
- `st.session_state.index_status` - 索引状态信息

## 错误处理和用户体验

### 错误处理

- **索引未加载**：显示友好提示，引导用户到索引管理页面
- **上传文件格式错误**：提示支持的格式（PNG, JPG, JPEG, BMP, WEBP）
- **搜索失败**：捕获异常，显示错误信息，不中断应用
- **索引构建失败**：显示详细错误日志，允许重试

### 用户体验优化

- 搜索时显示 spinner 和进度提示
- 批量搜索显示进度条（"正在处理 3/20 张图片..."）
- 图片懒加载，避免一次加载太多图片卡顿
- 结果网格使用 Streamlit columns，响应式布局
- 添加"返回顶部"按钮（结果很多时）
- 搜索参数使用合理的默认值（top_k=10, min_similarity=0.5）

### 性能优化

- 图片缩略图：显示时自动压缩到 300x300
- 限制批量搜索最多 20 张图片
- 搜索历史只保留最近 100 条记录
- 定期清理临时文件（启动时自动执行）

## 配置管理

### 配置文件（config.yaml）

```yaml
app:
  title: "鞋子图片搜索系统"
  port: 8501
  max_upload_size: 200  # MB

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

## 部署方案

### 部署步骤

1. 安装依赖：`pip install -r requirements.txt`
2. 构建索引：`python build_index.py <图片文件夹> -o index`
3. 启动应用：`streamlit run streamlit_app.py`
4. 内网访问：`http://<服务器IP>:8501`

### 生产环境建议

- 使用 systemd 或 supervisor 管理进程
- 配置自动重启
- 设置日志轮转
- 定期备份搜索历史数据库

### 多用户并发

- Streamlit 默认支持多用户
- 索引在内存中共享，节省资源
- 每个用户有独立的 session_state

## 未来扩展

如果需要更高性能或更多功能，可以考虑：
- 迁移到 Streamlit + Flask API 分离架构
- 添加用户认证系统
- 集成 Redis 缓存热门查询
- 添加搜索历史分析和统计功能
- 支持更多图片格式和预处理选项

## 风险和限制

- **并发限制**：单体应用不适合超大规模并发（100+ 同时在线）
- **内存占用**：索引加载到内存，大规模数据集需要足够的 RAM
- **单点故障**：没有高可用设计，服务器故障会导致服务中断

对于内网团队使用场景，这些限制是可接受的。
