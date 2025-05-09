/**
 * scripts.js - Custom JavaScript for the application
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Custom scripts loaded.");

    // --- Theme Toggle Functionality ---
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;
    const sunIcon = document.querySelector('.theme-toggle .sun-icon');
    const moonIcon = document.querySelector('.theme-toggle .moon-icon');

    // Function to apply the theme
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.setAttribute('data-theme', 'dark');
            body.classList.add('dark-mode'); // Add class for AdminLTE compatibility if needed
            if(sunIcon) sunIcon.style.opacity = '1';
            if(moonIcon) moonIcon.style.opacity = '0';
        } else {
            body.removeAttribute('data-theme');
            body.classList.remove('dark-mode'); // Remove class for AdminLTE compatibility
             if(sunIcon) sunIcon.style.opacity = '0';
            if(moonIcon) moonIcon.style.opacity = '1';
        }
        console.log(`Theme applied: ${theme}`);
    };

    // Function to toggle theme and save preference
    const toggleTheme = () => {
        const currentTheme = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', currentTheme); // Save preference
        applyTheme(currentTheme);
    };

    // Add click listener to the toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);

        // Check for saved theme preference on load
        const savedTheme = localStorage.getItem('theme');
        // Check for system preference if no saved theme
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

        // Apply saved theme or system preference
        if (savedTheme) {
            applyTheme(savedTheme);
        } else if (prefersDark) {
            applyTheme('dark');
        } else {
            applyTheme('light'); // Default to light if nothing else applies
        }

        // Listen for changes in system preference
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
            // Only change if no theme is explicitly saved
            if (!localStorage.getItem('theme')) {
                applyTheme(event.matches ? 'dark' : 'light');
            }
        });

    } else {
        console.warn("Theme toggle button not found.");
    }


    // --- Sidebar Hover Glow Effect ---
    const sidebarLinks = document.querySelectorAll('.nav-sidebar .nav-link');

    sidebarLinks.forEach(link => {
        link.addEventListener('mousemove', (e) => {
            // Get the bounding rectangle of the link
            const rect = link.getBoundingClientRect();
            // Calculate mouse position relative to the link
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            // Update the CSS variables for the radial gradient position
            link.style.setProperty('--x', `${x}px`);
            link.style.setProperty('--y', `${y}px`);
        });
    });


    // --- 3D Input Effect (Tilt on Focus) ---
    // Note: This effect can sometimes feel distracting or cause minor layout shifts.
    // Enable it cautiously and test thoroughly.
    const formControls = document.querySelectorAll('.form-control, input[type="text"], input[type="email"], input[type="password"], input[type="number"], input[type="date"], input[type="time"], input[type="search"], select, textarea');

    formControls.forEach(control => {
        control.addEventListener('focus', () => {
            // Apply a subtle tilt - adjust rotation values as desired
            // control.style.transform = 'translateZ(5px) rotateX(1deg) rotateY(-0.5deg)';
            // control.style.boxShadow = `0 0 0 3px var(--input-focus), 0 5px 10px rgba(0,0,0,0.1)`; // Enhance shadow
        });

        control.addEventListener('blur', () => {
            // Reset transformation and shadow on blur
            control.style.transform = 'translateZ(0) rotateX(0deg) rotateY(0deg)';
            // Reset to default focus shadow if needed, or rely on CSS :focus styles
            // control.style.boxShadow = `0 0 0 3px var(--input-focus)`; // Or remove completely if CSS handles it
        });
    });


    // --- Initialize Tooltips (Example using Bootstrap 5) ---
    // Ensure Bootstrap's JS is loaded for this to work
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        console.log("Bootstrap tooltips initialized.");
    } else {
        console.warn("Bootstrap Tooltip component not found. Skipping tooltip initialization.");
    }

    // --- Add more custom scripts below ---

    // Example: Initialize a specific plugin if it exists
    // if ($.fn.dataTable) { // Check if jQuery DataTables is loaded
    //     $('#myDataTable').DataTable();
    //     console.log("DataTables initialized.");
    // }

}); // End DOMContentLoaded
