import os
import re
import sys
import requests
from pybtex.database import parse_file, BibliographyData, parse_string

# Only load environment variables from .env when running locally (skip in GitHub Actions)
if not os.getenv("GITHUB_ACTIONS"):
    from dotenv import load_dotenv

    load_dotenv()


def fix_back_slashes(text):
    """
    Fix repeated backslashes in BibTeX strings
    This prevents the accumulation of escape characters when reading and writing files
    """
    # Replace multiple backslashes with a single backslash
    # (this catches cases where previous runs have already stacked backslashes)
    text = re.sub(r"\\{2,}", r"\\", text)
    return text


def has_eprint_field(entry):
    """
    Check if a BibTeX entry has an eprint field
    """
    fields = {k.lower(): v for k, v in entry.fields.items()}
    return "eprint" in fields


def get_updated_bibtex_entry(bibcode, token):
    """
    Get updated BibTeX entry for a specific bibcode from ADS
    """
    base_url = "https://api.adsabs.harvard.edu/v1/export/bibtexabs"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "bibcode": [bibcode],
        "sort": "date desc",
        "format": "bibtex",
        "maxauthor": 0,  # Include all authors
        "keyformat": "%R",  # Use bibcode as key
    }

    print(f"  Retrieving updated BibTeX entry for {bibcode}...")
    response = requests.post(base_url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"  Error exporting BibTeX for {bibcode}: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

    bibtex_data = response.json().get("export", "")

    if not bibtex_data.strip():
        print(f"  No BibTeX data returned for {bibcode}")
        return None

    try:
        # Parse the retrieved BibTeX data
        updated_bib = parse_string(bibtex_data, "bibtex")
        if bibcode in updated_bib.entries:
            return updated_bib.entries[bibcode]
        else:
            print(f"  Warning: Expected bibcode {bibcode} not found in returned data")
            return None
    except Exception as e:
        print(f"  Error parsing BibTeX data for {bibcode}: {e}")
        return None


def update_entry_with_eprint(original_entry, updated_entry):
    """
    Update the original entry with eprint and archivePrefix fields from the updated entry
    Returns True if any fields were added
    """
    updated = False

    # Check for eprint field in updated entry
    updated_fields = {k.lower(): k for k, v in updated_entry.fields.items()}

    if "eprint" in updated_fields and "eprint" not in {k.lower() for k in original_entry.fields.keys()}:
        eprint_key = updated_fields["eprint"]
        original_entry.fields["eprint"] = updated_entry.fields[eprint_key]
        print(f"    Added eprint: {updated_entry.fields[eprint_key]}")
        updated = True

    if "archiveprefix" in updated_fields and "archiveprefix" not in {k.lower() for k in original_entry.fields.keys()}:
        archiveprefix_key = updated_fields["archiveprefix"]
        original_entry.fields["archivePrefix"] = updated_entry.fields[archiveprefix_key]
        print(f"    Added archivePrefix: {updated_entry.fields[archiveprefix_key]}")
        updated = True

    if "primaryclass" in updated_fields and "primaryclass" not in {k.lower() for k in original_entry.fields.keys()}:
        primaryclass_key = updated_fields["primaryclass"]
        original_entry.fields["primaryClass"] = updated_entry.fields[primaryclass_key]
        print(f"    Added primaryClass: {updated_entry.fields[primaryclass_key]}")
        updated = True

    return updated


def save_bibtex(bib_data, output_path):
    """
    Save BibTeX data to a file using BibTeX format
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            # Generate BibTeX string
            bibtex_str = bib_data.to_string("bibtex")

            # Fix backslashes to prevent duplication
            bibtex_str = fix_back_slashes(bibtex_str)

            # Use regex to replace double quotes with braces, preserving title field formatting
            bibtex_str = re.sub(r'(\w+) = "(?!\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)
            bibtex_str = re.sub(r'(\w+) = "(?=\{)(.*?)(?!\})"(,|\n)', r"\1 = {\2}\3", bibtex_str)

            f.write(bibtex_str)
        print(f"Successfully saved updated BibTeX data to {output_path}")
        return True
    except Exception as e:
        print(f"Error writing BibTeX file to {output_path}: {e}")
        return False


def main(input_bib_file, output_bib_file=None):
    """
    Main function to check and update eprint fields in BibTeX entries
    """
    # Get API token from environment variable
    ads_token = os.environ.get("ADS_TOKEN")

    if not ads_token:
        print("Error: ADS_TOKEN environment variable not set")
        print("Please set your ADS API token: export ADS_TOKEN='your_token_here'")
        sys.exit(1)

    # Set output file name
    if output_bib_file is None:
        base_name = os.path.splitext(input_bib_file)[0]
        output_bib_file = f"{base_name}_updated.bib"

    # Load the input BibTeX file
    try:
        print(f"Loading BibTeX file: {input_bib_file}")
        bib_data = parse_file(input_bib_file, bib_format="bibtex")
        print(f"Loaded {len(bib_data.entries)} entries")
    except FileNotFoundError:
        print(f"Error: BibTeX file not found: {input_bib_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing BibTeX file {input_bib_file}: {e}")
        sys.exit(1)

    # Check each entry for missing eprint field
    entries_without_eprint = []
    entries_with_eprint = 0

    for key, entry in bib_data.entries.items():
        if has_eprint_field(entry):
            entries_with_eprint += 1
        else:
            entries_without_eprint.append((key, entry))

    print(f"\nFound {entries_with_eprint} entries with eprint field")
    print(f"Found {len(entries_without_eprint)} entries without eprint field")

    if not entries_without_eprint:
        print("All entries already have eprint fields. No updates needed.")
        return

    # Update entries without eprint field
    updated_count = 0
    failed_count = 0

    print(f"\nUpdating entries without eprint field...")

    for i, (key, entry) in enumerate(entries_without_eprint, 1):
        print(f"\n[{i}/{len(entries_without_eprint)}] Processing {key}")

        # Get updated entry from ADS
        updated_entry = get_updated_bibtex_entry(key, ads_token)

        if updated_entry is None:
            print(f"  Failed to retrieve updated entry for {key}")
            failed_count += 1
            continue

        # Check if updated entry has eprint field
        if not has_eprint_field(updated_entry):
            print(f"  Updated entry for {key} still doesn't have eprint field")
            failed_count += 1
            continue

        # Update the original entry with eprint information
        if update_entry_with_eprint(entry, updated_entry):
            updated_count += 1
            print(f"  Successfully updated {key}")
        else:
            print(f"  No new fields added to {key}")
            failed_count += 1

    # Save the updated BibTeX file
    print(f"\nSummary:")
    print(f"  Total entries processed: {len(entries_without_eprint)}")
    print(f"  Successfully updated: {updated_count}")
    print(f"  Failed to update: {failed_count}")

    if updated_count > 0:
        print(f"\nSaving updated entries to: {output_bib_file}")
        if save_bibtex(bib_data, output_bib_file):
            print(f"Successfully saved {len(bib_data.entries)} entries to {output_bib_file}")
        else:
            print(f"Failed to save updated entries")
            sys.exit(1)
    else:
        print("No entries were updated, so no new file was created.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_eprint.py <input_bib_file> [output_bib_file]")
        print("")
        print("This script checks all entries in a BibTeX file for missing eprint fields")
        print("and updates them using the ADS API.")
        print("")
        print("Arguments:")
        print("  input_bib_file   : Path to the input BibTeX file")
        print("  output_bib_file  : Path to the output BibTeX file (optional)")
        print("                     If not provided, will use <input_name>_updated.bib")
        print("")
        print("Environment variables:")
        print("  ADS_TOKEN        : Your ADS API token (required)")
        print("")
        print("Example:")
        print("  python update_eprint.py aslrd.bib aslrd_with_eprint.bib")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    main(input_file, output_file)
