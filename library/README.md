# ADS Bibliography for Little Red Dots

This directory contains scripts and bibliography files related to papers about "Little Red Dots".

## Usage

### lrd_ads_request.py

This script searches the NASA ADS API for papers containing "Little Red Dots" in their abstracts and exports the results as BibTeX entries to separate files:
- `aslrd.bib`: Contains only ARTICLE entries
- `aslrd_prop.bib`: Contains MISC entries related to proposals (with `jwst.prop` in their bibcode)

Requirements:
- Python 3
- `requests` library
- `pybtex` library
- `python-dotenv` library

To use:

1. Set your ADS API token as an environment variable:
   ```
   export ADS_TOKEN="your_ads_api_token"
   ```
   
   Or create a `.env` file in the same directory with:
   ```
   ADS_TOKEN=your_ads_api_token
   ```

2. Run the script:
   ```
   ./lrd_ads_request.py
   ```

The script will:
1. Search for papers with "Little Red Dots" in their abstracts
2. Export all matching papers as BibTeX entries with abstracts included
3. Parse and manage BibTeX entries using the pybtex library
4. Remove outdated entries (entries in the existing file but no longer in search results)
5. Add/update dimensions and altmetric fields for entries with DOIs
6. Check for existing entries to avoid duplicates (using BibTeX keys as identifiers)
7. Separate articles and proposals into different files
8. Format and save the updated entries to `aslrd.bib` and `aslrd_prop.bib`

## Files

- `aslrd.bib`: BibTeX database containing ARTICLE entries with "Little Red Dots" in their abstracts
- `aslrd_prop.bib`: BibTeX database containing proposal entries (MISC with jwst.prop in bibcode)
- `lrd_ads_request.py`: Script to update the BibTeX databases

## GitHub Actions

This script runs daily via GitHub Actions at 6:00 AM UTC by setting the `ADS_TOKEN` as a repository secret and running the script as part of a workflow. 