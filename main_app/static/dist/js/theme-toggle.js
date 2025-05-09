/**
 * Theme Toggle System
 * Controls light/dark mode preferences and transitions
 */
// Add this function to your theme-toggle.js
function updateChartColors() {
    const chartText = getComputedStyle(document.documentElement).getPropertyValue('--chart-text').trim();
    const borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim();
    
    // Update chart text color
    document.querySelectorAll('.chart-container text, .chart-container .tick text').forEach(el => {
        el.style.fill = chartText;
    });
    
    // Update any Chart.js instances if you're using that library
    if (window.Chart && Chart.instances) {
        Object.values(Chart.instances).forEach(chart => {
            // Update legend text color
            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = chartText;
            }
            
            // Update axis colors
            if (chart.options.scales) {
                Object.values(chart.options.scales).forEach(scale => {
                    if (scale.ticks) scale.ticks.color = chartText;
                    if (scale.grid) scale.grid.color = borderColor;
                });
            }
            
            chart.update();
        });
    }
}

// Call this function when theme changes
themeToggle.addEventListener('click', function() {
    // ... existing code ...
    
    // Update chart colors after theme change
    setTimeout(updateChartColors, 50);
});

// Also call it on initial load
setTimeout(updateChartColors, 100);
// Add to your theme-toggle.js
window.addEventListener('load', function() {
    document.documentElement.classList.remove('no-transitions');
});
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    // Apply theme immediately
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Update theme toggle button state
    updateThemeToggleState(currentTheme);
    
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update theme toggle button state
        updateThemeToggleState(newTheme);
        
        // Add animation to toggle button
        this.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.style.transform = 'scale(1)';
        }, 100);
    });

    // Function to update theme toggle button state
    function updateThemeToggleState(theme) {
        const moonIcon = themeToggle.querySelector('.moon-icon');
        const sunIcon = themeToggle.querySelector('.sun-icon');
        
        if (theme === 'dark') {
            moonIcon.style.opacity = '0';
            moonIcon.style.transform = 'rotate(90deg) scale(0.5)';
            sunIcon.style.opacity = '1';
            sunIcon.style.transform = 'rotate(0) scale(1)';
        } else {
            moonIcon.style.opacity = '1';
            moonIcon.style.transform = 'rotate(0) scale(1)';
            sunIcon.style.opacity = '0';
            sunIcon.style.transform = 'rotate(-90deg) scale(0.5)';
        }
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            updateThemeToggleState(newTheme);
        }
    });
});
// Add this to your theme-toggle.js after the existing code

// Function to update chart colors when theme changes
function updateChartTheme() {
    // Only try if Chart is defined
    if (typeof Chart !== 'undefined') {
        const textColor = getComputedStyle(document.documentElement).getPropertyValue('--chart-text').trim();
        const gridColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim();
        const cardBg = getComputedStyle(document.documentElement).getPropertyValue('--card-bg').trim();
        
        // Set global font color
        Chart.defaults.global.defaultFontColor = textColor;
        
        // Update all charts
        Chart.helpers.each(Chart.instances, function(chart) {
            // Update legend colors
            if (chart.options.legend && chart.options.legend.labels) {
                chart.options.legend.labels.fontColor = textColor;
            }
            
            // Update tooltip colors
            if (chart.options.tooltips) {
                chart.options.tooltips.backgroundColor = cardBg;
                chart.options.tooltips.titleFontColor = textColor;
                chart.options.tooltips.bodyFontColor = textColor;
                chart.options.tooltips.borderColor = gridColor;
            }
            
            // Update scales if they exist
            if (chart.options.scales) {
                if (chart.options.scales.yAxes) {
                    chart.options.scales.yAxes.forEach(function(axis) {
                        if (axis.ticks) axis.ticks.fontColor = textColor;
                        if (axis.gridLines) {
                            axis.gridLines.color = gridColor;
                            axis.gridLines.zeroLineColor = gridColor;
                        }
                    });
                }
                
                if (chart.options.scales.xAxes) {
                    chart.options.scales.xAxes.forEach(function(axis) {
                        if (axis.ticks) axis.ticks.fontColor = textColor;
                        if (axis.gridLines) {
                            axis.gridLines.color = gridColor;
                            axis.gridLines.zeroLineColor = gridColor;
                        }
                    });
                }
            }
            
            // Update the chart
            chart.update();
        });
    }
}

// Add chart theme update to toggle click handler
themeToggle.addEventListener('click', function() {
    // Your existing theme toggle code here...
    
    // Add this to update chart colors after theme change
    setTimeout(updateChartTheme, 100);
});

// Also update on initial page load
if (document.readyState === 'complete') {
    updateChartTheme();
} else {
    window.addEventListener('load', function() {
        setTimeout(updateChartTheme, 200);
    });
}