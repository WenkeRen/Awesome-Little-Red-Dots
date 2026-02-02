#!/usr/bin/env python3
"""
Generate NotebookLM paper list from ranking reports.

This script:
1. Reads ranking reports (LRD and kick_off)
2. Loads BibTeX files to extract eprint (arXiv ID) information
3. Selects top papers by relevance score that have eprint
4. Generates a consolidated list for NotebookLM

Output:
- LRD papers: Top 200 with eprint
- Kick_off papers: Top 50 with eprint
- Total: 250 papers
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from pybtex.database import parse_file
from typing import Dict, List, Optional, Tuple


def load_bibtex_eprint_ids(bib_file_path: str) -> Dict[str, str]:
    """
    Load arXiv eprint IDs from BibTeX file.

    Args:
        bib_file_path: Path to BibTeX file

    Returns:
        Dictionary mapping bibtex_key -> eprint (arXiv ID)
    """
    eprint_map = {}
    bib_path = Path(bib_file_path)

    if not bib_path.exists():
        print(f"⚠️  BibTeX file not found: {bib_file_path}")
        return eprint_map

    try:
        bib_data = parse_file(bib_path, bib_format="bibtex")

        for key, entry in bib_data.entries.items():
            # Check for eprint field (case-insensitive)
            eprint = None
            for field_name in entry.fields:
                if field_name.lower() == "eprint":
                    eprint = entry.fields[field_name]
                    # Remove version suffix if present (e.g., 2301.12345v1 -> 2301.12345)
                    if eprint and "v" in eprint:
                        # Check if version suffix exists (v followed by number)
                        parts = eprint.split("v")
                        if len(parts) > 1 and parts[1].isdigit():
                            eprint = parts[0]
                    break

            if eprint:
                eprint_map[key] = eprint

        print(f"✓ Loaded {len(eprint_map)} eprint IDs from {bib_file_path}")
        return eprint_map

    except Exception as e:
        print(f"❌ Error parsing BibTeX file {bib_file_path}: {e}")
        return eprint_map


def load_ranking_report(report_path: str) -> Tuple[List[Dict], str]:
    """
    Load papers from ranking report.

    Args:
        report_path: Path to ranking report JSON file

    Returns:
        Tuple of (papers list, generated timestamp)
    """
    report_path = Path(report_path)

    if not report_path.exists():
        print(f"⚠️  Ranking report not found: {report_path}")
        return [], ""

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        papers = report.get("papers", [])
        generated_at = report.get("generated_at", "")

        print(f"✓ Loaded {len(papers)} papers from {report_path}")
        return papers, generated_at

    except Exception as e:
        print(f"❌ Error loading ranking report {report_path}: {e}")
        return [], ""


def select_papers_with_eprint(
    papers: List[Dict], eprint_map: Dict[str, str], max_count: int
) -> Tuple[List[Tuple[str, str, float]], List[Tuple[str, str, float]]]:
    """
    Select papers with eprint from ranked list, and track high-scoring papers without eprint.

    Args:
        papers: List of paper dictionaries from ranking report
        eprint_map: Dictionary mapping bibtex_key -> eprint
        max_count: Maximum number of papers to select

    Returns:
        Tuple of:
        - List of tuples (bibtex_key, eprint, relevance_score) for papers with eprint
        - List of tuples (bibtex_key, title, relevance_score) for high-scoring papers without eprint
    """
    selected = []
    skipped_high_quality = []

    for paper in papers:
        bibtex_key = paper.get("bibtex_key", "")
        relevance_score = paper.get("relevance_score", 0.0)
        title = paper.get("title", "")

        if not bibtex_key:
            continue

        if bibtex_key in eprint_map:
            if len(selected) < max_count:
                eprint = eprint_map[bibtex_key]
                selected.append((bibtex_key, eprint, relevance_score))
        else:
            # Track papers without eprint that have high scores (>= 7.0)
            if relevance_score >= 7.0:
                skipped_high_quality.append((bibtex_key, title, relevance_score))

    return selected, skipped_high_quality


def generate_notebooklm_list(
    lrd_report: str,
    kick_off_report: str,
    aslrd_bib: str,
    kick_off_bib: str,
    output_path: str,
    lrd_count: int = 200,
    kick_off_count: int = 50,
) -> None:
    """
    Generate consolidated NotebookLM paper list.

    Args:
        lrd_report: Path to LRD ranking report
        kick_off_report: Path to kick_off ranking report
        aslrd_bib: Path to aslrd.bib file
        kick_off_bib: Path to kick_off.bib file
        output_path: Path to output text file
        lrd_count: Number of LRD papers to select
        kick_off_count: Number of kick_off papers to select
    """
    print("=" * 80)
    print("Generating NotebookLM Paper List")
    print("=" * 80)

    # Load ranking reports
    print("\n📊 Loading ranking reports...")
    lrd_papers, lrd_generated_at = load_ranking_report(lrd_report)
    kick_off_papers, kick_off_generated_at = load_ranking_report(kick_off_report)

    if not lrd_papers and not kick_off_papers:
        print("❌ No papers found in ranking reports")
        return

    # Load eprint IDs from BibTeX files
    print("\n📚 Loading eprint IDs from BibTeX files...")
    aslrd_eprints = load_bibtex_eprint_ids(aslrd_bib)
    kick_off_eprints = load_bibtex_eprint_ids(kick_off_bib)

    # Select papers with eprint
    print(f"\n🔍 Selecting top {lrd_count} LRD papers with eprint...")
    lrd_selected, lrd_skipped = select_papers_with_eprint(lrd_papers, aslrd_eprints, lrd_count)

    print(f"🔍 Selecting top {kick_off_count} kick_off papers with eprint...")
    kick_off_selected, kick_off_skipped = select_papers_with_eprint(kick_off_papers, kick_off_eprints, kick_off_count)

    if not lrd_selected and not kick_off_selected:
        print("❌ No papers with eprint found")
        return

    # Generate output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generation_time = datetime.now().isoformat()

    with open(output_path, "w", encoding="utf-8") as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("NOTEBOOKLM PAPER LIST\n")
        f.write("=" * 80 + "\n")
        f.write(f"\nGenerated: {generation_time}\n")
        f.write(f"Total papers: {len(lrd_selected) + len(kick_off_selected)}\n")
        f.write(f"  - LRD papers: {len(lrd_selected)}\n")
        f.write(f"  - Kick_off papers: {len(kick_off_selected)}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("LRD PAPERS (Top 200 by relevance score)\n")
        f.write("=" * 80 + "\n\n")

        # LRD papers
        for i, (bibtex_key, eprint, score) in enumerate(lrd_selected, 1):
            f.write(f"{i:3d}. {eprint}  (score: {score:.1f}, key: {bibtex_key})\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("KICK_OFF PAPERS (Top 50 by relevance score)\n")
        f.write("=" * 80 + "\n\n")

        # Kick_off papers
        for i, (bibtex_key, eprint, score) in enumerate(kick_off_selected, 1):
            f.write(f"{i:3d}. {eprint}  (score: {score:.1f}, key: {bibtex_key})\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("ARXIV IDs ONLY (for automated processing)\n")
        f.write("=" * 80 + "\n\n")

        # Consolidated arXiv ID list
        all_eprints = [eprint for _, eprint, _ in lrd_selected] + [eprint for _, eprint, _ in kick_off_selected]
        for eprint in all_eprints:
            f.write(f"{eprint}\n")

        # High-scoring papers without eprint (skipped from NotebookLM)
        all_skipped = lrd_skipped + kick_off_skipped
        if all_skipped:
            f.write("\n" + "=" * 80 + "\n")
            f.write("HIGH-SCORING PAPERS WITHOUT ARXIV ID (score >= 7.0)\n")
            f.write("=" * 80)
            f.write("\n\nThese papers have high relevance scores but lack arXiv eprint field.\n")
            f.write("They were excluded from NotebookLM list but may be worth adding manually.\n\n")

            # Sort by score descending
            all_skipped_sorted = sorted(all_skipped, key=lambda x: x[2], reverse=True)

            for bibtex_key, title, score in all_skipped_sorted:
                # Clean up title - remove extra formatting
                clean_title = title.strip()
                if clean_title.startswith("{") and clean_title.endswith("}"):
                    clean_title = clean_title[1:-1]
                f.write(f"[{score:.1f}] {bibtex_key}\n")
                f.write(f"    {clean_title}\n\n")

    print(f"\n✅ Successfully generated NotebookLM paper list: {output_path}")
    print(f"   Total papers: {len(lrd_selected) + len(kick_off_selected)}")
    print(f"   - LRD: {len(lrd_selected)}")
    print(f"   - Kick_off: {len(kick_off_selected)}")

    if lrd_skipped or kick_off_skipped:
        total_skipped = len(lrd_skipped) + len(kick_off_skipped)
        print(f"\n⚠️  Note: {total_skipped} high-scoring papers without arXiv ID (see file for details)")

    if len(lrd_selected) < lrd_count:
        print(f"\n⚠️  Warning: Only found {len(lrd_selected)} LRD papers with eprint (requested {lrd_count})")

    if len(kick_off_selected) < kick_off_count:
        print(f"⚠️  Warning: Only found {len(kick_off_selected)} kick_off papers with eprint (requested {kick_off_count})")


def main():
    """Main entry point."""
    # Default paths (relative to repository root)
    repo_root = Path(__file__).parent.parent.parent
    default_lrd_report = repo_root / "AIBot" / "results" / "ranking_report.json"
    default_kick_off_report = repo_root / "AIBot" / "results" / "kick_off_ranking_report.json"
    default_aslrd_bib = repo_root / "library" / "aslrd.bib"
    default_kick_off_bib = repo_root / "library" / "kick_off.bib"
    default_output = repo_root / "AIBot" / "results" / "notebooklm_paper_list.txt"

    # Check if reports exist
    if not default_lrd_report.exists():
        print(f"❌ LRD ranking report not found: {default_lrd_report}")
        print("   Please run paper_ranker.py first to generate the ranking report.")
        sys.exit(1)

    if not default_kick_off_report.exists():
        print(f"❌ Kick_off ranking report not found: {default_kick_off_report}")
        print("   Please run kick_off_ranker.py first to generate the ranking report.")
        sys.exit(1)

    # Generate list
    generate_notebooklm_list(
        lrd_report=str(default_lrd_report),
        kick_off_report=str(default_kick_off_report),
        aslrd_bib=str(default_aslrd_bib),
        kick_off_bib=str(default_kick_off_bib),
        output_path=str(default_output),
        lrd_count=200,
        kick_off_count=50,
    )


if __name__ == "__main__":
    main()
