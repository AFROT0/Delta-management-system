document.addEventListener('DOMContentLoaded', function() {
    // Only add the clock if we're not on the login page
    if (!document.querySelector('.login-page') && !document.querySelector('.register-page')) {
        // Create clock container
        const clockContainer = document.createElement('div');
        clockContainer.className = 'digital-clock-container';
        
        // Add clock icon
        const clockIcon = document.createElement('i');
        clockIcon.className = 'fas fa-clock digital-clock-icon';
        clockContainer.appendChild(clockIcon);
        
        // Add time element
        const timeElement = document.createElement('span');
        timeElement.className = 'digital-clock-time';
        clockContainer.appendChild(timeElement);
        
        // Add date element (shows on hover)
        const dateElement = document.createElement('span');
        dateElement.className = 'digital-clock-date';
        clockContainer.appendChild(dateElement);
        
        // Find the wrapper element and insert the clock at the beginning
        const wrapper = document.querySelector('.wrapper');
        if (wrapper) {
            wrapper.insertBefore(clockContainer, wrapper.firstChild);
        } else {
            // Fallback to body if wrapper not found
            document.body.appendChild(clockContainer);
        }
        
        // Update clock function
        function updateClock() {
            // Get current time in Cairo (UTC+2)
            const options = { 
                timeZone: 'Africa/Cairo',
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit',
                hour12: true
            };
            
            const dateOptions = {
                timeZone: 'Africa/Cairo',
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            };
            
            const now = new Date();
            
            // Format the time for Cairo timezone
            const timeString = now.toLocaleTimeString('en-US', options);
            const dateString = now.toLocaleDateString('en-US', dateOptions);
            
            // Update the elements
            timeElement.textContent = timeString;
            dateElement.textContent = dateString;
        }
        
        // Initial update
        updateClock();
        
        // Update every second
        setInterval(updateClock, 1000);
    }
}); 