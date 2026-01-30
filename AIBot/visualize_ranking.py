"""
生成 paper_ranker.py 评分报告的可视化图表
"""

import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
import numpy as np


# 配置中文字体支持
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 设置整体样式
plt.style.use("seaborn-v0_8-whitegrid")


def load_report(report_path: str) -> Dict[str, Any]:
    """加载 ranking_report.json 文件"""
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_visualization(report: Dict[str, Any], output_path: str) -> None:
    """创建完整的可视化图表"""

    # 创建大图，禁用 constrained_layout，使用更大尺寸
    fig = plt.figure(figsize=(28, 22), constrained_layout=False)
    fig.suptitle(
        "LRD Paper Ranking Analysis Report\n"
        f"Total: {report['total_papers']} papers | "
        f"Generated: {report['generated_at'][:10]}",
        fontsize=22,
        fontweight="bold",
        y=0.995,
    )

    # 创建网格布局，增加间距和边距
    # 使用 height_ratios 控制每行高度比例
    gs = fig.add_gridspec(
        5,
        3,
        height_ratios=[1, 1, 1, 1, 1.2],
        hspace=0.45,
        wspace=0.35,
        left=0.06,
        right=0.96,
        top=0.92,
        bottom=0.04,
    )

    # ========== 1. 总体评分分布 (左上) ==========
    ax1 = fig.add_subplot(gs[0, 0])
    scores = [paper["relevance_score"] for paper in report["papers"]]

    # 使用更美观的直方图
    n, bins, patches = ax1.hist(scores, bins=20, color="steelblue", alpha=0.7, edgecolor="black", linewidth=0.5)

    # 添加均值线
    mean_score = np.mean(scores)
    ax1.axvline(mean_score, color="red", linestyle="--", linewidth=2, label=f"Mean: {mean_score:.2f}")

    ax1.set_xlabel("Relevance Score", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Number of Papers", fontsize=11, fontweight="bold")
    ax1.set_title("Score Distribution", fontsize=13, fontweight="bold", pad=10)
    ax1.legend(fontsize=10)
    ax1.grid(axis="y", alpha=0.3)

    # 添加统计信息文本框
    stats_text = f"Mean: {np.mean(scores):.2f}\nMedian: {np.median(scores):.2f}\nStd: {np.std(scores):.2f}"
    ax1.text(
        0.95,
        0.95,
        stats_text,
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    # ========== 2. 分数区间分布 (中上) ==========
    ax2 = fig.add_subplot(gs[0, 1])

    bins_ranges = [(0, 3), (3, 5), (5, 7), (7, 8), (8, 10)]
    bin_labels = ["Low\n(<3)", "Medium-Low\n(3-5)", "Medium\n(5-7)", "Medium-High\n(7-8)", "High\n(8-10)"]
    colors = ["#d73027", "#fc8d59", "#fee08b", "#91bfdb", "#4575b4"]

    bin_counts = []
    for low, high in bins_ranges:
        if high == 10:
            count = sum(1 for s in scores if low <= s <= high)
        else:
            count = sum(1 for s in scores if low <= s < high)
        bin_counts.append(count)

    bars = ax2.bar(bin_labels, bin_counts, color=colors, alpha=0.8, edgecolor="black", linewidth=0.8)

    # 添加数值标签
    for bar, count in zip(bars, bin_counts):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{count}\n({count / len(scores) * 100:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax2.set_ylabel("Number of Papers", fontsize=11, fontweight="bold")
    ax2.set_title("Score Categories", fontsize=13, fontweight="bold", pad=10)
    ax2.set_ylim(0, max(bin_counts) * 1.15)

    # ========== 3. NotebookLM 推荐统计 (右上，饼图) ==========
    ax3 = fig.add_subplot(gs[0, 2])

    recommendations = [paper["notebooklm_recommendation"] for paper in report["papers"]]
    rec_counter = Counter(recommendations)

    # 简化标签
    simplified_labels = {
        "High priority for NotebookLM": "High",
        "Medium priority for NotebookLM": "Medium",
        "Critical priority for NotebookLM": "Critical",
        "Highest priority for NotebookLM": "Highest",
        "Medium-High priority for NotebookLM": "Medium-High",
    }

    # 简化统计
    simplified_counts = Counter()
    for rec, count in rec_counter.items():
        # 找到匹配的简化标签
        matched = False
        for key, simple_label in simplified_labels.items():
            if key in rec:
                simplified_counts[simple_label] += count
                matched = True
                break
        if not matched:
            simplified_counts["Other"] += count

    # 只显示前5个 + Other
    top_items = simplified_counts.most_common(6)
    labels = [item[0] for item in top_items]
    sizes = [item[1] for item in top_items]
    colors_pie = plt.cm.Set3(np.linspace(0, 1, len(labels)))

    wedges, texts, autotexts = ax3.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors_pie,
        startangle=90,
        textprops={"fontsize": 9},
        wedgeprops={"edgecolor": "black", "linewidth": 0.5},
    )

    # 美化百分比文本
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_fontweight("bold")

    ax3.set_title("NotebookLM Recommendations", fontsize=13, fontweight="bold", pad=10)

    # ========== 4. 年份分布 (第二行左) ==========
    ax4 = fig.add_subplot(gs[1, 0])

    years = [int(paper["year"]) for paper in report["papers"] if paper["year"].isdigit()]
    year_counts = Counter(years)

    sorted_years = sorted(year_counts.items())
    year_labels = [str(year) for year, _ in sorted_years]
    year_values = [count for _, count in sorted_years]

    bars = ax4.bar(year_labels, year_values, color="coral", alpha=0.7, edgecolor="black", linewidth=0.8)

    for bar, count in zip(bars, year_values):
        height = bar.get_height()
        ax4.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{count}\n({count / len(years) * 100:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax4.set_xlabel("Year", fontsize=11, fontweight="bold")
    ax4.set_ylabel("Number of Papers", fontsize=11, fontweight="bold")
    ax4.set_title("Publication Year Distribution", fontsize=13, fontweight="bold", pad=10)
    ax4.grid(axis="y", alpha=0.3)

    # ========== 5. 各维度评分对比 (第二行中，雷达图) ==========
    ax5 = fig.add_subplot(gs[1, 1], projection="polar")

    categories = [
        "core_lrd_focus",
        "observational_techniques",
        "physical_properties",
        "scientific_impact",
        "methodological_rigor",
    ]

    category_labels = [
        "LRD Focus",
        "Observation",
        "Physics",
        "Impact",
        "Rigor",
    ]

    # 计算每个维度的平均分
    category_avg_scores = []
    for cat in categories:
        scores = [paper["category_scores"][cat]["score"] for paper in report["papers"]]
        category_avg_scores.append(np.mean(scores))

    # 设置雷达图
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    category_avg_scores += category_avg_scores[:1]  # 闭合图形
    angles += angles[:1]

    ax5.plot(angles, category_avg_scores, "o-", linewidth=2, color="darkblue", markersize=6)
    ax5.fill(angles, category_avg_scores, alpha=0.25, color="darkblue")

    ax5.set_xticks(angles[:-1])
    ax5.set_xticklabels(category_labels, fontsize=10, fontweight="bold")
    ax5.set_ylim(0, 10)
    ax5.set_yticks([2, 4, 6, 8, 10])
    ax5.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8)
    ax5.set_title("Category Scores (Average)", fontsize=13, fontweight="bold", pad=20)
    ax5.grid(True, linestyle="--", alpha=0.7)

    # ========== 6. Top 15 标签频率 (第二行右，水平柱状图) ==========
    ax6 = fig.add_subplot(gs[1, 2])

    all_tags = []
    for paper in report["papers"]:
        if paper["existing_tags"]:
            tags = [tag.strip() for tag in paper["existing_tags"].split(",")]
            all_tags.extend(tags)

    tag_counts = Counter(all_tags)
    top_tags = tag_counts.most_common(15)

    tag_names = [tag for tag, _ in top_tags][::-1]
    tag_values = [count for _, count in top_tags][::-1]

    y_pos = np.arange(len(tag_names))
    bars = ax6.barh(y_pos, tag_values, color="lightcoral", alpha=0.7, edgecolor="black", linewidth=0.5)

    ax6.set_yticks(y_pos)
    ax6.set_yticklabels(tag_names, fontsize=9)
    ax6.invert_yaxis()
    ax6.set_xlabel("Number of Papers", fontsize=11, fontweight="bold")
    ax6.set_title("Top 15 Tags", fontsize=13, fontweight="bold", pad=10)
    ax6.grid(axis="x", alpha=0.3)

    # 添加数值标签
    for i, (bar, count) in enumerate(zip(bars, tag_values)):
        ax6.text(
            count + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{count} ({count / len(report['papers']) * 100:.1f}%)",
            va="center",
            fontsize=8,
        )

    # ========== 7. 各维度评分箱线图 (第三行，占据整行) ==========
    ax7 = fig.add_subplot(gs[2, :])

    category_data = []
    for cat in categories:
        scores = [paper["category_scores"][cat]["score"] for paper in report["papers"]]
        category_data.append(scores)

    bp = ax7.boxplot(
        category_data,
        tick_labels=category_labels,
        patch_artist=True,
        notch=True,
        showmeans=True,
    )

    # 美化箱线图
    for patch, color in zip(bp["boxes"], plt.cm.Set2(np.linspace(0, 1, len(categories)))):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    for element in ["whiskers", "fliers", "means", "medians", "caps"]:
        plt.setp(bp[element], linewidth=1.5)

    ax7.set_ylabel("Score", fontsize=11, fontweight="bold")
    ax7.set_title("Category Score Distribution (Box Plot)", fontsize=13, fontweight="bold", pad=10)
    ax7.set_ylim(0, 10.5)
    ax7.grid(axis="y", alpha=0.3)

    # ========== 8. Top 20 论文表格 (第四和第五行，占据两行) ==========
    ax8 = fig.add_subplot(gs[3:, :])
    ax8.axis("off")

    sorted_papers = sorted(report["papers"], key=lambda x: x["relevance_score"], reverse=True)
    top_papers = sorted_papers[:20]

    # 准备表格数据
    table_data = []
    for i, paper in enumerate(top_papers, 1):
        title_short = paper["title"][:60] + "..." if len(paper["title"]) > 60 else paper["title"]
        title_short = title_short.replace("{", "").replace("}", "")
        table_data.append([i, f"{paper['relevance_score']:.1f}", paper["year"], title_short, paper["bibtex_key"]])

    col_labels = ["Rank", "Score", "Year", "Title", "BibTeX Key"]
    table = ax8.table(cellText=table_data, colLabels=col_labels, cellLoc="left", loc="center", bbox=[0, 0, 1, 1])

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.5)

    # 美化表头
    for i, col in enumerate(col_labels):
        table[(0, i)].set_facecolor("#4CAF50")
        table[(0, i)].set_text_props(weight="bold", color="white")

    # 斑马纹
    for i in range(1, len(top_papers) + 1):
        for j in range(len(col_labels)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor("#f0f0f0")

    # 根据分数设置颜色
    for i, paper in enumerate(top_papers, 1):
        score = paper["relevance_score"]
        if score >= 9.0:
            color = "#d73027"  # 深红
        elif score >= 8.5:
            color = "#fc8d59"  # 橙色
        else:
            color = "#fee08b"  # 黄色
        table[(i, 1)].set_facecolor(color)
        table[(i, 1)].set_text_props(weight="bold")

    ax8.set_title("Top 20 Papers", fontsize=13, fontweight="bold", pad=10)

    # 保存图片
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"✓ 可视化图表已保存至: {output_path}")
    print(f"  分辨率: 300 DPI")
    print(f"  尺寸: 28 x 22 英寸")


def main():
    """主函数"""
    report_path = Path(__file__).parent / "ranking_report.json"
    output_path = Path(__file__).parent / "ranking_report_visualization.png"

    print(f"\n正在加载评分报告: {report_path}")
    report = load_report(report_path)

    print("正在生成可视化图表...")
    create_visualization(report, str(output_path))

    print("\n完成！")


if __name__ == "__main__":
    main()
