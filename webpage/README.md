# Awesome Little Red Dots Bibliography Webpage

This directory contains the Jekyll-based bibliography website for the Awesome Little Red Dots (ASLRD) project. The website is automatically built and deployed to GitHub Pages whenever changes are made to the `webpage` or `library` directories.

## Structure

- The website uses Jekyll and the Jekyll-Scholar plugin to generate a bibliography from the BibTeX file in the `../library/` directory.
- The tag filtering system allows users to filter papers by tags defined in the `_data/lrd_tags.yml` file.

## Development

To run this website locally:

1. Install Ruby and Bundler
2. Run `bundle install` in this directory
3. Run `bundle exec jekyll serve` to start a local server

## Deployment

The website is automatically deployed to GitHub Pages using GitHub Actions. The workflow:

1. Copies the tag definitions from the library to the Jekyll `_data` directory
2. Builds the Jekyll site
3. Deploys to GitHub Pages

## How It Works

- The bibliography is generated from the `aslrd.bib` file in the `../library/` directory
- The Jekyll-Scholar plugin processes this file and generates HTML for each bibliography entry
- The tag filtering system extracts tag information from the BibTeX entries and allows users to filter based on these tags
- Tags are defined in `_data/lrd_tags.yml` and accessed via Jekyll's data system
- The `_includes/tag_list.html` template dynamically renders the tags from the data file

## Files and Directories

- `_config.yml`: Configuration for Jekyll and Jekyll-Scholar
- `index.md`: Main landing page
- `_layouts/`: Contains template files for the site
- `_data/`: Contains structured data files (including tag definitions)
- `_includes/`: Contains reusable template components
- `assets/`: Contains CSS and JavaScript files
- `scripts/`: Contains utility scripts for managing the website
- `docs/`: Contains documentation files for the website

## Tag System

The website's tag filtering system allows users to filter bibliography entries by topic. See `docs/tag-system.md` for detailed documentation on how the tag system works and how to maintain it.

## Utilities

The `scripts` directory contains utility scripts:

- `update_tags.rb`: Validates tag definitions against usage in the BibTeX file
