document.addEventListener('DOMContentLoaded', function() {
    // Request notification permission
    if ('Notification' in window && Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
    
    // Function to show browser notification
    function showNotification(title, options) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(title, options);
            
            notification.onclick = function() {
                window.focus();
                if (options.url) {
                    window.location.href = options.url;
                }
                this.close();
            };
            
            // Auto close after 5 seconds
            setTimeout(notification.close.bind(notification), 5000);
        }
    }
    
    // Make the function available globally
    window.showNotification = showNotification;
});