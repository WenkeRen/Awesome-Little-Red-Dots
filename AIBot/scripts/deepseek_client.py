"""
DeepSeek API client wrapper for LRD paper ranking.

This module provides a robust interface to DeepSeek's official OpenAI-compatible
API for scoring paper relevance to Little Red Dot research. Includes retry logic,
error handling, and response parsing.

Author: Awesome-Little-Red-Dots Project
Date: 2026-08-06
"""

import json
import os
import time
from typing import Any, Dict, Optional

from openai import OpenAI


class DeepSeekRankingError(Exception):
    """Custom exception for DeepSeek ranking errors."""

    pass


class DeepSeekRankingClient:
    """
    Client for ranking LRD papers using DeepSeek's official API.

    Attributes:
        client: Configured OpenAI-compatible client instance
        model_name: Model identifier for DeepSeek API
        ranking_criteria: Loaded ranking criteria JSON
        max_retries: Maximum number of retry attempts
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        criteria_path: str = "AIBot/data/lrd_ranking_criteria.json",
        model_name: str = "deepseek-v4-pro",
        max_retries: int = 3,
    ):
        """
        Initialize the DeepSeek ranking client.

        Args:
            api_key: DeepSeek API key (defaults to DS_API_KEY/DEEPSEEK_API_KEY env vars)
            criteria_path: Path to ranking criteria JSON file
            model_name: DeepSeek model to use (default: deepseek-v4-pro)
            max_retries: Maximum retry attempts for failed API calls

        Raises:
            FileNotFoundError: If criteria file not found
            ValueError: If API key not provided or found in environment
        """
        if not api_key:
            api_key = os.getenv("DS_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DeepSeek API key not found. Set DS_API_KEY or DEEPSEEK_API_KEY, "
                "or pass api_key parameter."
            )

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model_name = model_name
        self.max_retries = max_retries

        self.criteria_path = criteria_path
        self.ranking_criteria = self._load_criteria()

    def _load_criteria(self) -> Dict[str, Any]:
        """Load ranking criteria from JSON file."""
        try:
            with open(self.criteria_path, "r", encoding="utf-8") as f:
                criteria = json.load(f)
            return criteria
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Ranking criteria file not found: {self.criteria_path}\n"
                "Ensure the ranking criteria JSON exists in AIBot/data/."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in criteria file: {e}")

    def _build_prompt(
        self,
        title: str,
        abstract: str,
        tags: Optional[str] = None,
        lrd_index: Optional[int] = None,
    ) -> str:
        """Build the prompt for DeepSeek API with paper details and ranking criteria."""
        prompt_template = self.ranking_criteria.get("usage_instructions", {}).get(
            "prompt_template", ""
        )

        if lrd_index is not None and "{lrdIndex}" in prompt_template:
            prompt_template = prompt_template.replace("{lrdIndex}", str(lrd_index))

        paper_details = f"""**Paper Title:** {title}

**Abstract:** {abstract}"""

        if tags:
            paper_details += f"\n\n**Existing Tags:** {tags}"

        if lrd_index is not None:
            paper_details += f"\n\n**LRD Community Citation Count (lrdIndex):** {lrd_index}"

        return f"""{prompt_template}

**Paper to Evaluate:**

{paper_details}

**Evaluation:**
Provide your scoring assessment following the JSON structure specified above."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse DeepSeek API response and extract JSON."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            if "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)

            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)

        raise DeepSeekRankingError(
            f"Failed to parse JSON from DeepSeek response:\n{response_text[:500]}..."
        )

    def rank_paper(
        self, title: str, abstract: str, tags: Optional[str] = None, lrd_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Rank a single paper's relevance to LRD research."""
        prompt = self._build_prompt(title, abstract, tags, lrd_index)

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert astrophysics reviewer specializing in "
                                "high-redshift galaxy evolution and Little Red Dot (LRD) "
                                "research. You are thorough, objective, and "
                                "domain-knowledgeable. Always return valid JSON responses."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    top_p=0.9,
                )

                response_text = response.choices[0].message.content or ""
                result = self._parse_response(response_text)

                if "final_score" not in result:
                    raise DeepSeekRankingError("Response missing 'final_score' field")

                return result

            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"  ⚠ JSON parse error, retrying in {wait_time}s... "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    raise DeepSeekRankingError(
                        f"Failed to parse response after {self.max_retries} attempts: {e}"
                    )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"  ⚠ API error: {e}, retrying in {wait_time}s... "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    raise DeepSeekRankingError(
                        f"Failed to rank paper after {self.max_retries} attempts: {e}"
                    )

        raise DeepSeekRankingError("Unexpected error in ranking logic")
