// notifications.js - Notification system
window.NotificationSystem = {
    // Show notification to user
    showNotification(message, type = 'info') {
        // Check for notification area container, fallback to body
        const container = document.getElementById('notification-area') || document.body;
        
        // Create notification element
        const notification = document.createElement('div');
        
        // Determine background color based on type
        let bgColorClass = 'bg-blue-500';
        switch(type) {
            case 'on':
            case 'success':
                bgColorClass = 'bg-green-600';
                break;
            case 'off':
            case 'error':
                bgColorClass = 'bg-red-600';
                break;
            case 'warning':
                bgColorClass = 'bg-yellow-500';
                break;
            default:
                bgColorClass = 'bg-blue-500';
        }
        
        // Set notification classes and styling
        if (container === document.body) {
            // Fixed positioning for body container (top-right)
            notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full text-white ${bgColorClass}`;
        } else {
            // Relative positioning for notification area container
            notification.className = `p-4 rounded-lg shadow-md text-white transition-all duration-300 ease-in-out mb-2 transform translate-y-full opacity-0 ${bgColorClass}`;
        }
        
        notification.textContent = message;
        container.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            if (container === document.body) {
                notification.classList.remove('translate-x-full');
            } else {
                notification.classList.remove('translate-y-full', 'opacity-0');
            }
        });
        
        // Auto remove after appropriate time
        const autoRemoveTime = container === document.body ? 3000 : 5000;
        setTimeout(() => {
            if (container === document.body) {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            } else {
                notification.classList.add('opacity-0');
                notification.addEventListener('transitionend', () => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                });
            }
        }, autoRemoveTime);
    },

    // Show loading notification
    showLoading(message = 'Loading...') {
        const loadingId = 'loading-notification';
        
        // Remove existing loading notification
        this.hideLoading();
        
        const notification = document.createElement('div');
        notification.id = loadingId;
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 bg-indigo-600 text-white flex items-center`;
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
