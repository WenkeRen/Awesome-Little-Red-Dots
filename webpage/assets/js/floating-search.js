// Floating Search Bar
document.addEventListener('DOMContentLoaded', function () {
    const searchElement = document.querySelector('.search');
    if (!searchElement) return;

    // Create container and placeholder elements
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';

    const searchPlaceholder = document.createElement('div');
    searchPlaceholder.className = 'search-placeholder';

    // Wrap the search element
    searchElement.parentNode.insertBefore(searchContainer, searchElement);
    searchContainer.appendChild(searchElement);
    searchContainer.parentNode.insertBefore(searchPlaceholder, searchContainer.nextSibling);

    // Store the original position
    let originalOffsetTop = searchContainer.offsetTop;
    let isFloating = false;

    // Throttle function for performance
    const throttle = (func, delay) => {
        let timeoutId;
        let lastExecTime = 0;
        return function (...args) {
            const currentTime = Date.now();

            if (currentTime - lastExecTime > delay) {
                func.apply(this, args);
                lastExecTime = currentTime;
            } else {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                    lastExecTime = Date.now();
                }, delay - (currentTime - lastExecTime));
            }
        };
    };

    // Handle scroll events
    const handleScroll = throttle(() => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        // Update original position if layout changes
        if (!isFloating) {
            originalOffsetTop = searchContainer.offsetTop;
        }

        if (scrollTop > originalOffsetTop && !isFloating) {
            // Make search bar floating
            isFloating = true;
            searchContainer.classList.add('floating');
            searchPlaceholder.classList.add('active');

        } else if (scrollTop <= originalOffsetTop && isFloating) {
            // Remove floating state
            isFloating = false;
            searchContainer.classList.remove('floating');
            searchPlaceholder.classList.remove('active');
            // Clear any transform styles that may have been applied
            searchContainer.style.transform = '';
        }
    }, 16); // ~60fps

    // Handle window resize
    const handleResize = throttle(() => {
        if (!isFloating) {
            originalOffsetTop = searchContainer.offsetTop;
        }
        // Force a scroll check to ensure correct state
        handleScroll();
    }, 250);

    // Add event listeners
    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleResize);

    // Initial check in case page is already scrolled
    handleScroll();

    // Enhanced focus behavior for floating search
    searchElement.addEventListener('focus', () => {
        if (isFloating) {
            searchContainer.style.transform = 'translateX(-50%) scale(1.02)';
        }
    });

    searchElement.addEventListener('blur', () => {
        if (isFloating) {
            searchContainer.style.transform = 'translateX(-50%) scale(1)';
        } else {
            // Ensure no transform is applied when not floating
            searchContainer.style.transform = '';
        }
    });
}); 