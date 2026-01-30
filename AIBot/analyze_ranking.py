"""
分析 paper_ranker.py 生成的评分报告统计信息
"""

from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

import json


def load_report(report_path: str) -> Dict[str, Any]:
    """加载 ranking_report.json 文件"""
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_basic_stats(report: Dict[str, Any]) -> None:
    """打印基本统计信息"""
    print("=" * 80)
    print("基本统计信息")
    print("=" * 80)
    print(f"生成时间: {report['generated_at']}")
    print(f"论文总数: {report['total_papers']}")
    print(f"成功评分: {report['successfully_scored']}")
    print(f"失败数量: {report['failed']}")
    if report["failed"] > 0:
        print(f"  ⚠️  成功率: {report['successfully_scoreed'] / report['total_papers'] * 100:.1f}%")
    print()


def print_score_distribution(report: Dict[str, Any]) -> None:
    """打印评分分布统计"""
    print("=" * 80)
    print("总体评分分布 (relevance_score)")
    print("=" * 80)

    scores = [paper["relevance_score"] for paper in report["papers"]]

    print(f"平均分: {sum(scores) / len(scores):.2f}")
    print(f"中位数: {sorted(scores)[len(scores) // 2]:.2f}")
    print(f"最高分: {max(scores):.2f}")
    print(f"最低分: {min(scores):.2f}")

    # 分数区间统计
    bins = [(0, 3), (3, 5), (5, 7), (7, 8), (8, 10)]
    bin_labels = ["低 (<3)", "较低 (3-5)", "中等 (5-7)", "较高 (7-8)", "高 (8-10)"]

    print("\n分数区间分布:")
    for (low, high), label in zip(bins, bin_labels):
        count = sum(1 for s in scores if low <= s < high)
        if high == 10:  # 包含上限
            count = sum(1 for s in scores if low <= s <= high)
        pct = count / len(scores) * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:15s}: {count:3d} ({pct:5.1f}%) {bar}")

    print()


def print_category_scores(report: Dict[str, Any]) -> None:
    """打印各维度评分统计"""
    print("=" * 80)
    print("各维度评分统计")
    print("=" * 80)

    categories = [
        "core_lrd_focus",
        "observational_techniques",
        "physical_properties",
        "scientific_impact",
        "methodological_rigor",
    ]

    category_labels = {
        "core_lrd_focus": "LRD核心度",
        "observational_techniques": "观测技术",
        "physical_properties": "物理特性",
        "scientific_impact": "科学影响",
        "methodological_rigor": "方法严谨性",
    }

    for cat in categories:
        scores = [paper["category_scores"][cat]["score"] for paper in report["papers"]]
        avg = sum(scores) / len(scores)
        print(f"{category_labels[cat]:15s}: 平均 {avg:.2f} | 最高 {max(scores):.1f} | 最低 {min(scores):.1f}")

    print()


def print_top_papers(report: Dict[str, Any], top_n: int = 20) -> None:
    """打印高分论文"""
    print("=" * 80)
    print(f"Top {top_n} 高分论文")
    print("=" * 80)

    sorted_papers = sorted(report["papers"], key=lambda x: x["relevance_score"], reverse=True)

    for i, paper in enumerate(sorted_papers[:top_n], 1):
        print(f"\n{i}. [{paper['relevance_score']:.1f}] {paper['bibtex_key']}")
        print(f"   标题: {paper['title'][:100]}...")
        print(f"   年份: {paper['year']}")
        print(f"   标签: {paper['existing_tags']}")
        print(f"   NotebookLM: {paper['notebooklm_recommendation']}")


def print_notebooklm_stats(report: Dict[str, Any]) -> None:
    """打印 NotebookLM 推荐统计"""
    print("=" * 80)
    print("NotebookLM 推荐统计")
    print("=" * 80)

    recommendations = [paper["notebooklm_recommendation"] for paper in report["papers"]]
    counter = Counter(recommendations)

    for rec, count in counter.most_common():
        pct = count / len(recommendations) * 100
        bar = "█" * int(pct / 2)
        print(f"{rec:30s}: {count:3d} ({pct:5.1f}%) {bar}")

    print()


def print_year_distribution(report: Dict[str, Any]) -> None:
    """打印年份分布"""
    print("=" * 80)
    print("年份分布")
    print("=" * 80)

    years = [int(paper["year"]) for paper in report["papers"] if paper["year"].isdigit()]
    year_counts = Counter(years)

    for year in sorted(year_counts.keys()):
        count = year_counts[year]
        pct = count / len(years) * 100
        bar = "█" * int(pct / 2)
        print(f"{year:4d}: {count:3d} ({pct:5.1f}%) {bar}")

    print()


def print_tag_frequency(report: Dict[str, Any], top_n: int = 20) -> None:
    """打印标签频率统计"""
    print("=" * 80)
    print(f"Top {top_n} 最常见标签")
    print("=" * 80)

    all_tags = []
    for paper in report["papers"]:
        if paper["existing_tags"]:
            tags = [tag.strip() for tag in paper["existing_tags"].split(",")]
            all_tags.extend(tags)

    tag_counts = Counter(all_tags)

    for i, (tag, count) in enumerate(tag_counts.most_common(top_n), 1):
        pct = count / len(report["papers"]) * 100
        print(f"{i:2d}. {tag:30s}: {count:3d} ({pct:5.1f}%)")

    print()


def print_score_by_tag(report: Dict[str, Any]) -> None:
    """分析各标签论文的平均评分"""
    print("=" * 80)
    print("各标签论文的平均评分 (Top 15)")
    print("=" * 80)

    tag_scores: Dict[str, List[float]] = {}

    for paper in report["papers"]:
        if paper["existing_tags"]:
            tags = [tag.strip() for tag in paper["existing_tags"].split(",")]
            for tag in tags:
                if tag not in tag_scores:
                    tag_scores[tag] = []
                tag_scores[tag].append(paper["relevance_score"])

    # 计算每个标签的平均分并排序
    tag_avg_scores = {tag: sum(scores) / len(scores) for tag, scores in tag_scores.items()}
    sorted_tags = sorted(tag_avg_scores.items(), key=lambda x: x[1], reverse=True)

    for i, (tag, avg_score) in enumerate(sorted_tags[:15], 1):
        count = len(tag_scores[tag])
        print(f"{i:2d}. {tag:30s}: {avg_score:.2f} (n={count})")

    print()


def main():
    """主函数"""
    report_path = Path(__file__).parent / "ranking_report.json"

    print(f"\n正在加载评分报告: {report_path}\n")
    report = load_report(report_path)

    # 打印各类统计信息
    print_basic_stats(report)
    print_score_distribution(report)
    print_category_scores(report)
    print_notebooklm_stats(report)
    print_year_distribution(report)
    print_tag_frequency(report)
    print_score_by_tag(report)
    print_top_papers(report, top_n=20)

    print("=" * 80)
    print("分析完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
