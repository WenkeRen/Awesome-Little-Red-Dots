---
layout: default
title: Citation Network
---

## Citation Network Papers

This collection of papers is derived from the citation network of Little Red Dots (LRD) literature. These papers may not explicitly mention "Little Red Dots" in their abstracts, but are frequently cited by LRD publications, indicating their importance to the field.

Our collection process (implemented in `kick_off_papers.py`) analyzes citation patterns to identify influential papers that:
- The bibtex type is `article`
- Are referenced by multiple LRD publications (>=10)
- Are published in 2022 or later to avoid very foundational papers

This citation-based approach helps identify key literature that might otherwise be missed by keyword searches, ensuring a comprehensive understanding of the field.

{% include bib_search.liquid %}

{% bibliography --file kick_off %} 