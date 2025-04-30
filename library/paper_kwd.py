import os
import sys
import yaml
import requests
import logging
from pybtex.database import parse_file, BibliographyData, Entry
from pybtex.database.output.bibtex import Writer
import time  # Add time for retry delay
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Constants ---
MAX_RETRIES = 3
ALIYUN_API_KEY_ENV_VAR = "ALIYUN_API_KEY"
QWEN_MAX_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


def load_tags(yaml_path: str) -> dict | None:
    """Loads tags and descriptions from a YAML file."""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            tags_data = yaml.safe_load(f)
            # Basic validation
            if isinstance(tags_data, dict) and "tags" in tags_data and isinstance(tags_data["tags"], list):
                logging.info(f"Successfully loaded {len(tags_data['tags'])} tags from {yaml_path}")
                return tags_data
            else:
                logging.error(f"Invalid format in YAML file: {yaml_path}. Expected a dict with a 'tags' list.")
                return None
    except FileNotFoundError:
        logging.error(f"Error: YAML file not found at {yaml_path}")
        return None
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {yaml_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading {yaml_path}: {e}")
        return None


def load_bibtex(bib_path: str) -> BibliographyData | None:
    """Loads BibTeX data from a file."""
    try:
        bib_data = parse_file(bib_path, bib_format="bibtex")
        logging.info(f"Successfully loaded {len(bib_data.entries)} entries from {bib_path}")
        return bib_data
    except FileNotFoundError:
        logging.error(f"Error: BibTeX file not found at {bib_path}")
        return None
    except Exception as e:  # Catch other potential parsing errors from pybtex
        logging.error(f"Error parsing BibTeX file {bib_path}: {e}")
        return None


def save_bibtex(bib_data: BibliographyData, output_path: str) -> None:
    """Saves BibTeX data to a file using BibTeX format."""
    writer = Writer()
    # Customize writer settings if needed, e.g., for encoding
    # writer.encoding = 'utf8'
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            writer.write_file(bib_data, f)
        logging.info(f"BibTeX data successfully saved to {output_path}")
    except IOError as e:
        logging.error(f"Error writing BibTeX file to {output_path}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving {output_path}: {e}")


def call_qwen_max(prompt: str, api_key: str) -> str | None:
    """Calls the Aliyun Qwen-max API and returns the text response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-max",
        "input": {"prompt": prompt},
        "parameters": {
            "result_format": "text"  # Request plain text output
            # Add other parameters like temperature, max_tokens if needed
            # "temperature": 0.8,
            # "max_tokens": 100,
        },
    }

    try:
        response = requests.post(QWEN_MAX_ENDPOINT, headers=headers, json=payload, timeout=60)  # 60 second timeout
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        result = response.json()

        # Check response structure based on Aliyun Dashscope documentation
        if result.get("output") and result["output"].get("text"):
            text_output = result["output"]["text"].strip()
            logging.debug(f"Qwen-max raw response: {text_output}")
            return text_output
        else:
            logging.error(f"Error: Unexpected response format from Qwen-max API: {result}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling Qwen-max API: {e}")
        # Log specific status code if available
        if isinstance(e, requests.exceptions.HTTPError):
            logging.error(f"API Response Status Code: {e.response.status_code}")
            logging.error(f"API Response Body: {e.response.text}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during API call: {e}")
        return None


def generate_keywords_for_entry(entry: Entry, tags_data: dict, api_key: str) -> list[str] | None:
    """Generates keywords for a single BibTeX entry using the AI model with retry logic."""
    title = entry.fields.get("title", "[No Title]")
    abstract = entry.fields.get("abstract", "[No Abstract]")

    # Format tags for the prompt
    tag_descriptions = "\n".join([f"- {t['tag']}: {t['description']}" for t in tags_data.get("tags", [])])

    prompt = f"""
    Based on the following research paper title and abstract, please select up to 5 relevant keywords from the provided list. The keywords should best describe the main topics of the paper.

    **Title:** {title}

    **Abstract:** {abstract}

    **Available Keywords (choose up to 5):**
    {tag_descriptions}

    **Instructions:**
    Return ONLY a comma-separated list of the chosen keywords (maximum 5). For example: 'agn, jwst, emission lines'
    Do not include any other text, explanations, or formatting.
    """

    logging.debug(f"Generated prompt for entry '{entry.key}':\n{prompt[:500]}...")  # Log beginning of prompt

    for attempt in range(MAX_RETRIES):
        logging.info(f"Attempt {attempt + 1}/{MAX_RETRIES} to get keywords for entry '{entry.key}'")
        raw_response = call_qwen_max(prompt, api_key)

        if raw_response:
            # Basic validation: check if it's a non-empty string
            if isinstance(raw_response, str) and raw_response.strip():
                # Simple parsing: split by comma, strip whitespace
                keywords = [kw.strip().lower() for kw in raw_response.split(",") if kw.strip()]
                # Further validation could be added here, e.g., check against valid tags
                # but the main loop already handles final validation against the YAML tags
                if keywords:
                    logging.info(f"Successfully received keywords from AI for '{entry.key}': {keywords}")
                    return keywords  # Return the list of parsed keywords
                else:
                    logging.warning(f"AI returned an empty or invalid response for '{entry.key}': '{raw_response}'")
            else:
                logging.warning(f"AI returned an empty or invalid response for '{entry.key}': '{raw_response}'")
        else:
            logging.warning(f"API call failed for entry '{entry.key}' on attempt {attempt + 1}")

        # Wait before retrying
        if attempt < MAX_RETRIES - 1:
            wait_time = 2**attempt  # Exponential backoff (1, 2, 4 seconds...)
            logging.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)

    logging.error(f"Failed to get valid keywords for entry '{entry.key}' after {MAX_RETRIES} attempts.")
    return None


def main():
    """Main function to process the BibTeX file and add keywords."""
    # Define file paths (adjust if needed)
    bib_file_path = "./aslrd.bib"
    yaml_file_path = "./LRD Literature Tags.yml"
    output_bib_path = "./aslrd_updated.bib"  # Save to a new file initially

    # Get API Key
    api_key = os.getenv(ALIYUN_API_KEY_ENV_VAR)
    if not api_key:
        logging.error(f"Error: Environment variable {ALIYUN_API_KEY_ENV_VAR} not set.")
        sys.exit(1)

    # Load data
    tags_data = load_tags(yaml_file_path)
    if not tags_data:
        sys.exit(1)

    bib_data = load_bibtex(bib_file_path)
    if not bib_data:
        sys.exit(1)

    valid_tags = {tag_info["tag"] for tag_info in tags_data.get("tags", [])}
    if not valid_tags:
        logging.error(f"No valid tags found in {yaml_file_path}")
        sys.exit(1)

    updated_entries_count = 0
    entries_to_process = list(bib_data.entries.items())  # Create a list to iterate over

    for key, entry in entries_to_process:
        # Check if 'lrdKeys' field exists and is non-empty
        if "lrdkeys" in entry.fields and entry.fields["lrdkeys"].strip():
            logging.info(f"Entry '{key}' already has lrdKeys: {entry.fields['lrdkeys']}. Skipping.")
            continue

        logging.info(f"Processing entry: {key}")

        keywords = generate_keywords_for_entry(entry, tags_data, api_key)

        if keywords:
            # Filter keywords to ensure they are in the valid list (case-insensitive)
            valid_keywords_found = [kw for kw in keywords if kw.lower() in {vt.lower() for vt in valid_tags}]

            if valid_keywords_found:
                keywords_str = ", ".join(sorted(valid_keywords_found))  # Sort for consistency
                entry.fields["lrdKeys"] = keywords_str
                logging.info(f"Added keywords to entry '{key}': {keywords_str}")
                updated_entries_count += 1
            else:
                logging.warning(f"AI returned keywords for '{key}', but none matched the valid tags: {keywords}")
        else:
            logging.error(f"Failed to generate keywords for entry '{key}' after multiple retries.")
            # Decide if you want to exit here or continue with other entries
            # For now, we continue

    # Save the updated BibTeX data if any entries were modified
    if updated_entries_count > 0:
        logging.info(f"Saving updated BibTeX data to {output_bib_path}...")
        save_bibtex(bib_data, output_bib_path)
        logging.info(f"Successfully updated {updated_entries_count} entries.")
    else:
        logging.info("No entries were updated.")

    logging.info("Script finished.")


if __name__ == "__main__":
    main()
