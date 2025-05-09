// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Remove the loading class to enable transitions after page load
    setTimeout(function() {
        document.documentElement.classList.remove('theme-loading');
    }, 300);
    
    const themeToggle = document.getElementById('themeToggle');
    
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    // Apply theme immediately
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Update theme toggle button state
    updateThemeToggleState(currentTheme);
    
    themeToggle.addEventListener('click', function(e) {
        // Prevent default action if this was a link
        e.preventDefault();
        
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
        
        // Ensure inputs get updated with correct colors
        updateInputStyles();
        
        return false; // Prevent page reload
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
    
    // Function to update input styles based on theme
    function updateInputStyles() {
        const inputs = document.querySelectorAll('.form-control');
        inputs.forEach(input => {
            // Force a redraw of the input to ensure CSS variables are applied
            input.style.display = 'none';
            setTimeout(() => {
                input.style.display = '';
            }, 5);
        });
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            updateThemeToggleState(newTheme);
            updateInputStyles();
        }
    });

    // Add particles
    createParticles();
    
    // Initialize inputs
    updateInputStyles();
});

// Add particles with JavaScript
function createParticles() {
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    document.body.appendChild(particlesContainer);

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.opacity = Math.random() * 0.5;
        particlesContainer.appendChild(particle);
    }
}

// Handle login messages
document.addEventListener('DOMContentLoaded', function() {
    const messageElements = document.querySelectorAll('#login-messages .message');
    if (messageElements.length > 0) {
        messageElements.forEach(function(element) {
            Swal.fire({
                icon: 'error',
                title: 'Login Failed',
                text: element.dataset.text,
                confirmButtonColor: '#2E86C1'
            });
        });
    }
});