// Tag filtering functionality for LRD bibliography

document.addEventListener('DOMContentLoaded', function() {
  // We'll load tag descriptions from the YAML file
  let tagDescriptions = {};
  let bibtexEntries = [];
  
  // Function to load and parse the YAML file
  const loadTagDescriptions = async () => {
    try {
      // Try to load YAML file from assets/data directory
      const response = await fetch('/assets/data/LRD Literature Tags.yml');
      const yamlText = await response.text();
      
      // Simple YAML parser for our specific format
      const lines = yamlText.split('\n');
      let currentTag = null;
      
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
      
      // After loading descriptions, load BibTeX file
      loadBibtexFile();
    } catch (error) {
      console.log("Error loading tag descriptions:", error);
      
      // Fallback to some basic descriptions if YAML loading fails
      tagDescriptions = {
        "case study": "In-depth analysis of specific LRD sources",
        "simulation": "Computational models for LRD properties",
        "jwst": "JWST observational data"
        // Add other essential tags as minimal fallback
      };
      
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