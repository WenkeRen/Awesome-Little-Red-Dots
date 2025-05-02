# Webpage Scripts

This directory contains utility scripts for maintaining the Awesome Little Red Dots bibliography website.

## Scripts

- `update_tags.rb` - Validates tag usage between the YAML definitions and the BibTeX entries
  - Shows defined tags from `_data/lrd_tags.yml`
  - Shows tags used in BibTeX entries
  - Highlights any inconsistencies (tags used but not defined)

## Usage

From the `webpage` directory, run:

```bash
ruby scripts/update_tags.rb
```

## Dependencies

The scripts require the following Ruby gems:

```
gem install bibtex-ruby colorize
```
