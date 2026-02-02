"""
Google Gen AI client wrapper for LRD paper ranking.

This module provides a robust interface to Google's Gemini AI API for scoring
paper relevance to Little Red Dot research. Includes retry logic, error handling,
and response parsing.

Uses the NEW google-genai SDK (not the deprecated google-generativeai).

Author: Awesome-Little-Red-Dots Project
Date: 2025-01-29
"""

import json
import os
import time
from typing import Dict, Any, Optional

from google import genai
from google.genai import types


class GeminiRankingError(Exception):
    """Custom exception for Gemini ranking errors."""
    pass


class GeminiRankingClient:
    """
    Client for ranking LRD papers using Google's Gemini API.

    Attributes:
        client: Configured GenAI client instance
        ranking_criteria: Loaded ranking criteria JSON
        max_retries: Maximum number of retry attempts
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        criteria_path: str = "AIBot/data/lrd_ranking_criteria.json",
        model_name: str = "gemini-2.5-flash",
        max_retries: int = 3,
    ):
        """
        Initialize the Gemini ranking client.

        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
            criteria_path: Path to ranking criteria JSON file
            model_name: Gemini model to use (default: gemini-2.5-flash)
            max_retries: Maximum retry attempts for failed API calls

        Raises:
            FileNotFoundError: If criteria file not found
            ValueError: If API key not provided or found in environment
        """
        # Load API key
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set environment variable or pass api_key parameter."
            )

        # Initialize GenAI client
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.max_retries = max_retries

        # Load ranking criteria
        self.criteria_path = criteria_path
        self.ranking_criteria = self._load_criteria()

    def _load_criteria(self) -> Dict[str, Any]:
        """
        Load ranking criteria from JSON file.

        Returns:
            Dictionary containing scoring categories and rubric

        Raises:
            FileNotFoundError: If criteria file doesn't exist
            json.JSONDecodeError: If criteria file is invalid JSON
        """
        try:
            with open(self.criteria_path, "r", encoding="utf-8") as f:
                criteria = json.load(f)
            return criteria
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Ranking criteria file not found: {self.criteria_path}\n"
                "Ensure lrd_ranking_criteria.json exists in AIBot/data/ directory."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in criteria file: {e}")

    def _build_prompt(self, title: str, abstract: str, tags: Optional[str] = None, lrd_index: Optional[int] = None) -> str:
        """
        Build the prompt for Gemini API with paper details and ranking criteria.

        Args:
            title: Paper title
            abstract: Paper abstract
            tags: Comma-separated lrdKeys tags (optional)
            lrd_index: Citation count from LRD papers (for kick_off papers, optional)

        Returns:
            Formatted prompt string
        """
        # Extract prompt template from criteria
        prompt_template = self.ranking_criteria.get("usage_instructions", {}).get(
            "prompt_template", ""
        )

        # Replace {lrdIndex} placeholder in template if present
        if lrd_index is not None and "{lrdIndex}" in prompt_template:
            prompt_template = prompt_template.replace("{lrdIndex}", str(lrd_index))

        # Build paper details section
        paper_details = f"""**Paper Title:** {title}

**Abstract:** {abstract}"""

        if tags:
            paper_details += f"\n\n**Existing Tags:** {tags}"

        if lrd_index is not None:
            paper_details += f"\n\n**LRD Community Citation Count (lrdIndex):** {lrd_index}"

        # Combine template with paper details
        full_prompt = f"""{prompt_template}

**Paper to Evaluate:**

{paper_details}

