/**
 * Interactive Elements System
 * Handles animation and interactive behaviors for UI elements
 */
document.addEventListener('DOMContentLoaded', function() {
    // Select all elements that should be interactive
    const interactiveElements = '.card, .container-fluid > div, .form-group, .btn, .nav-item, .form-control, .nav-link';
    
    document.querySelectorAll(interactiveElements).forEach(element => {
        element.classList.add('interactive-element');
    });
    
    // Add hover glow effect to sidebar navigation links
    document.querySelectorAll('.nav-sidebar .nav-link').forEach(link => {
        link.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / this.offsetWidth) * 100;
            const y = ((e.clientY - rect.top) / this.offsetHeight) * 100;
            
            this.style.setProperty('--x', `${x}%`);
            this.style.setProperty('--y', `${y}%`);
        });
    });
    
    // Message display system (for Django messages)
    if (document.getElementById('django-messages')) {
        const messageElements = document.querySelectorAll('#django-messages .message');
        messageElements.forEach(function(element) {
            Swal.fire({
                icon: element.dataset.type,
                title: element.dataset.type.charAt(0).toUpperCase() + element.dataset.type.slice(1),
                text: element.dataset.text,
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });
        });
    }
});