"""
LRD Paper Relevance Ranking Script

This script processes the LRD bibliography (aslrd.bib) and ranks each paper's
relevance to Little Red Dot research using AI backends (Volcengine ARK or Google Gemini).

Usage:
    # Test on first 10 papers with Volcengine
    python paper_ranker.py --backend volcengine --test-mode --limit 10

    # Process all papers with Gemini
    python paper_ranker.py --backend gemini --full

Output:
    Creates AIBot/ranking_report.json with relevance scores and justifications.

Author: Awesome-Little-Red-Dots Project
Date: 2025-01-29
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
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)


def parse_bibtex(bib_path: str) -> Dict[str, Any]:
    """
    Parse BibTeX file and extract paper information.

    Args:
        bib_path: Path to aslrd.bib file

    Returns:
        Dictionary with bibtex_key -> {title, abstract, tags, ...}

    Raises:
        FileNotFoundError: If bib file doesn't exist
        Exception: If bib file is invalid
    """
    if not os.path.exists(bib_path):
        raise FileNotFoundError(f"BibTeX file not found: {bib_path}")

    bib_data = parse_file(bib_path, bib_format="bibtex")

    papers = {}
    missing_abstract = 0

    for key, entry in bib_data.entries.items():
        title = entry.fields.get("title", "")
        abstract = entry.fields.get("abstract", "")
        tags = entry.fields.get("lrdKeys", "")

        # Skip papers without abstracts (optional - can be configured)
        if not abstract or abstract == "":
            missing_abstract += 1
            continue

        papers[key] = {
            "bibtex_key": key,
            "title": title,
            "abstract": abstract,
            "existing_tags": tags,
            "year": entry.fields.get("year", ""),
            "authors": str(entry.persons.get("author", "")) if "author" in entry.persons else "",
        }

    if missing_abstract > 0:
        print(f"⚠ Skipped {missing_abstract} papers with missing abstracts")

    return papers


def rank_papers(
    papers: Dict[str, Any],
    client: Union[GeminiRankingClient, VolcengineRankingClient],
    output_path: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Rank papers using AI backend (Volcengine or Gemini) with incremental saving.

    Args:
        papers: Dictionary of paper information
        client: RankingClient instance (Gemini or Volcengine)
        output_path: Path to output JSON file (for incremental saving)
        limit: Maximum number of papers to process (None for all)

    Returns:
        List of ranked papers with scores
    """
    # Apply limit if specified
    paper_items = list(papers.items())
    if limit:
        paper_items = paper_items[:limit]

    results = []
    failed = 0

    # Create output directory if needed
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize report structure
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_papers": len(paper_items),
        "successfully_scored": 0,
        "failed": 0,
        "papers": [],
        "status": "in_progress"
    }

    print(f"\n🔬 Ranking {len(paper_items)} papers...")
    print(f"💾 Saving results incrementally to: {output_path}\n")

    for idx, (bibtex_key, paper_info) in enumerate(tqdm(paper_items, desc="Processing papers"), 1):
        try:
            # Call AI backend API
            ranking = client.rank_paper(
                title=paper_info["title"],
                abstract=paper_info["abstract"],
                tags=paper_info["existing_tags"] or None,
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
                    "high_relevance_count": sum(1 for r in results if r["relevance_score"] >= 7),
                    "moderate_relevance_count": sum(1 for r in results if 4 <= r["relevance_score"] < 7),
                    "low_relevance_count": sum(1 for r in results if r["relevance_score"] < 4),
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
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Successfully ranked {len(results)} papers")
    if failed > 0:
        print(f"❌ Failed to rank {failed} papers")
    print(f"💾 Final report saved to: {output_path}")

    return results


def save_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save ranking results to JSON report.

    Args:
        results: List of ranked papers
        output_path: Path to output JSON file
    """
    # Sort by relevance score (descending)
    sorted_results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    # Create report structure
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_papers": len(results),
        "successfully_scored": len(results),
        "papers": sorted_results,
        "statistics": {
            "average_score": sum(r["relevance_score"] for r in results) / len(results) if results else 0,
            "median_score": sorted(r["relevance_score"] for r in results)[len(results) // 2] if results else 0,
            "high_relevance_count": sum(1 for r in results if r["relevance_score"] >= 7),
            "moderate_relevance_count": sum(1 for r in results if 4 <= r["relevance_score"] < 7),
            "low_relevance_count": sum(1 for r in results if r["relevance_score"] < 4),
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
    print(f"  High relevance (7-10): {report['statistics']['high_relevance_count']} papers")
    print(f"  Moderate relevance (4-6): {report['statistics']['moderate_relevance_count']} papers")
    print(f"  Low relevance (0-3): {report['statistics']['low_relevance_count']} papers")


def print_top_papers(results: List[Dict[str, Any]], n: int = 10) -> None:
    """
    Print top N papers by relevance score.

    Args:
        results: List of ranked papers
        n: Number of top papers to display
    """
    sorted_results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    top_papers = sorted_results[:n]

    print(f"\n🏆 Top {n} LRD Papers by Relevance:")
    print("=" * 80)

    for i, paper in enumerate(top_papers, 1):
        print(f"\n{i}. Score: {paper['relevance_score']}/10")
        print(f"   Title: {paper['title'][:80]}...")
        if len(paper["title"]) > 80:
            print(f"         {paper['title'][80:160]}...")
        print(f"   Year: {paper['year']}")
        print(f"   Justification: {paper['justification']}")
        print(f"   Key Factors: {', '.join(paper['key_factors'][:3])}")


def main():
    """Main entry point for paper ranking script."""
    parser = argparse.ArgumentParser(description="Rank LRD papers by relevance using Google Gemini AI")
    parser.add_argument(
        "--bib-file",
        default="library/aslrd.bib",
        help="Path to BibTeX file (default: library/aslrd.bib)",
    )
    parser.add_argument(
        "--output",
        default="AIBot/ranking_report.json",
        help="Output JSON report path (default: AIBot/ranking_report.json)",
    )
    parser.add_argument(
        "--criteria",
        default="AIBot/lrd_ranking_criteria.json",
        help="Path to ranking criteria JSON (default: AIBot/lrd_ranking_criteria.json)",
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

    args = parser.parse_args()

    # Set default models based on backend
    if args.model is None:
        if args.backend == "volcengine":
            args.model = "kimi-k2-thinking-251104"
        else:  # gemini
            args.model = "gemini-2.5-flash"

    # Load environment variables
    load_environment()

    print("🚀 LRD Paper Relevance Ranking System")
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

        # Parse BibTeX file
        print(f"\n📚 Parsing BibTeX file: {args.bib_file}")
        papers = parse_bibtex(args.bib_file)
        print(f"✓ Loaded {len(papers)} papers")

        if args.limit:
            print(f"ℹ Limiting to first {args.limit} papers")

        # Rank papers (with incremental saving)
        results = rank_papers(papers, client, output_path=args.output, limit=args.limit)

        if not results:
            print("❌ No papers were successfully ranked")
            sys.exit(1)

        # Print top papers
        print_top_papers(results, n=args.show_top)

        # Test mode summary
        if args.test_mode:
            print("\n" + "=" * 80)
            print("✅ Test mode completed successfully!")
            print(f"   Processed {len(results)} papers")
            print("\n📝 To process all papers, run:")
            print(f"   python {sys.argv[0]} --full")

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
