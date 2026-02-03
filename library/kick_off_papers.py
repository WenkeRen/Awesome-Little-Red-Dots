import os
import re
import requests
from pybtex.database import parse_file, BibliographyData, parse_string
from collections import Counter

# Only load environment variables from .env when running locally (skip in GitHub Actions)
if not os.getenv("GITHUB_ACTIONS"):
    from dotenv import load_dotenv

    load_dotenv()

MIN_CITATIONS = 10


def search_references(bibcode, token):
    """
    Search for the references of a paper by its bibcode
    """
    base_url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {token}"}
    search_params = {"q": f"references(bibcode:{bibcode})", "fl": "bibcode", "rows": 500}

    print(f"Searching for references of {bibcode}...")
    response = requests.get(base_url, headers=headers, params=search_params)

    if response.status_code != 200:
        print(f"Error searching ADS: {response.status_code}")
        print(response.text)
        return []

    data = response.json()
    refs_bibcodes = [doc["bibcode"] for doc in data.get("response", {}).get("docs", [])]
    print(f"Found {len(refs_bibcodes)} references for {bibcode}")

    return refs_bibcodes


def get_bibtex_with_abstract(bibcodes, token):
    """
    Get BibTeX entries with abstracts for a list of bibcodes from ADS
    """
    base_url = "https://api.adsabs.harvard.edu/v1/export/bibtexabs"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "bibcode": bibcodes,
        "sort": "date desc",
        "format": "bibtex",
        "maxauthor": 0,  # Include all authors
        "keyformat": "%R",  # Use bibcode as key
    }

    print(f"Retrieving BibTeX entries with abstracts for {len(bibcodes)} papers...")
    response = requests.post(base_url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"Error exporting BibTeX: {response.status_code}")
        print(response.text)
        return ""

    bibtex_data = response.json().get("export", "")
    return bibtex_data


def fix_back_slashes(text):
    """
    Fix repeated backslashes in BibTeX strings
    This prevents the accumulation of escape characters when reading and writing files
    """
    # Replace multiple backslashes with a single backslash
    # (this catches cases where previous runs have already stacked backslashes)
    text = re.sub(r"\\{2,}", r"\\", text)
    return text


def check_publication_year(bibcode):
    """
    Check if a publication is from 2022 or later based on its bibcode
    """
    # Extract the year from the bibcode (positions 0-4)
    year_str = bibcode[:4]
    try:
        year = int(year_str)
        return year >= 2022
    except ValueError:
        return False


def check_is_article(bibcode, token):
    """
    Check if a bibcode is an article by querying ADS
    """
    base_url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {token}"}
    search_params = {"q": f"bibcode:{bibcode}", "fl": "bibcode,doctype", "rows": 1}

    response = requests.get(base_url, headers=headers, params=search_params)

    if response.status_code != 200:
        print(f"Error checking if {bibcode} is an article: {response.status_code}")
        return False

    data = response.json()
    docs = data.get("response", {}).get("docs", [])

    if not docs:
        return False

    doctype = docs[0].get("doctype", "")
    return doctype == "article"


def add_dimensions(bib_database):
    """
    Add dimensions field to entries that are missing them
    """
    updated_count = 0

    for key, entry in bib_database.entries.items():
        # Add dimensions field if missing
        if "dimensions" not in entry.fields:
            entry.fields["dimensions"] = "true"
            updated_count += 1

    return updated_count


def add_lrd_index(bib_database, reference_counts):
    """
    Add lrdIndex field with the number of citations to each entry
    """
    updated_count = 0

    for key, entry in bib_database.entries.items():
        # Add or update lrdIndex field with the number of citations
        if key in reference_counts:
            entry.fields["lrdIndex"] = str(reference_counts[key])
            updated_count += 1
            print(f"  Added/Updated lrdIndex: {reference_counts[key]} for {key}")

    return updated_count


