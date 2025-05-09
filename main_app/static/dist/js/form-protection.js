// Form submission protection
(function() {
    // Prevent form resubmission on page refresh
    if (window.history.replaceState) {
        window.history.replaceState(null, null, window.location.href);
    }

    // Add protection to all forms
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            let formSubmitted = false;

            form.addEventListener('submit', function(e) {
                if (formSubmitted) {
                    e.preventDefault();
                    if (window.Swal) { // Check if SweetAlert2 is available
                        Swal.fire({
                            icon: 'warning',
                            title: 'Form Already Submitted',
                            text: 'Please wait or refresh the page to submit again.'
                        });
                    } else {
                        alert('Form already submitted. Please wait or refresh the page to submit again.');
                    }
                    return false;
                }
                formSubmitted = true;

                // Add hidden input with unique form ID
                const formId = document.createElement('input');
                formId.type = 'hidden';
                formId.name = 'form_id';
                formId.value = new Date().getTime() + '_' + Math.random().toString(36).substr(2, 9);
                form.appendChild(formId);
            });
        });
    });

    // Clear form submission status on page load
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            // Page was loaded from back-forward cache
            window.location.reload();
        }
    });
})(); 