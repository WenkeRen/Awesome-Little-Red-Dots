document.addEventListener("DOMContentLoaded", function () {
  // actual bibsearch logic
  const filterItems = (searchTerm) => {
    document.querySelectorAll(".bibliography, .unloaded").forEach((element) => element.classList.remove("unloaded"));

    // Simply add unloaded class to all non-matching items
    document.querySelectorAll(".bibliography > li").forEach((element, index) => {
      const text = element.innerText.toLowerCase();
      
      // Check if already hidden by tag filtering
      if (element.style.display === 'none') {
        element.classList.add("unloaded");
      } else if (searchTerm && text.indexOf(searchTerm) == -1) {
        element.classList.add("unloaded");
      }
    });

    document.querySelectorAll("h2.bibliography").forEach(function (element) {
      let iterator = element.nextElementSibling; // get next sibling element after h2, which can be h3 or ol
      let hideFirstGroupingElement = true;
      // iterate until next group element (h2), which is already selected by the querySelectorAll(-).forEach(-)
      while (iterator && iterator.tagName !== "H2") {
        if (iterator.tagName === "OL") {
          const ol = iterator;
          const unloadedSiblings = ol.querySelectorAll(":scope > li.unloaded");
          const totalSiblings = ol.querySelectorAll(":scope > li");

          if (unloadedSiblings.length === totalSiblings.length) {
            ol.previousElementSibling.classList.add("unloaded"); // Add the '.unloaded' class to the previous grouping element (e.g. year)
            ol.classList.add("unloaded"); // Add the '.unloaded' class to the OL itself
          } else {
            hideFirstGroupingElement = false; // there is at least some visible entry, don't hide the first grouping element
          }
        }
        iterator = iterator.nextElementSibling;
      }
      // Add unloaded class to first grouping element (e.g. year) if no item left in this group
      if (hideFirstGroupingElement) {
        element.classList.add("unloaded");
      }
    });
  };

  // Sensitive search. Only start searching if there's been no input for 300 ms
  let timeoutId;
  const searchInput = document.getElementById("bibsearch");
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      clearTimeout(timeoutId); // Clear the previous timeout
      const searchTerm = this.value.toLowerCase();
      timeoutId = setTimeout(() => filterItems(searchTerm), 300);
    });
  }
  
  // Make the filterItems function available globally for the tag filter to use
  window.bibsearchFilterItems = filterItems;
}); 