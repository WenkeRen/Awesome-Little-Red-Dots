import os
import re
import requests
from pybtex.database import parse_string, BibliographyData


def search_ads(query, token, output_article, output_proposal):
    """
    Search the NASA ADS API for papers matching the query and save bibtex to separate files:
    - Articles go to output_article
    - Proposals (MISC entries with jwst.prop in bibcode) go to output_proposal
    """
    base_url = "https://api.adsabs.harvard.edu/v1"
    headers = {"Authorization": f"Bearer {token}"}

    # First search for papers with the query in abstract
    search_url = f"{base_url}/search/query"
    search_params = {"q": f'abs:"{query}"', "fl": "bibcode", "rows": 200, "sort": "date desc"}

    print(f"Searching for papers with '{query}' in abstract...")
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
                existing_article_bib = parse_string(f.read(), "bibtex")
            print(f"Loaded {len(existing_article_bib.entries)} existing article entries")
        except Exception as e:
            print(f"Warning: Could not read existing article entries: {e}")

    if os.path.exists(output_proposal):
        try:
            with open(output_proposal, "r", encoding="utf-8") as f:
                existing_proposal_bib = parse_string(f.read(), "bibtex")
            print(f"Loaded {len(existing_proposal_bib.entries)} existing proposal entries")
        except Exception as e:
            print(f"Warning: Could not read existing proposal entries: {e}")

    # Create new databases for articles and proposals
    article_bib = BibliographyData()
    proposal_bib = BibliographyData()

    # Classify entries and add new ones
    new_article_count = 0
    new_proposal_count = 0

    for key, entry in new_bib_database.entries.items():
        # Check if it's a proposal (MISC with jwst.prop in key)
        if ("jwst.prop" in key) or (entry.type == "misc" and ".prop." in key):
            if key not in existing_proposal_bib.entries:
                proposal_bib.add_entry(key, entry)
                new_proposal_count += 1
        # Check if it's an article
        elif entry.type == "article":
            if key not in existing_article_bib.entries:
                article_bib.add_entry(key, entry)
                new_article_count += 1

    # Update existing databases with new entries
    article_success = True
    proposal_success = True

    if new_article_count > 0:
        # Merge with existing entries
        for key, entry in article_bib.entries.items():
            existing_article_bib.add_entry(key, entry)

        try:
            # Write processed BibTeX back to file
            with open(output_article, "w", encoding="utf-8") as f:
                # Generate BibTeX string
                bibtex_str = existing_article_bib.to_string("bibtex")

                # Use regex to replace double quotes with braces, preserving title field formatting
                bibtex_str = re.sub(r'(\w+) = "(?!\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)
                bibtex_str = re.sub(r'(\w+) = "(?=\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)

                f.write(bibtex_str)
            print(f"Added {new_article_count} new article entries to {output_article}")
        except Exception as e:
            print(f"Error writing article entries: {e}")
            article_success = False
    else:
        print("No new article entries found.")

    if new_proposal_count > 0:
        # Merge with existing entries
        for key, entry in proposal_bib.entries.items():
            existing_proposal_bib.add_entry(key, entry)

        try:
            # Write processed BibTeX back to file
            with open(output_proposal, "w", encoding="utf-8") as f:
                # Generate BibTeX string
                bibtex_str = existing_proposal_bib.to_string("bibtex")

                # Use regex to replace double quotes with braces, preserving title field formatting
                bibtex_str = re.sub(r'(\w+) = "(?!\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)
                bibtex_str = re.sub(r'(\w+) = "(?=\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)

                f.write(bibtex_str)
            print(f"Added {new_proposal_count} new proposal entries to {output_proposal}")
        except Exception as e:
            print(f"Error writing proposal entries: {e}")
            proposal_success = False
    else:
        print("No new proposal entries found.")

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
