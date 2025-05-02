# Tag Filtering System Documentation

## Overview

The tag filtering system for the Awesome Little Red Dots bibliography allows users to filter papers based on predefined tags that describe the content and focus of each paper. This document explains how the tag system is implemented.

## Tag Data Management

Tags are stored in a YAML data file:

- Location: `_data/lrd_tags.yml`
- Format: A structured YAML file containing tag names and descriptions

### Sample Tag Data Structure

```yaml
tags:
  - tag: case study
    description: Provides an in-depth analysis of one or a few specific LRD sources.
  - tag: catalog
    description: Presents a list or table of LRD sources, candidates, or related objects with measured/derived properties.
  # ... more tags
```

## How It Works

1. **Loading Tags**:
   - Tags are defined in `_data/lrd_tags.yml`
   - The `_includes/tag_list.html` template generates the necessary HTML structure
   - Jekyll injects these tags into the page during site building

2. **Rendering Tags**:
   - On the main bibliography page (`index.md`), we include the tag list using `{% include tag_list.html %}`
   - This dynamically generates the tag list from the YAML data

3. **JavaScript Processing**:
   - The `tag-filter.js` script scans the generated HTML for tags
   - It creates UI controls for filtering papers based on tags
   - When a user selects tags, JavaScript filters the bibliography accordingly

## Adding or Modifying Tags

To add or modify tags:

1. Edit the `_data/lrd_tags.yml` file
2. Follow the established format (tag name and description)
3. Rebuild the site to see changes
4. Ensure papers are properly tagged with the corresponding tags in the bibtex file

## Tag Usage in BibTeX

To tag papers in the bibliography, add the `lrdKeys` field to the BibTeX entry:

```bibtex
@article{example2023,
  author = {Smith, J.},
  title = {Example Paper},
  journal = {Astronomy Journal},
  year = {2023},
  lrdKeys = {jwst, black hole mass, spectroscopy}
}
```

The `lrdKeys` field should contain a comma-separated list of tags that match those defined in the data file.

## Utility Scripts

The repository includes utility scripts to help maintain the tag system:

- **Tag Validation**: `webpage/scripts/update_tags.rb` - Helps identify inconsistencies between defined tags and tags used in BibTeX entries

To run the validation script:

```bash
cd webpage
ruby scripts/update_tags.rb
```

This will show:

- All defined tags in the YAML file
- All tags actually used in the BibTeX entries
- Any tags that are used but not defined (which should be added to the YAML file)