def main():
    # Get API token from environment variable
    ads_token = os.environ.get("ADS_TOKEN")

    if not ads_token:
        print("Error: ADS_TOKEN environment variable not set")
        exit(1)

    # Path to the bibtex files
    input_bib_file = "./aslrd.bib"
    output_bib_file = "./kick_off.bib"

    # Parse the input BibTeX file
    try:
        bib_database = parse_file(input_bib_file)
        print(f"Loaded {len(bib_database.entries)} entries from {input_bib_file}")
    except Exception as e:
        print(f"Error reading {input_bib_file}: {e}")
        exit(1)

    # Load existing entries from output BibTeX file if it exists
    existing_output_entries = BibliographyData()
    if os.path.exists(output_bib_file):
        try:
            existing_output_entries = parse_file(output_bib_file)
            print(f"Loaded {len(existing_output_entries.entries)} existing entries from {output_bib_file}")
        except Exception as e:
            print(f"Error reading existing {output_bib_file}: {e}")
            print("Will create a new file.")

    # Get the set of bibcodes in our database
    existing_bibcodes = set(bib_database.entries.keys())
    existing_output_bibcodes = set(existing_output_entries.entries.keys())
    print(f"Found {len(existing_bibcodes)} existing bibcodes in aslrd.bib")
    print(f"Found {len(existing_output_bibcodes)} existing bibcodes in kick_off.bib")

    # Dictionary to store all referenced papers
    all_references = []

    # For each entry in the BibTeX file
    for key, entry in bib_database.entries.items():
        # Get the bibcode, which is the key in our case
        bibcode = key

        # Search for references of this paper
        refs = search_references(bibcode, ads_token)

        # Add to our collection
        all_references.extend(refs)

    # Count occurrences of each reference
    reference_counts = Counter(all_references)

    # Remove references that are in aslrd.bib (but keep ones that are in kick_off.bib)
    for bibcode in existing_bibcodes:
        if bibcode in reference_counts:
            del reference_counts[bibcode]

    print(f"Excluded {len(existing_bibcodes)} existing bibcodes from aslrd.bib from results")

    # Sort by count (descending)
    sorted_references = sorted(reference_counts.items(), key=lambda x: x[1], reverse=True)

    # Print the sorted references
    print("\nReference counts (sorted by most cited, excluding existing entries in aslrd.bib):")
    for bibcode, count in sorted_references:
        print(f"{bibcode}: {count}")

    # Total unique references
    print(f"\nTotal unique references (excluding existing entries in aslrd.bib): {len(reference_counts)}")
    print(f"Total citations (excluding existing entries in aslrd.bib): {sum(reference_counts.values())}")

    # Keep track of current references (for cleaning up outdated entries later)
    current_references = set(reference_counts.keys())

    # Filter references to keep only those with count > 10 and published in 2022 or later
    interesting_refs = []
    interesting_counts = {}
    print("\nChecking publication type and year for frequently cited papers...")

    for bibcode, count in sorted_references:
        if count >= MIN_CITATIONS:
            # Skip if it's already in aslrd.bib
            if bibcode in existing_bibcodes:
                continue

            # Check if it's an article published in 2022 or later
            recent = check_publication_year(bibcode)
            if recent:
                is_article = check_is_article(bibcode, ads_token)
                if is_article:
                    # Include in our list of interesting references
                    if bibcode not in existing_output_bibcodes:
                        interesting_refs.append(bibcode)
                    interesting_counts[bibcode] = count
                    print(f"Keeping {bibcode} (count: {count}, recent article)")
                else:
                    print(f"Skipping {bibcode} (count: {count}, recent but not an article)")
            else:
                print(f"Skipping {bibcode} (count: {count}, not recent)")

    # Check for entries in kick_off.bib that are no longer in the current references
    outdated_entries = []
    for bibcode in existing_output_bibcodes:
        if bibcode not in current_references:
            outdated_entries.append(bibcode)

    if outdated_entries:
        print(f"\nFound {len(outdated_entries)} entries in kick_off.bib that are no longer listed:")
        for bibcode in outdated_entries:
            print(f"  {bibcode}")

    # Only proceed if we have new references to add or entries to update
    if interesting_refs or interesting_counts or outdated_entries:
        # Create a new database for the updated entries
        updated_database = BibliographyData()

        # First add existing entries that are still referenced
        for key, entry in existing_output_entries.entries.items():
            if key not in outdated_entries:
                updated_database.add_entry(key, entry)

        # Get BibTeX with abstracts only for completely new entries
        if interesting_refs:
            bibtex_data = get_bibtex_with_abstract(interesting_refs, ads_token)

            if bibtex_data:
                try:
                    # Parse the retrieved BibTeX data
                    new_entries = parse_string(bibtex_data, "bibtex")

                    # Add new entries to the updated database
                    for key, entry in new_entries.entries.items():
                        updated_database.add_entry(key, entry)
                except Exception as e:
                    print(f"Error parsing new BibTeX data: {e}")
            else:
                print("Failed to retrieve BibTeX data for new references")

        # Add dimensions field and update lrdIndex for all entries
        if len(updated_database.entries) > 0:
            # Add dimensions field to all entries
            print("\nAdding dimensions field...")
            added_fields = add_dimensions(updated_database)
            print(f"Added/updated dimensions in {added_fields} entries")

            # Add lrdIndex field with citation counts to all entries
            print("\nAdding lrdIndex field with citation counts...")
            added_indices = add_lrd_index(updated_database, reference_counts)
            print(f"Added/updated lrdIndex in {added_indices} entries")

            # Generate BibTeX string
            updated_bibtex = updated_database.to_string("bibtex")

            # Fix backslashes
            updated_bibtex = fix_back_slashes(updated_bibtex)

            # Use regex to replace double quotes with braces, preserving title field formatting
            updated_bibtex = re.sub(r'(\w+) = "(?!\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", updated_bibtex)
            updated_bibtex = re.sub(r'(\w+) = "(?=\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", updated_bibtex)

            # Save to output file
            with open(output_bib_file, "w", encoding="utf-8") as f:
                f.write(updated_bibtex)

            # Print summary
            entries_added = len(interesting_refs)
            entries_updated = len(interesting_counts) - entries_added
            entries_removed = len(outdated_entries)
            print(f"\nSaved {len(updated_database.entries)} entries to {output_bib_file}")
            print(f"  Added: {entries_added} new entries")
            print(f"  Updated: {entries_updated} existing entries")
            print(f"  Removed: {entries_removed} outdated entries")
        else:
            print("\nNo entries to save after processing")
    else:
        print("\nNo new entries to add or update")


if __name__ == "__main__":
    main()
