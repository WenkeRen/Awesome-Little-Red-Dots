"""
LRD Kick_Off Paper Relevance Ranking Script

This script processes the kick_off bibliography (library/kick_off.bib) and ranks each paper's
value as supporting literature for Little Red Dot research using AI backends (Volcengine ARK or Google Gemini).

Kick_off papers are frequently-cited references (10+ citations from LRD papers) that provide
foundational knowledge, theoretical frameworks, and methodological innovations for LRD research.

⚡ Resume Support: By default, the script will skip papers that are already ranked
in the existing kick_off_ranking_report.json file. Use --no-resume to process all papers from scratch.

Usage:
    # Resume ranking (default - skips already-ranked papers)
    python kick_off_ranker.py --backend volcengine

    # Resume with limit (processes N NEW papers)
    python kick_off_ranker.py --backend volcengine --limit 20

    # Process all papers from scratch (do not skip)
    python kick_off_ranker.py --backend volcengine --no-resume

    # Test on first 10 NEW papers
    python kick_off_ranker.py --backend volcengine --test-mode --limit 10

Output:
    Creates AIBot/results/kick_off_ranking_report.json with relevance scores and justifications.
    Incrementally saves after each paper, so you can safely interrupt and resume.

Author: Awesome-Little-Red-Dots Project
Date: 2025-01-30
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pybtex.database import parse_file
from tqdm import tqdm

# Add parent directory to path to import clients
sys.path.insert(0, str(Path(__file__).parent))

# Import both clients (will be chosen dynamically)
from gemini_client import GeminiRankingClient, GeminiRankingError
from volcengine_client import VolcengineRankingClient, VolcengineRankingError


def load_environment():
    """Load environment variables from .env file if not in GitHub Actions."""
    if not os.getenv("GITHUB_ACTIONS"):
        # Script is in AIBot/scripts/, so we need parent.parent.parent to get to repo root
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)


def parse_kick_off_bibtex(bib_path: str) -> Dict[str, Any]:
    """
    Parse kick_off BibTeX file and extract paper information.

    Args:
        bib_path: Path to kick_off.bib file

    Returns:
        Dictionary with bibtex_key -> {title, abstract, lrdIndex, tags, ...}

    Raises:
        FileNotFoundError: If bib file doesn't exist
        Exception: If bib file is invalid
    """
    if not os.path.exists(bib_path):
        raise FileNotFoundError(f"BibTeX file not found: {bib_path}")

    bib_data = parse_file(bib_path, bib_format="bibtex")

    papers = {}
    missing_abstract = 0
    missing_lrdindex = 0

    for key, entry in bib_data.entries.items():
        title = entry.fields.get("title", "")
        abstract = entry.fields.get("abstract", "")
        tags = entry.fields.get("lrdKeys", "")
        lrd_index_str = entry.fields.get("lrdIndex", "")

        # Skip papers without abstracts (optional - can be configured)
        if not abstract or abstract == "":
            missing_abstract += 1
            continue

        # Parse lrdIndex (citation count from LRD papers)
        try:
            lrd_index = int(lrd_index_str) if lrd_index_str else 0
        except ValueError:
            lrd_index = 0
            missing_lrdindex += 1

        papers[key] = {
            "bibtex_key": key,
            "title": title,
            "abstract": abstract,
            "lrdIndex": lrd_index,
            "existing_tags": tags,
            "year": entry.fields.get("year", ""),
            "authors": str(entry.persons.get("author", "")) if "author" in entry.persons else "",
        }

    if missing_abstract > 0:
        print(f"⚠ Skipped {missing_abstract} papers with missing abstracts")

    if missing_lrdindex > 0:
        print(f"⚠ {missing_lrdindex} papers missing lrdIndex field (set to 0)")

    return papers


def load_existing_report(output_path: str) -> Optional[Dict[str, Any]]:
    """
    Load existing ranking report if available.

    Args:
        output_path: Path to output JSON file

    Returns:
        Existing report dict or None if not exists
    """
    output_file = Path(output_path)
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing report: {e}")
    return None


def rank_papers(
    papers: Dict[str, Any],
    client: Union[GeminiRankingClient, VolcengineRankingClient],
    output_path: str,
    limit: Optional[int] = None,
    resume: bool = True,
) -> List[Dict[str, Any]]:
    """
    Rank kick_off papers using AI backend (Volcengine or Gemini) with incremental saving.

    Args:
        papers: Dictionary of paper information
        client: RankingClient instance (Gemini or Volcengine)
        output_path: Path to output JSON file (for incremental saving)
        limit: Maximum number of NEW papers to process (None for all)
        resume: If True, skip papers already in existing report (default: True)

    Returns:
        List of ranked papers with scores
    """
    # Load existing report to support resume
    existing_report = load_existing_report(output_path) if resume else None
    existing_papers = {}
    if existing_report and "papers" in existing_report:
        # Create a map of bibtex_key -> ranked paper data
        for paper in existing_report["papers"]:
            existing_papers[paper["bibtex_key"]] = paper
        print(f"📋 Loaded {len(existing_papers)} previously ranked papers")

    # Filter out already-ranked papers
    paper_items = []
    skipped = 0
    for bibtex_key, paper_info in papers.items():
        if bibtex_key in existing_papers and resume:
            skipped += 1
        else:
            paper_items.append((bibtex_key, paper_info))

    if skipped > 0:
        print(f"⏩ Skipping {skipped} already-ranked papers")

    # Apply limit to NEW papers only
    if limit:
        paper_items = paper_items[:limit]
        print(f"ℹ Limiting to {len(paper_items)} NEW papers")

    if not paper_items:
        print("\n✅ All papers are already ranked!")
        return list(existing_papers.values())

    # Start with existing results
    results = list(existing_papers.values())
    failed = existing_report.get("failed", 0) if existing_report else 0

    # Create output directory if needed
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize report structure
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_papers": len(papers),  # Total papers in bib file
        "successfully_scored": len(results),
        "failed": failed,
        "papers": results,
        "status": "in_progress"
    }

    print(f"\n🔬 Ranking {len(paper_items)} NEW kick_off papers...")
    print(f"💾 Saving results incrementally to: {output_path}\n")

    for idx, (bibtex_key, paper_info) in enumerate(tqdm(paper_items, desc="Processing papers"), 1):
        try:
            # Call AI backend API with lrdIndex included
            ranking = client.rank_paper(
                title=paper_info["title"],
                abstract=paper_info["abstract"],
                tags=paper_info["existing_tags"] or None,
                lrd_index=paper_info.get("lrdIndex", 0),  # Pass citation count
            )

            # Combine paper info with ranking
            result = {
                **paper_info,
                "relevance_score": ranking.get("final_score", 0),
                "justification": ranking.get("justification", ""),
                "key_factors": ranking.get("key_factors", []),
                "category_scores": ranking.get("category_scores", {}),
                "notebooklm_recommendation": ranking.get("notebooklm_recommendation", ""),
            }

            results.append(result)

            # Update report and save incrementally
            report["successfully_scored"] = len(results)
            report["failed"] = failed
            report["papers"] = results

            # Add statistics for current progress
            if results:
                report["statistics"] = {
                    "average_score": sum(r["relevance_score"] for r in results) / len(results),
                    "median_score": sorted(r["relevance_score"] for r in results)[len(results) // 2],
                    "critical_count": sum(1 for r in results if r["relevance_score"] >= 8),
                    "high_value_count": sum(1 for r in results if 6 <= r["relevance_score"] < 8),
                    "moderate_value_count": sum(1 for r in results if 4 <= r["relevance_score"] < 6),
                    "low_priority_count": sum(1 for r in results if r["relevance_score"] < 4),
                }

            # Save after each successful paper
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            tqdm.write(f"  ✓ Saved progress ({idx}/{len(paper_items)} papers)")

        except (GeminiRankingError, VolcengineRankingError) as e:
            failed += 1
            tqdm.write(f"  ❌ Failed to rank {bibtex_key}: {e}")

            # Still save progress even on failure
            report["failed"] = failed
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            continue
        except Exception as e:
            failed += 1
            tqdm.write(f"  ❌ Unexpected error for {bibtex_key}: {e}")

            # Still save progress even on failure
            report["failed"] = failed
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            continue

    # Final status update
    report["status"] = "completed"
    # Note: Final sorted report will be saved by save_report() in main()
    # This incremental save preserves progress but may not be sorted
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Successfully ranked {len(results)} papers")
    if failed > 0:
        print(f"❌ Failed to rank {failed} papers")
    print(f"💾 Incremental report saved to: {output_path}")

    return results


def get_category_score(paper: Dict[str, Any], category_name: str) -> float:
    """
    Safely get category score from a paper entry.

    Args:
        paper: Paper dictionary with category_scores
        category_name: Name of the category to retrieve

    Returns:
        Category score (0.0 if category not found)
    """
    return paper.get("category_scores", {}).get(category_name, {}).get("score", 0.0)


def save_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save ranking results to JSON report.

    Papers are sorted by:
    1. Primary: relevance_score (descending)
    2. Secondary: category scores in weight order (descending)
       - direct_lrd_connection (0.30)
       - citation_frequency (0.25)
       - foundational_value (0.20)
       - methodological_innovation (0.15)
       - evolutionary_context (0.10)

    Args:
        results: List of ranked papers
        output_path: Path to output JSON file
    """
    # Multi-level sorting: primary score, then category scores by weight
    sorted_results = sorted(
        results,
        key=lambda p: (
            -p["relevance_score"],  # Primary: relevance_score (descending)
            -get_category_score(p, "direct_lrd_connection"),  # Secondary 1: weight 0.30
            -get_category_score(p, "citation_frequency"),  # Secondary 2: weight 0.25
            -get_category_score(p, "foundational_value"),  # Secondary 3: weight 0.20
            -get_category_score(p, "methodological_innovation"),  # Secondary 4: weight 0.15
            -get_category_score(p, "evolutionary_context"),  # Secondary 5: weight 0.10
        ),
    )

    # Create report structure
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_papers": len(results),
        "successfully_scored": len(results),
        "papers": sorted_results,
        "statistics": {
            "average_score": sum(r["relevance_score"] for r in results) / len(results) if results else 0,
            "median_score": sorted(r["relevance_score"] for r in results)[len(results) // 2] if results else 0,
            "critical_count": sum(1 for r in results if r["relevance_score"] >= 8),
            "high_value_count": sum(1 for r in results if 6 <= r["relevance_score"] < 8),
            "moderate_value_count": sum(1 for r in results if 4 <= r["relevance_score"] < 6),
            "low_priority_count": sum(1 for r in results if r["relevance_score"] < 4),
        },
    }

    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Ranking report saved to: {output_path}")
    print("\n📈 Statistics:")
    print(f"  Average score: {report['statistics']['average_score']:.2f}/10")
    print(f"  Median score: {report['statistics']['median_score']:.2f}/10")
    print(f"  Critical foundation (8-10): {report['statistics']['critical_count']} papers")
    print(f"  High value supporting (6-7): {report['statistics']['high_value_count']} papers")
    print(f"  Moderate value (4-5): {report['statistics']['moderate_value_count']} papers")
    print(f"  Low priority (0-3): {report['statistics']['low_priority_count']} papers")


