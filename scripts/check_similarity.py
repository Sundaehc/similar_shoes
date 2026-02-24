"""
查看图片相似度的测试脚本
用于帮助确定合适的阈值
"""

import sys
from pathlib import Path
import numpy as np
from feature_extractor import ShoeFeatureExtractor
from sklearn.metrics.pairwise import cosine_similarity

def test_similarity(image_folder):
    """测试文件夹中图片的相似度"""

    # 获取所有图片
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    images = []
    for ext in image_extensions:
        images.extend(Path(image_folder).glob(f"*{ext}"))
        images.extend(Path(image_folder).glob(f"*{ext.upper()}"))

    if len(images) < 2:
        print("需要至少2张图片")
        return

    print(f"找到 {len(images)} 张图片")
    print("正在提取特征...")

    # 提取特征
    extractor = ShoeFeatureExtractor()
    features = []
    valid_images = []

    for img_path in images:
        try:
            feat = extractor.extract_features(img_path)
            features.append(feat)
            valid_images.append(img_path)
        except Exception as e:
            print(f"跳过 {img_path.name}: {e}")

    features = np.array(features)

    # 计算相似度矩阵
    sim_matrix = cosine_similarity(features)

    print(f"\n{'='*60}")
    print("相似度分析结果")
    print(f"{'='*60}\n")

    # 显示统计信息
    # 获取上三角矩阵（排除对角线）
    upper_triangle = sim_matrix[np.triu_indices_from(sim_matrix, k=1)]

    print(f"相似度统计：")
    print(f"  最高相似度: {upper_triangle.max():.3f}")
    print(f"  最低相似度: {upper_triangle.min():.3f}")
    print(f"  平均相似度: {upper_triangle.mean():.3f}")
    print(f"  中位数相似度: {np.median(upper_triangle):.3f}")

    # 显示相似度分布
    print(f"\n相似度分布：")
    ranges = [
        (0.95, 1.0, "极度相似"),
        (0.90, 0.95, "非常相似"),
        (0.85, 0.90, "很相似"),
        (0.80, 0.85, "相似"),
        (0.75, 0.80, "较相似"),
        (0.70, 0.75, "有些相似"),
        (0.0, 0.70, "不太相似")
    ]

    for low, high, label in ranges:
        count = np.sum((upper_triangle >= low) & (upper_triangle < high))
        percentage = count / len(upper_triangle) * 100
        print(f"  {label} ({low:.2f}-{high:.2f}): {count} 对 ({percentage:.1f}%)")

    # 建议阈值
    print(f"\n{'='*60}")
    print("阈值建议：")
    print(f"{'='*60}\n")

    percentile_90 = np.percentile(upper_triangle, 90)
    percentile_70 = np.percentile(upper_triangle, 70)

    print(f"如果这些图片应该被归为一组：")
    print(f"  建议 duplicate-threshold: {percentile_70:.2f}")
    print(f"  建议 similar-threshold: {max(0.65, percentile_70 - 0.10):.2f}")

    print(f"\n如果想要更严格的分组：")
    print(f"  建议 duplicate-threshold: {percentile_90:.2f}")
    print(f"  建议 similar-threshold: {percentile_70:.2f}")

    # 显示最相似和最不相似的图片对
    print(f"\n{'='*60}")
    print("示例图片对：")
    print(f"{'='*60}\n")

    # 找出最相似的5对
    print("最相似的5对图片：")
    flat_indices = np.argsort(upper_triangle)[::-1][:5]
    for idx in flat_indices:
        i, j = np.triu_indices_from(sim_matrix, k=1)
        img_i, img_j = i[idx], j[idx]
        score = sim_matrix[img_i, img_j]
        print(f"  {valid_images[img_i].name} <-> {valid_images[img_j].name}: {score:.3f}")

    # 找出最不相似的5对
    print("\n最不相似的5对图片：")
    flat_indices = np.argsort(upper_triangle)[:5]
    for idx in flat_indices:
        i, j = np.triu_indices_from(sim_matrix, k=1)
        img_i, img_j = i[idx], j[idx]
        score = sim_matrix[img_i, img_j]
        print(f"  {valid_images[img_i].name} <-> {valid_images[img_j].name}: {score:.3f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_similarity.py <图片文件夹>")
        sys.exit(1)

    test_similarity(sys.argv[1])
