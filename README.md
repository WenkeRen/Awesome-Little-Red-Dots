# Awesome-Little-Red-Dots

![GitHub last commit](https://img.shields.io/github/last-commit/wenkeren/Awesome-Little-Red-Dots)
![GitHub stars](https://img.shields.io/github/stars/wenkeren/Awesome-Little-Red-Dots?style=social)

## 🔴 What are Little Red Dots (LRDs)?

Little Red Dots (LRDs) are a newly discovered population of faint, red, compact sources revealed by JWST observations. They are believed to be active galactic nuclei (AGNs) at high redshifts (z~4-6), representing the early growth phase of supermassive black holes in the early universe. Understanding LRDs helps us trace the origins of supermassive black holes and galaxy formation in the early universe.

## 📚 About This Project

Awesome-Little-Red-Dots is an open-science initiative to centralize and analyze the rapidly growing literature on "Little Red Dots" (LRDs). This repository:

- Maintains a comprehensive, up-to-date bibliography of LRD-related research
- Provides an accessible website for browsing and filtering the literature
- Uses AI to tag and categorize papers by their key focus areas
- Facilitates community collaboration on understanding early SMBH growth and galaxy formation

**Browse the bibliography: [https://www.wenkeren.com/Awesome-Little-Red-Dots/](https://www.wenkeren.com/Awesome-Little-Red-Dots/)**

## 🤖 How We Use AI for Paper Tagging

One of the unique aspects of this project is the use of AI to automatically categorize papers with relevant tags:

1. We maintain a structured taxonomy of LRD research areas in `library/LRD Literature Tags.yml`
2. Our `paper_kwd.py` script processes papers through the Qwen-Max API (Aliyun's large language model)
3. For each paper, the AI analyzes the title and abstract to select up to 5 relevant tags
4. These tags are stored in the paper's BibTeX entry and displayed on the website
5. Tags help researchers quickly identify papers focusing on specific aspects (e.g., spectroscopy, black hole mass, dust)

This approach ensures consistent categorization across the growing literature and makes the bibliography more useful for filtering and finding relevant research.

## 🔄 How We Collect and Update Data

The bibliography is automatically updated through several mechanisms:

1. **Daily ADS API Queries**: The `lrd_ads_request.py` script searches NASA's ADS API for new papers mentioning "Little Red Dots"
2. **Separate Collection of Articles and Proposals**: Papers are sorted into `aslrd.bib` (articles) and `aslrd_prop.bib` (proposals)
3. **GitHub Actions Automation**: Updates run daily at 6:00 AM UTC to keep the bibliography current
4. **Metrics Integration**: For papers with DOIs, we incorporate Dimensions and Altmetric data
5. **Manual Curation**: Community contributions help ensure the bibliography captures relevant papers that might use varying terminology

## 🌐 Website Organization

The project website ([https://www.wenkeren.com/Awesome-Little-Red-Dots/](https://www.wenkeren.com/Awesome-Little-Red-Dots/)) provides:

- A searchable, filterable bibliography of all LRD papers
- Tag-based filtering to find papers on specific aspects of LRD research
- Links to paper DOIs, ADS entries, and arXiv preprints when available
- Paper abstracts and citation information
- A clean, responsive interface built with Jekyll

## 👥 How to Contribute

We welcome contributions of all kinds! Here's how you can help:

- **Missing Papers**: If you notice papers about LRDs missing from our collection, please open an issue
- **Website Improvements**: Suggestions for enhancing the website functionality and user experience
- **Data Analysis**: Ideas for analyzing the collected literature or creating visualizations
- **Tag Taxonomy**: Refinements to our tagging system to better represent research areas
- **Code Contributions**: Improvements to our automation scripts and website

To contribute, either:

- Open an [issue](https://github.com/wenkeren/Awesome-Little-Red-Dots/issues) with your suggestion/feedback
- Submit a [pull request](https://github.com/wenkeren/Awesome-Little-Red-Dots/pulls) with your proposed changes

All contributions are appreciated, and we're especially interested in making this resource more valuable to the astronomy community!

## License

This repository is licensed under dual licenses:

- **Code**: All scripts, automation tools, and other code in this repository are licensed under the [MIT License](LICENSE).
- **Content**: All curated content, including bibliographic files (.bib), markdown summaries, and other documentation are licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

This means you are free to:

- Use, modify and distribute the code under the terms of the MIT License
- Share and adapt the content as long as you provide appropriate credit as specified by the CC BY 4.0 license