def print_top_papers(results: List[Dict[str, Any]], n: int = 10) -> None:
    """
    Print top N papers by relevance score.

    Args:
        results: List of ranked papers
        n: Number of top papers to display
    """
    sorted_results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    top_papers = sorted_results[:n]

    print(f"\n🏆 Top {n} Kick_Off Papers for LRD Research:")
    print("=" * 80)

    for i, paper in enumerate(top_papers, 1):
        print(f"\n{i}. Score: {paper['relevance_score']}/10 (lrdIndex: {paper.get('lrdIndex', 0)})")
        print(f"   Title: {paper['title'][:80]}...")
        if len(paper["title"]) > 80:
            print(f"         {paper['title'][80:160]}...")
        print(f"   Year: {paper['year']}")
        print(f"   Justification: {paper['justification']}")
        print(f"   Key Factors: {', '.join(paper['key_factors'][:3])}")


def main():
    """Main entry point for kick_off paper ranking script."""
    # Script is in AIBot/scripts/, so we need parent.parent.parent to get to repo root
    repo_root = Path(__file__).parent.parent.parent

    parser = argparse.ArgumentParser(description="Rank kick_off papers by relevance to LRD research using AI")
    parser.add_argument(
        "--bib-file",
        default=str(repo_root / "library" / "kick_off.bib"),
        help="Path to kick_off BibTeX file (default: library/kick_off.bib)",
    )
    parser.add_argument(
        "--output",
        default=str(repo_root / "AIBot" / "results" / "kick_off_ranking_report.json"),
        help="Output JSON report path (default: AIBot/results/kick_off_ranking_report.json)",
    )
    parser.add_argument(
        "--criteria",
        default=str(repo_root / "AIBot" / "data" / "kick_off_ranking_criteria.json"),
        help="Path to ranking criteria JSON (default: AIBot/data/kick_off_ranking_criteria.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit processing to first N papers (useful for testing)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Enable test mode (shows top papers and stops)",
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=10,
        help="Number of top papers to display (default: 10)",
    )
    parser.add_argument(
        "--backend",
        choices=["volcengine", "gemini"],
        default="volcengine",
        help="AI backend to use (default: volcengine)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to use (backend-dependent default if not specified)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not skip already-ranked papers (process all papers from scratch)",
    )

    args = parser.parse_args()

    # Set default models based on backend
    if args.model is None:
        if args.backend == "volcengine":
            args.model = "kimi-k2-thinking-251104"
        else:  # gemini
            args.model = "gemini-2.5-flash"

    # Load environment variables
    load_environment()

    print("🚀 LRD Kick_Off Paper Relevance Ranking System")
    print("=" * 50)
    print(f"Backend: {args.backend.upper()}")
    print(f"Model: {args.model}")
    print("=" * 50)

    # Check API key based on backend
    if args.backend == "volcengine":
        if not os.getenv("ARK_API_KEY"):
            print("❌ Error: ARK_API_KEY not found in environment")
            print("   Set it in .env file or export ARK_API_KEY=your_key")
            sys.exit(1)
    else:  # gemini
        if not os.getenv("GEMINI_API_KEY"):
            print("❌ Error: GEMINI_API_KEY not found in environment")
            print("   Set it in .env file or export GEMINI_API_KEY=your_key")
            sys.exit(1)

    try:
        # Initialize appropriate client based on backend
        print(f"\n🔧 Initializing {args.backend.capitalize()} client (model: {args.model})...")

        if args.backend == "volcengine":
            client = VolcengineRankingClient(
                criteria_path=args.criteria,
                model_name=args.model,
            )
        else:  # gemini
            client = GeminiRankingClient(
                criteria_path=args.criteria,
                model_name=args.model,
            )

        # Parse kick_off BibTeX file
        print(f"\n📚 Parsing kick_off BibTeX file: {args.bib_file}")
        papers = parse_kick_off_bibtex(args.bib_file)
        print(f"✓ Loaded {len(papers)} papers")

        if args.limit:
            print(f"ℹ Limiting to first {args.limit} papers")

        # Rank papers (with incremental saving and resume support)
        resume = not args.no_resume
        results = rank_papers(papers, client, output_path=args.output, limit=args.limit, resume=resume)

        if not results:
            print("❌ No papers were successfully ranked")
            sys.exit(1)

        # Print top papers
        print_top_papers(results, n=args.show_top)

        # Save final sorted report
        print("\n💾 Saving final sorted report...")
        save_report(results, args.output)

        # Test mode summary
        if args.test_mode:
            print("\n" + "=" * 80)
            print("✅ Test mode completed successfully!")
            print(f"   Processed {len(results)} papers")
            print("\n📝 To process all papers, run:")
            print(f"   python {sys.argv[0]}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