**Evaluation:**
Provide your scoring assessment following the JSON structure specified above."""

        return full_prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini API response and extract JSON.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Parsed JSON dictionary with scores and reasoning

        Raises:
            GeminiRankingError: If response cannot be parsed as JSON
        """
        # Try to extract JSON from response
        # Sometimes Gemini adds markdown code blocks or extra text
        try:
            # First, try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                # Extract content between ```json and ```
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                # Extract content between first ``` and closing ```
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            else:
                # Try to find JSON-like structure with braces
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                    return json.loads(json_str)

        raise GeminiRankingError(
            f"Failed to parse JSON from Gemini response:\n{response_text[:500]}..."
        )

    def rank_paper(
        self, title: str, abstract: str, tags: Optional[str] = None, lrd_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rank a single paper's relevance to LRD research.

        Args:
            title: Paper title
            abstract: Paper abstract
            tags: Comma-separated lrdKeys tags (optional)
            lrd_index: Citation count from LRD papers (for kick_off papers, optional)

        Returns:
            Dictionary with:
                - category_scores: Dict of individual category scores
                - final_score: Overall weighted score (0-10)
                - justification: Text explanation
                - key_factors: List of key reasons
                - notebooklm_recommendation: Priority level

        Raises:
            GeminiRankingError: If ranking fails after all retries
        """
        prompt = self._build_prompt(title, abstract, tags, lrd_index)

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )

                # Extract text from response
                response_text = response.text
                result = self._parse_response(response_text)

                # Validate response structure
                if "final_score" not in result:
                    raise GeminiRankingError("Response missing 'final_score' field")

                return result

            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"  ⚠ JSON parse error, retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise GeminiRankingError(f"Failed to parse response after {self.max_retries} attempts: {e}")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    print(f"  ⚠ API error: {e}, retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise GeminiRankingError(f"Failed to rank paper after {self.max_retries} attempts: {e}")

        # Should never reach here
        raise GeminiRankingError("Unexpected error in ranking logic")

    def get_criteria_summary(self) -> str:
        """
        Get a summary of the ranking criteria for display/logging.

        Returns:
            Formatted string describing the scoring system
        """
        categories = self.ranking_criteria.get("scoring_categories", [])

        summary_lines = [
            "LRD Paper Ranking Criteria",
            "=" * 40,
            f"Version: {self.ranking_criteria.get('version', 'N/A')}",
            f"Last Updated: {self.ranking_criteria.get('last_updated', 'N/A')}",
            "",
            "Scoring Categories:",
        ]

        for cat in categories:
            summary_lines.append(f"  - {cat['name']} (weight: {cat['weight']:.0%})")
            summary_lines.append(f"    {cat['description']}")

        summary_lines.extend([
            "",
            "Score Interpretation:",
        ])

        score_interp = self.ranking_criteria.get("score_interpretation", {})
        for range_str, info in score_interp.items():
            summary_lines.append(f"  {range_str}: {info['label']}")

        return "\n".join(summary_lines)


# Convenience function for quick testing
def test_client(api_key: Optional[str] = None) -> None:
    """
    Test the Gemini client with a sample paper.

    Args:
        api_key: Google API key (optional, uses env var if not provided)
    """
    client = GeminiRankingClient(api_key=api_key)

    print(client.get_criteria_summary())
    print("\n" + "=" * 40)
    print("Testing with sample paper...")
    print("=" * 40 + "\n")

    sample_title = (
        "'Little red dots' in the JWST era: Evidence for obscured AGN at z ~ 4-7"
    )
    sample_abstract = """\
We present a analysis of compact red sources detected in JWST NIRCam imaging from the CEERS survey.
With photometric redshifts z ~ 4-7, these objects exhibit red rest-frame optical colors and
point-source morphologies. Spectroscopic follow-up with NIRSpec reveals broad emission lines
in several sources, with FWHM > 2000 km/s and high equivalent widths. We measure black hole
masses using virial scaling relations, finding M_BH ~ 10^7-10^8 M_sun. The X-ray stacking
shows non-detections, suggesting heavy obscuration with N_H > 10^24 cm^-2. We argue that
these 'little red dots' represent a population of obscured AGN undergoing rapid growth
in the early universe."""

    try:
        result = client.rank_paper(sample_title, sample_abstract, "jwst, spectroscopy, black hole mass")

        print(f"Final Score: {result['final_score']}/10")
        print(f"Justification: {result['justification']}")
        print(f"Key Factors: {', '.join(result['key_factors'])}")
        print(f"\nCategory Scores:")
        for cat, scores in result['category_scores'].items():
            print(f"  {cat}: {scores['score']}/10 - {scores['reasoning']}")

    except GeminiRankingError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run test if executed directly
    test_client()
