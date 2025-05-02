// Tag filtering functionality for LRD bibliography

document.addEventListener('DOMContentLoaded', function () {
  // We'll load tag descriptions from the available tags in the HTML
  let tagDescriptions = {};
  let bibtexEntries = [];

  // Get available tags from HTML
  const getTagsFromHTML = () => {
    console.log("Getting tags from HTML");
    const availableTags = document.getElementById('available-tags');
    if (!availableTags) {
      console.log("available-tags element not found");
      return {};
    }

    const tagSpans = availableTags.querySelectorAll('span[data-tag]');
    const tags = {};

    tagSpans.forEach(span => {
      const tag = span.getAttribute('data-tag');
      if (tag) {
        tags[tag] = span.textContent || `Tag: ${tag}`;
      }
    });

    console.log(`Found ${Object.keys(tags).length} tags from HTML`);
    return tags;
  };

  // Function to extract all available tag names from available-tags div
  const extractTagsFromAvailableTagsDiv = () => {
    const availableTags = document.getElementById('available-tags');
    if (!availableTags) {
      console.log("available-tags element not found for extraction");
      return [];
    }

    const tagNames = [];

    // Get span elements with data-tag attributes
    const tagSpans = availableTags.querySelectorAll('span[data-tag]');
    tagSpans.forEach(span => {
      const tag = span.getAttribute('data-tag');
      if (tag && !tagNames.includes(tag)) {
        tagNames.push(tag);
      }
    });

    console.log(`Extracted ${tagNames.length} tag names from available-tags div`);
    return tagNames;
  };

  // Function to load and parse the YAML file
  const loadTagDescriptions = async () => {
    try {
      // First try to get tags from HTML
      const htmlTags = getTagsFromHTML();
      if (Object.keys(htmlTags).length > 0) {
        console.log("Using tags from HTML");
        for (const [tag, description] of Object.entries(htmlTags)) {
          tagDescriptions[tag] = description;
        }
        loadBibtexFile();
        return;
      }

      console.log("No tags found in HTML, attempting to load from YAML file");

      // Try to load YAML file from assets/data directory
      // Get baseUrl from meta tag
      const baseUrl = document.querySelector('meta[name="baseurl"]')?.getAttribute('content') || '';
      console.log("Base URL from meta tag:", baseUrl);

      let yamlText = null;
      let fetchSuccessful = false;

      // Try multiple potential paths
      const potentialPaths = [
        `${baseUrl}/assets/data/LRD Literature Tags.yml`,
        `/assets/data/LRD Literature Tags.yml`,
        `/Awesome-Little-Red-Dots/assets/data/LRD Literature Tags.yml`,
        `./assets/data/LRD Literature Tags.yml`
      ];

      for (const path of potentialPaths) {
        if (fetchSuccessful) break;

        try {
          console.log(`Attempting to fetch from: ${path}`);
          const response = await fetch(path);
          if (response.ok) {
            yamlText = await response.text();
            console.log(`Successfully loaded YAML from: ${path}`);
            fetchSuccessful = true;
          }
        } catch (e) {
          console.log(`Failed to fetch from ${path}:`, e);
        }
      }

      if (!yamlText) {
        throw new Error("Could not load YAML file from any potential path");
      }

      // Simple YAML parser for our specific format
      const lines = yamlText.split('\n');
      let currentTag = null;

      console.log("Successfully loaded YAML file, parsing tags...");

      lines.forEach(line => {
        // Look for tag definition
        const tagMatch = line.match(/^\s*-\s+tag:\s+(.+)$/);
        if (tagMatch) {
          currentTag = tagMatch[1].trim();
        }

        // Look for description that corresponds to the current tag
        const descMatch = line.match(/^\s*description:\s+(.+)$/);
        if (descMatch && currentTag) {
          tagDescriptions[currentTag] = descMatch[1].trim();
          currentTag = null;
        }
      });

      console.log(`Parsed ${Object.keys(tagDescriptions).length} tags from YAML`);

      // After loading descriptions, load BibTeX file
      loadBibtexFile();
    } catch (error) {
      console.log("Error loading tag descriptions:", error);

      // Fallback to tags in #available-tags or basic descriptions
      const htmlTags = getTagsFromHTML();
      if (Object.keys(htmlTags).length > 0) {
        console.log("Falling back to HTML tags");
        tagDescriptions = htmlTags;
      } else {
        console.log("Using hardcoded fallback tags");
        // Fallback to some basic descriptions if YAML loading fails
        tagDescriptions = {
          "case study": "In-depth analysis of specific LRD sources",
          "simulation": "Computational models for LRD properties",
          "jwst": "JWST observational data",
          "dust": "Role of dust in LRD properties",
          "sed": "Spectral Energy Distribution analysis",
          "black hole mass": "SMBH mass estimation or growth",
          "spectroscopy": "Spectral analysis",
          "photometry": "Source brightness measurements",
          "sample selection": "Methods for identifying LRD candidates"
        };
      }

      // Still try to load BibTeX file
      loadBibtexFile();
    }
  };

  // Function to load the BibTeX file directly
  const loadBibtexFile = async () => {
    try {
      // First, check if the bibliography is already loaded in the HTML
      // If it is, we can get tags directly from the HTML without fetching the BibTeX file
      const bibliographyElements = document.querySelectorAll('.bibliography li');
      if (bibliographyElements.length > 0) {
        console.log("Bibliography already loaded in HTML, skipping BibTeX fetch");
        initializeTagFilters();
        return;
      }

      // If bibliography is not in HTML, we need to try to load the BibTeX file
      console.log("Attempting to fetch bibtex data...");

      // In Jekyll, we can't easily access files outside the website root directly with fetch
      // However, Jekyll-Scholar has already processed the BibTeX file, so let's use that info
      const bib_items = document.querySelectorAll('.bibtex.hidden');
      if (bib_items && bib_items.length > 0) {
        console.log(`Found ${bib_items.length} bibliography items with bibtex data in HTML`);

        // Extract and parse bibtex data from HTML elements
        bib_items.forEach(item => {
          const bibtexContent = item.textContent;
          if (bibtexContent) {
            parseBibtexEntry(bibtexContent);
          }
        });

        // Initialize filters with the data we extracted
        initializeTagFilters();
        return;
      }

      console.log("No bibliography or bibtex data found in the HTML");
      initializeTagFilters();
    } catch (error) {
      console.log("Error loading BibTeX content:", error);

      // If we couldn't load the BibTeX file, just initialize with what we have
      initializeTagFilters();
    }
  };

  // Function to parse a single bibtex entry
  const parseBibtexEntry = (bibtexText) => {
    // Extract BibTeX key
    const keyMatch = bibtexText.match(/@\w+\s*{\s*([^,]+),/);
    if (!keyMatch) return;

    const key = keyMatch[1].trim();

    // Extract lrdKeys
    const lrdKeysMatch = bibtexText.match(/lrdKeys\s*=\s*{([^}]*)}/i);

    if (lrdKeysMatch) {
      const lrdKeys = lrdKeysMatch[1]
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag !== '');

      // Add to our bibtex entries list
      bibtexEntries.push({
        key: key,
        bibtex: bibtexText,
        lrdKeys: lrdKeys,
        lrdKeysLower: lrdKeys.map(tag => tag.toLowerCase())
      });
    }
  };

  // Function to parse BibTeX entries
  const parseBibtexEntries = (bibtexText) => {
    // Split the text into entries
    const entries = bibtexText.split('@');

    // Process each entry
    for (let i = 1; i < entries.length; i++) { // Start from 1 to skip the first empty entry
      const entry = '@' + entries[i].trim();
      parseBibtexEntry(entry);
    }
  };

  // Get all bibliography items
  const bibliographyItems = document.querySelectorAll('.bibliography li');

  // Create tag filter container
  const createTagFilter = () => {
    // Check if we're on the main bibliography page
    const isMainBibliographyPage = !window.location.pathname.includes('kick_off') &&
      !window.location.pathname.includes('proposals');

    if (!isMainBibliographyPage) {
      return;
    }

    console.log("Creating tag filter with", Object.keys(tagDescriptions).length, "tags");

    // If we don't have tag descriptions yet, try to get them from bibliography entries
    if (Object.keys(tagDescriptions).length === 0) {
      console.log("No tag descriptions found, extracting from bibliography entries");

      // First try to get tag names from the available-tags div
      const availableTagNames = extractTagsFromAvailableTagsDiv();
      availableTagNames.forEach(tag => {
        if (!tagDescriptions[tag]) {
          tagDescriptions[tag] = `Tag: ${tag}`;
        }
      });

      // Then try to extract from bibliography entries
      bibliographyItems.forEach(item => {
        const tagsAttr = item.getAttribute('data-lrd-keys');
        if (tagsAttr) {
          const tags = tagsAttr.split(',').map(tag => tag.trim()).filter(tag => tag !== '');
          tags.forEach(tag => {
            if (!tagDescriptions[tag]) {
              tagDescriptions[tag] = `Tag: ${tag}`;
            }
          });
        }

        // Also try to find tags in bibtex content
        const bibtexElement = item.querySelector('.bibtex.hidden');
        if (bibtexElement) {
          const bibtexContent = bibtexElement.textContent || '';
          const lrdKeysMatch = bibtexContent.match(/lrdKeys\s*=\s*{([^}]*)}/i);
          if (lrdKeysMatch && lrdKeysMatch[1]) {
            const tags = lrdKeysMatch[1].split(',').map(tag => tag.trim()).filter(tag => tag !== '');
            tags.forEach(tag => {
              if (!tagDescriptions[tag]) {
                tagDescriptions[tag] = `Tag: ${tag}`;
              }
            });
          }
        }
      });

      // Also look for tags in the visible tags on the page
      document.querySelectorAll('.entry-tag').forEach(tagElement => {
        const tag = tagElement.textContent.trim();
        if (tag && !tagDescriptions[tag]) {
          tagDescriptions[tag] = `Tag: ${tag}`;
        }
      });

      console.log("Extracted", Object.keys(tagDescriptions).length, "tags from bibliography entries");
    }

    // Create the tag filter container regardless of whether items have been tagged yet
    const tagFilterContainer = document.createElement('div');
    tagFilterContainer.className = 'tag-filter-container';

    // Create the title
    const title = document.createElement('h3');
    title.textContent = 'Filter by Tags';
    tagFilterContainer.appendChild(title);

    // Create explanation text
    const explanation = document.createElement('p');
    explanation.className = 'tag-filter-explanation';
    explanation.textContent = 'Select one or more tags to filter papers. Only papers with all selected tags will be shown. Hover over a tag to see its description.';
    tagFilterContainer.appendChild(explanation);

    // Create the tag checkboxes
    const tagCheckboxes = document.createElement('div');
    tagCheckboxes.className = 'tag-checkboxes';

    // Sort all tags alphabetically
    const sortedTags = Object.keys(tagDescriptions).sort();

    sortedTags.forEach(tag => {
      const checkboxContainer = document.createElement('div');
      checkboxContainer.className = 'tag-checkbox';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.id = `tag-${tag.replace(/\s+/g, '-')}`;
      checkbox.value = tag;

      const label = document.createElement('label');
      label.htmlFor = checkbox.id;
      label.textContent = tag;

      // Add tooltip with tag description
      if (tagDescriptions[tag]) {
        const tooltip = document.createElement('span');
        tooltip.className = 'tag-tooltip';
        tooltip.textContent = tagDescriptions[tag];
        label.appendChild(tooltip);
      }

      checkboxContainer.appendChild(checkbox);
      checkboxContainer.appendChild(label);
      tagCheckboxes.appendChild(checkboxContainer);

      // Add event listener to filter items when checkbox is changed
      checkbox.addEventListener('change', filterItems);
    });

    // Create clear filters button
    const clearButton = document.createElement('button');
    clearButton.textContent = 'Clear Filters';
    clearButton.className = 'clear-filters-btn';
    clearButton.addEventListener('click', clearFilters);

    tagFilterContainer.appendChild(tagCheckboxes);
    tagFilterContainer.appendChild(clearButton);

    // Add the tag filter container before the search box
    const searchBox = document.querySelector('.search');
    if (searchBox) {
      searchBox.parentNode.insertBefore(tagFilterContainer, searchBox);
    }
  };

  // Filter bibliography items based on selected tags
  const filterItems = () => {
    const selectedTags = Array.from(document.querySelectorAll('.tag-checkbox input:checked'))
      .map(checkbox => checkbox.value);

    // Display all items if no tags are selected
    if (selectedTags.length === 0) {
      bibliographyItems.forEach(item => {
        item.style.display = '';
      });
      return;
    }

    // Convert selected tags to lowercase for case-insensitive matching
    const selectedTagsLower = selectedTags.map(tag => tag.toLowerCase());

    // First approach: If we have parsed BibTeX entries, use those
    if (bibtexEntries.length > 0) {
      // Get the keys of entries that have all selected tags
      const matchingKeys = bibtexEntries
        .filter(entry => selectedTagsLower.every(tag => entry.lrdKeysLower.includes(tag)))
        .map(entry => entry.key);

      // Hide/show bibliography items based on whether their key is in the matching keys list
      bibliographyItems.forEach(item => {
        const itemId = item.id;
        if (matchingKeys.includes(itemId)) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
    }
    // Second approach: If we couldn't parse BibTeX entries, check data-lrd-keys attributes
    else {
      bibliographyItems.forEach(item => {
        const itemTags = (item.getAttribute('data-lrd-keys') || '').split(',')
          .map(tag => tag.trim().toLowerCase())
          .filter(tag => tag !== '');

        if (selectedTagsLower.every(tag => itemTags.includes(tag))) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
    }

    // Update the bibsearch filtering as well
    if (window.bibsearchFilterItems) {
      const searchBox = document.querySelector('.search');
      if (searchBox) {
        window.bibsearchFilterItems(searchBox.value.toLowerCase());
      } else {
        window.bibsearchFilterItems('');
      }
    }
  };

  // Clear all selected filters
  const clearFilters = () => {
    document.querySelectorAll('.tag-checkbox input:checked').forEach(checkbox => {
      checkbox.checked = false;
    });

    bibliographyItems.forEach(item => {
      item.style.display = '';
    });

    // Update the bibsearch filtering as well
    if (window.bibsearchFilterItems) {
      const searchBox = document.querySelector('.search');
      if (searchBox) {
        window.bibsearchFilterItems(searchBox.value.toLowerCase());
      } else {
        window.bibsearchFilterItems('');
      }
    }
  };

  // Process each bibliography item to add tags
  const processBibliographyItems = () => {
    // If we have parsed BibTeX entries, use them to add tags to HTML items
    if (bibtexEntries.length > 0) {
      bibliographyItems.forEach(item => {
        const itemId = item.id;
        const matchingEntry = bibtexEntries.find(entry => entry.key === itemId);

        if (matchingEntry) {
          // Set data attribute with lowercase tags for filtering
          item.setAttribute('data-lrd-keys', matchingEntry.lrdKeysLower.join(','));

          // Create and add tag elements
          const tagsContainer = document.createElement('div');
          tagsContainer.className = 'entry-tags';

          matchingEntry.lrdKeys.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'entry-tag';
            tagElement.textContent = tag; // Keep original case for display

            // Find case-insensitive matching description
            const tagKey = Object.keys(tagDescriptions)
              .find(key => key.toLowerCase() === tag.toLowerCase());

            if (tagKey && tagDescriptions[tagKey]) {
              const tooltip = document.createElement('span');
              tooltip.className = 'tag-tooltip';
              tooltip.textContent = tagDescriptions[tagKey];
              tagElement.appendChild(tooltip);
            }

            tagsContainer.appendChild(tagElement);
          });

          // Find where to insert the tags
          const periodical = item.querySelector('.periodical');
          const links = item.querySelector('.links');

          if (periodical) {
            periodical.parentNode.insertBefore(tagsContainer, periodical.nextSibling);
          } else if (links) {
            links.parentNode.insertBefore(tagsContainer, links);
          }
        }
      });
    }
    // If we couldn't parse BibTeX entries, fall back to scanning HTML
    else {
      bibliographyItems.forEach(item => {
        // Find the bibtex element
        const bibtexElement = item.querySelector('.bibtex.hidden');
        if (!bibtexElement) {
          return;
        }

        const bibtexContent = bibtexElement.textContent || '';

        // Try to extract lrdKeys
        let lrdKeysMatch = bibtexContent.match(/lrdKeys\s*=\s*{([^}]*)}/i);

        if (!lrdKeysMatch) {
          lrdKeysMatch = bibtexContent.match(/tags\s*=\s*{([^}]*)}/i);
        }

        if (lrdKeysMatch && lrdKeysMatch[1]) {
          const lrdKeys = lrdKeysMatch[1];

          // Clean and normalize tags
          const tagArray = lrdKeys.split(',')
            .map(tag => tag.trim())
            .filter(tag => tag !== ''); // Remove empty tags

          if (tagArray.length > 0) {
            // For data attribute, use lowercase for case-insensitive matching
            item.setAttribute('data-lrd-keys', tagArray.join(',').toLowerCase());

            // Add visual tag indicators
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'entry-tags';

            tagArray.forEach(tag => {
              const tagElement = document.createElement('span');
              tagElement.className = 'entry-tag';
              tagElement.textContent = tag; // Keep original case for display

              // Find case-insensitive matching description
              const tagKey = Object.keys(tagDescriptions)
                .find(key => key.toLowerCase() === tag.toLowerCase());

              if (tagKey && tagDescriptions[tagKey]) {
                const tooltip = document.createElement('span');
                tooltip.className = 'tag-tooltip';
                tooltip.textContent = tagDescriptions[tagKey];
                tagElement.appendChild(tooltip);
              }

              tagsContainer.appendChild(tagElement);
            });

            // Insert tags after the periodical or before the links
            const periodical = item.querySelector('.periodical');
            const links = item.querySelector('.links');

            if (periodical) {
              periodical.parentNode.insertBefore(tagsContainer, periodical.nextSibling);
            } else if (links) {
              links.parentNode.insertBefore(tagsContainer, links);
            }
          }
        }
      });
    }
  };

  // Function to initialize everything after tag descriptions are loaded
  const initializeTagFilters = () => {
    processBibliographyItems();
    createTagFilter();
  };

  // Start by loading the tag descriptions
  loadTagDescriptions();
}); 