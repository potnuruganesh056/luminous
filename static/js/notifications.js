// notifications.js - Notification system
window.NotificationSystem = {
    // Show notification to user
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full`;
        
        // Set notification style based on type
        switch(type) {
            case 'on':
            case 'success':
                notification.className += ' bg-green-500 text-white';
                break;
            case 'off':
            case 'error':
                notification.className += ' bg-red-500 text-white';
                break;
            case 'warning':
                notification.className += ' bg-yellow-500 text-white';
                break;
            default:
                notification.className += ' bg-blue-500 text-white';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.classList.remove('translate-x-full');
        });
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    },

    // Show loading notification
    showLoading(message = 'Loading...') {
        const loadingId = 'loading-notification';
        
        // Remove existing loading notification
        const existing = document.getElementById(loadingId);
        if (existing) {
            existing.remove();
        }
        
        const notification = document.createElement('div');
        notification.id = loadingId;
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 bg-blue-500 text-white flex items-center`;
        notification.innerHTML = `
            <i class="fas fa-spinner fa-spin mr-2"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        return loadingId;
    },

    // Hide loading notification
    hideLoading(loadingId = 'loading-notification') {
        const notification = document.getElementById(loadingId);
        if (notification) {
            notification.remove();
        }
    }
};
