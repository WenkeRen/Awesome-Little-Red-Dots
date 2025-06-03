// Publication Chart - Monthly publication statistics with interactive scrolling
document.addEventListener('DOMContentLoaded', function () {
    let publicationData = [];
    let chart = null;

    // Initialize the chart
    const initChart = () => {
        collectPublicationData();
        createChart();
    };

    // Collect publication data from bibliography entries
    const collectPublicationData = () => {
        const bibliographyItems = document.querySelectorAll('.bibliography li');
        const monthlyData = {};

        bibliographyItems.forEach(item => {
            // Extract year and month from the bibtex data
            const bibtexElement = item.querySelector('.bibtex.hidden');
            if (bibtexElement) {
                const bibtexText = bibtexElement.textContent;

                // Extract year
                const yearMatch = bibtexText.match(/year\s*=\s*[{\"]?(\d{4})[}\"]?/i);
                // Extract month
                const monthMatch = bibtexText.match(/month\s*=\s*[{\"]?([^,}\n]+)[}\"]?/i);

                if (yearMatch) {
                    const year = parseInt(yearMatch[1]);
                    let month = 1; // Default to January if no month specified

                    if (monthMatch) {
                        const monthStr = monthMatch[1].trim().toLowerCase();
                        // Convert month name to number
                        const monthNames = {
                            'january': 1, 'jan': 1,
                            'february': 2, 'feb': 2,
                            'march': 3, 'mar': 3,
                            'april': 4, 'apr': 4,
                            'may': 5,
                            'june': 6, 'jun': 6,
                            'july': 7, 'jul': 7,
                            'august': 8, 'aug': 8,
                            'september': 9, 'sep': 9, 'sept': 9,
                            'october': 10, 'oct': 10,
                            'november': 11, 'nov': 11,
                            'december': 12, 'dec': 12
                        };

                        if (monthNames[monthStr]) {
                            month = monthNames[monthStr];
                        } else if (!isNaN(parseInt(monthStr))) {
                            month = Math.max(1, Math.min(12, parseInt(monthStr)));
                        }
                    }

                    // Create year-month key (YYYY-MM format)
                    const monthKey = `${year}-${month.toString().padStart(2, '0')}`;
                    monthlyData[monthKey] = (monthlyData[monthKey] || 0) + 1;
                }
            }
        });

        // If no data found, return empty array
        if (Object.keys(monthlyData).length === 0) {
            publicationData = [];
            return;
        }

        // Find the earliest and latest dates
        const dates = Object.keys(monthlyData).sort();
        const earliestDate = dates[0];
        const latestDate = dates[dates.length - 1];

        // Generate all months from earliest to latest
        const completeMonthlyData = {};
        const [startYear, startMonth] = earliestDate.split('-').map(Number);
        const [endYear, endMonth] = latestDate.split('-').map(Number);

        let currentYear = startYear;
        let currentMonth = startMonth;

        while (currentYear < endYear || (currentYear === endYear && currentMonth <= endMonth)) {
            const monthKey = `${currentYear}-${currentMonth.toString().padStart(2, '0')}`;
            completeMonthlyData[monthKey] = monthlyData[monthKey] || 0;

            // Move to next month
            currentMonth++;
            if (currentMonth > 12) {
                currentMonth = 1;
                currentYear++;
            }
        }

        // Convert to array and sort by date
        publicationData = Object.entries(completeMonthlyData)
            .map(([key, count]) => ({
                date: key,
                year: parseInt(key.split('-')[0]),
                month: parseInt(key.split('-')[1]),
                count: count,
                displayDate: formatDisplayDate(key)
            }))
            .sort((a, b) => a.date.localeCompare(b.date));
    };

    // Format date for display
    const formatDisplayDate = (dateKey) => {
        const [year, month] = dateKey.split('-');
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${monthNames[parseInt(month) - 1]} ${year}`;
    };

    // Create the chart
    const createChart = () => {
        const container = document.getElementById('publication-chart');
        if (!container || publicationData.length === 0) return;

        // Chart dimensions
        const margin = { top: 30, right: 30, bottom: 60, left: 40 };
        const barWidth = 40;
        const barSpacing = 10;
        const totalWidth = publicationData.length * (barWidth + barSpacing) + margin.left + margin.right;
        const containerWidth = container.clientWidth;
        const width = Math.max(containerWidth - margin.left - margin.right, totalWidth - margin.left - margin.right);
        const height = 280 - margin.top - margin.bottom;

        // Clear existing chart
        container.innerHTML = '';

        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'chart-tooltip';
        container.appendChild(tooltip);

        // Create wrapper for horizontal scrolling
        const wrapper = document.createElement('div');
        wrapper.className = 'chart-wrapper';
        container.appendChild(wrapper);

        // Create SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'chart-svg');
        svg.setAttribute('width', totalWidth);
        svg.setAttribute('height', height + margin.top + margin.bottom);
        wrapper.appendChild(svg);

        // Create scales with extra space for labels
        const maxCount = Math.max(...publicationData.map(d => d.count));
        // Ensure we have a minimum scale even if maxCount is 0
        const effectiveMaxCount = Math.max(maxCount, 1);
        const yScale = (value) => margin.top + (height - (value / effectiveMaxCount) * (height - 40)); // Reserve 40px for bottom space
        const xScale = (index) => margin.left + index * (barWidth + barSpacing);

        // Draw bars
        publicationData.forEach((d, i) => {
            const barHeight = Math.max(0, (d.count / effectiveMaxCount) * (height - 40)); // Ensure non-negative height
            const x = xScale(i);
            const y = yScale(d.count);

            // Create bar group
            const barGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');

            // Bar rectangle
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('class', 'chart-bar');
            rect.setAttribute('x', x);
            rect.setAttribute('y', y);
            rect.setAttribute('width', barWidth);
            rect.setAttribute('height', barHeight);

            // Add hover effects
            rect.addEventListener('mouseenter', (e) => {
                showTooltip(e, d);
            });

            rect.addEventListener('mouseleave', () => {
                hideTooltip();
            });

            barGroup.appendChild(rect);

            // X-axis label (rotated)
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'chart-axis');
            text.setAttribute('x', x + barWidth / 2);
            text.setAttribute('y', height + margin.top + 25);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('transform', `rotate(-45, ${x + barWidth / 2}, ${height + margin.top + 30})`);
            text.textContent = d.displayDate;
            barGroup.appendChild(text);

            // Y-axis value (with better positioning)
            const valueText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            valueText.setAttribute('class', 'chart-axis');
            valueText.setAttribute('x', x + barWidth / 2);
            valueText.setAttribute('y', y - 6); // Optimal space above the bar
            valueText.setAttribute('text-anchor', 'middle');
            valueText.setAttribute('font-size', '11px');
            valueText.setAttribute('font-weight', 'bold');
            valueText.setAttribute('fill', 'var(--primary-color)');
            valueText.textContent = d.count;
            barGroup.appendChild(valueText);

            svg.appendChild(barGroup);
        });

        // Add Y-axis
        const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        yAxis.setAttribute('x1', margin.left - 5);
        yAxis.setAttribute('y1', margin.top);
        yAxis.setAttribute('x2', margin.left - 5);
        yAxis.setAttribute('y2', height + margin.top);
        yAxis.setAttribute('stroke', 'var(--border-color)');
        yAxis.setAttribute('stroke-width', '1');
        svg.appendChild(yAxis);

        // Add Y-axis title
        const yTitle = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        yTitle.setAttribute('class', 'chart-axis');
        yTitle.setAttribute('x', 15);
        yTitle.setAttribute('y', height / 2 + margin.top);
        yTitle.setAttribute('text-anchor', 'middle');
        yTitle.setAttribute('transform', `rotate(-90, 15, ${height / 2 + margin.top})`);
        yTitle.textContent = 'Publications';
        svg.appendChild(yTitle);

        // Add scroll functionality
        addScrollFunctionality(wrapper);
    };

    // Show tooltip
    const showTooltip = (event, data) => {
        const tooltip = document.querySelector('.chart-tooltip');
        tooltip.innerHTML = `
            <strong>${data.displayDate}</strong><br>
            ${data.count} publication${data.count !== 1 ? 's' : ''}
        `;
        tooltip.style.opacity = '1';

        // Position tooltip
        const rect = event.target.getBoundingClientRect();
        const container = document.getElementById('publication-chart');
        const containerRect = container.getBoundingClientRect();

        tooltip.style.left = (rect.left - containerRect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = (rect.top - containerRect.top - tooltip.offsetHeight - 10) + 'px';
    };

    // Hide tooltip
    const hideTooltip = () => {
        const tooltip = document.querySelector('.chart-tooltip');
        tooltip.style.opacity = '0';
    };

    // Add scroll functionality for touch devices
    const addScrollFunctionality = (wrapper) => {
        let isScrolling = false;
        let startX, scrollLeft;

        // Mouse events
        wrapper.addEventListener('mousedown', (e) => {
            isScrolling = true;
            startX = e.pageX - wrapper.offsetLeft;
            scrollLeft = wrapper.scrollLeft;
            wrapper.style.cursor = 'grabbing';
        });

        wrapper.addEventListener('mouseleave', () => {
            isScrolling = false;
            wrapper.style.cursor = 'grab';
        });

        wrapper.addEventListener('mouseup', () => {
            isScrolling = false;
            wrapper.style.cursor = 'grab';
        });

        wrapper.addEventListener('mousemove', (e) => {
            if (!isScrolling) return;
            e.preventDefault();
            const x = e.pageX - wrapper.offsetLeft;
            const walk = (x - startX) * 2;
            wrapper.scrollLeft = scrollLeft - walk;
        });

        // Touch events for mobile
        wrapper.addEventListener('touchstart', (e) => {
            startX = e.touches[0].pageX - wrapper.offsetLeft;
            scrollLeft = wrapper.scrollLeft;
        });

        wrapper.addEventListener('touchmove', (e) => {
            const x = e.touches[0].pageX - wrapper.offsetLeft;
            const walk = (x - startX) * 2;
            wrapper.scrollLeft = scrollLeft - walk;
        });

        // Scroll to the end (most recent data) initially
        setTimeout(() => {
            wrapper.scrollLeft = wrapper.scrollWidth;
        }, 100);
    };

    // Resize chart on window resize
    window.addEventListener('resize', () => {
        if (publicationData.length > 0) {
            createChart();
        }
    });

    // Initialize chart
    initChart();
});