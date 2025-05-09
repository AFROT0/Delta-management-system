// messages-handler.js - Handle Django messages with SweetAlert2

document.addEventListener('DOMContentLoaded', function() {
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
});