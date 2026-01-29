import os
import re
import requests
from pybtex.database import parse_string, BibliographyData

# Only load environment variables from .env when running locally (skip in GitHub Actions)
if not os.getenv("GITHUB_ACTIONS"):
    from dotenv import load_dotenv

    load_dotenv()


def add_dimensions_altmetric(bib_database):
    """
    Add dimensions and altmetric fields to entries that are missing them
    """
    updated_count = 0

    for key, entry in bib_database.entries.items():
        # Add dimensions field if missing
        if "dimensions" not in entry.fields:
            entry.fields["dimensions"] = "true"
            updated_count += 1

        # Add altmetric field if missing and DOI is available
        if "altmetric" not in entry.fields and "doi" in entry.fields:
            try:
                # Build Altmetric API URL
                altmetric_api_url = f"https://api.altmetric.com/v1/doi/{entry.fields['doi']}"
                altmetric_response = requests.get(altmetric_api_url)

                # Check response status
                if altmetric_response.status_code == 200:
                    altmetric_data = altmetric_response.json()
                    if "altmetric_id" in altmetric_data:
                        entry.fields["altmetric"] = str(altmetric_data["altmetric_id"])
                        print(f"  Added Altmetric ID: {altmetric_data['altmetric_id']} for {key}")
                        updated_count += 1
                else:
                    print(f"  Cannot get Altmetric data for {key}, status code: {altmetric_response.status_code}")
            except Exception as e:
                print(f"  Error getting Altmetric data for {key}: {e}")

    return updated_count


def fix_back_slashes(text):
    """
    Fix repeated backslashes in BibTeX strings
    This prevents the accumulation of escape characters when reading and writing files
    """
    # Replace multiple backslashes with a single backslash
    # (this catches cases where previous runs have already stacked backslashes)
    text = re.sub(r"\\{2,}", r"\\", text)

    return text


def search_ads(query, token, output_article, output_proposal):
    """
    Search the NASA ADS API for papers matching the query and save bibtex to separate files:
    - Articles go to output_article
    - Proposals (MISC entries with jwst.prop in bibcode) go to output_proposal
    """
    base_url = "https://api.adsabs.harvard.edu/v1"
    headers = {"Authorization": f"Bearer {token}"}

    # First search for papers with the query in title OR abstract
    search_url = f"{base_url}/search/query"
    search_params = {"q": f'title:"{query}" OR abs:"{query}"', "fl": "bibcode", "rows": 1000, "sort": "date desc"}

    print(f"Searching for papers with '{query}' in title or abstract...")
    response = requests.get(search_url, headers=headers, params=search_params)

    if response.status_code != 200:
        print(f"Error searching ADS: {response.status_code}")
        print(response.text)
        return False

    data = response.json()
    bibcodes = [doc["bibcode"] for doc in data.get("response", {}).get("docs", [])]

    if not bibcodes:
        print("No papers found.")
        return False

    print(f"Found {len(bibcodes)} papers.")

    # Export to BibTeX with abstracts
    export_url = f"{base_url}/export/bibtexabs"
    export_data = {
        "bibcode": bibcodes,
        "sort": "date desc",
        "format": "bibtex",
        "maxauthor": 0,  # Include all authors
        "keyformat": "%R",  # Use bibcode as key
    }

    print("Retrieving BibTeX entries with abstracts...")
    response = requests.post(export_url, headers=headers, json=export_data)

    if response.status_code != 200:
        print(f"Error exporting BibTeX: {response.status_code}")
        print(response.text)
        return False

    bibtex_data = response.json().get("export", "")

    # Parse the retrieved BibTeX data
    try:
        new_bib_database = parse_string(bibtex_data, "bibtex")
    except Exception as e:
        print(f"Error parsing BibTeX data: {e}")
        return False

    # Load existing databases if they exist
    existing_article_bib = BibliographyData()
    existing_proposal_bib = BibliographyData()

    if os.path.exists(output_article):
        try:
            with open(output_article, "r", encoding="utf-8") as f:
                content = f.read()
                # Fix backslashes before parsing to prevent accumulation
                content = fix_back_slashes(content)
                existing_article_bib = parse_string(content, "bibtex")
            print(f"Loaded {len(existing_article_bib.entries)} existing article entries")
        except Exception as e:
            print(f"Warning: Could not read existing article entries: {e}")

    if os.path.exists(output_proposal):
        try:
            with open(output_proposal, "r", encoding="utf-8") as f:
                content = f.read()
                # Fix backslashes before parsing to prevent accumulation
                content = fix_back_slashes(content)
                existing_proposal_bib = parse_string(content, "bibtex")
            print(f"Loaded {len(existing_proposal_bib.entries)} existing proposal entries")
        except Exception as e:
            print(f"Warning: Could not read existing proposal entries: {e}")

    # Create new databases for articles and proposals
    article_bib = BibliographyData()
    proposal_bib = BibliographyData()

    # Classify entries and add new ones
    new_article_count = 0
    new_proposal_count = 0

    # Keep track of current bibcodes in search results
    current_article_keys = set()
    current_proposal_keys = set()

    for key, entry in new_bib_database.entries.items():
        # Check if it's a proposal (MISC with jwst.prop in key)
        if ("jwst.prop" in key) or (entry.type == "misc" and ".prop." in key):
            current_proposal_keys.add(key)
            if key not in existing_proposal_bib.entries:
                proposal_bib.add_entry(key, entry)
                new_proposal_count += 1
        # Check if it's an article
        elif entry.type == "article":
            current_article_keys.add(key)
            if key not in existing_article_bib.entries:
                article_bib.add_entry(key, entry)
                new_article_count += 1

    # Remove entries that are no longer in search results
    removed_article_count = 0
    removed_proposal_count = 0

    # Create new databases for updated content
    updated_article_bib = BibliographyData()
    updated_proposal_bib = BibliographyData()

    # Process article entries
    for key, entry in existing_article_bib.entries.items():
        if key in current_article_keys:
            # Keep entries that are still in search results
            updated_article_bib.add_entry(key, entry)
        else:
            removed_article_count += 1
            print(f"Removing article entry: {key}")

    # Process proposal entries
    for key, entry in existing_proposal_bib.entries.items():
        if key in current_proposal_keys:
            # Keep entries that are still in search results
            updated_proposal_bib.add_entry(key, entry)
        else:
            removed_proposal_count += 1
            print(f"Removing proposal entry: {key}")

    # Add new entries to updated databases
    for key, entry in article_bib.entries.items():
        updated_article_bib.add_entry(key, entry)

    for key, entry in proposal_bib.entries.items():
        updated_proposal_bib.add_entry(key, entry)

    # Add dimensions and altmetric fields
    print("Adding dimensions and altmetric fields to articles...")
    article_fields_added = add_dimensions_altmetric(updated_article_bib)

    print("Adding dimensions and altmetric fields to proposals...")
    proposal_fields_added = add_dimensions_altmetric(updated_proposal_bib)

    # Update existing databases with new entries
    article_success = True
    proposal_success = True

    # Save the updated article database
    try:
        # Write processed BibTeX back to file
        with open(output_article, "w", encoding="utf-8") as f:
            # Generate BibTeX string
            bibtex_str = updated_article_bib.to_string("bibtex")

            # Fix backslashes to prevent duplication
            bibtex_str = fix_back_slashes(bibtex_str)

            # Use regex to replace double quotes with braces, preserving title field formatting
            bibtex_str = re.sub(r'(\w+) = "(?!\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)
            bibtex_str = re.sub(r'(\w+) = "(?=\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)

            f.write(bibtex_str)
        print(f"Added {new_article_count} new article entries to {output_article}")
        print(f"Removed {removed_article_count} outdated article entries")
        print(f"Added/updated fields in {article_fields_added} article entries")
    except Exception as e:
        print(f"Error writing article entries: {e}")
        article_success = False

    # Save the updated proposal database
    try:
        # Write processed BibTeX back to file
        with open(output_proposal, "w", encoding="utf-8") as f:
            # Generate BibTeX string
            bibtex_str = updated_proposal_bib.to_string("bibtex")

            # Fix backslashes to prevent duplication
            bibtex_str = fix_back_slashes(bibtex_str)

            # Use regex to replace double quotes with braces, preserving title field formatting
            bibtex_str = re.sub(r'(\w+) = "(?!\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)
            bibtex_str = re.sub(r'(\w+) = "(?=\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)

            f.write(bibtex_str)
        print(f"Added {new_proposal_count} new proposal entries to {output_proposal}")
        print(f"Removed {removed_proposal_count} outdated proposal entries")
        print(f"Added/updated fields in {proposal_fields_added} proposal entries")
    except Exception as e:
        print(f"Error writing proposal entries: {e}")
        proposal_success = False

    return article_success and proposal_success


if __name__ == "__main__":
    # Get API token from environment variable
    ads_token = os.environ.get("ADS_TOKEN")

    if not ads_token:
        print("Error: ADS_TOKEN environment variable not set")
        exit(1)

    # Set the search query and output file
    query = "Little Red Dots"
    output_article = "./aslrd.bib"
    output_proposal = "./aslrd_prop.bib"

    # Search ADS and save BibTeX
    success = search_ads(query, ads_token, output_article, output_proposal)

    if not success:
        exit(1)
