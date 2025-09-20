// main.js - Main application initialization and coordination
window.RelayApp = {
    // Initialize the entire application
    init() {
        console.log('Initializing Relay Control Panel...');
        
        // Initialize QR Scanner
        window.QRScanner.init();
        
        // Initialize event listeners
        window.EventListeners.init();
        
        // Load AI model
        window.AIMonitoring.loadModel();
        
        // Initial data fetch
        window.ApplianceAPI.fetchRoomsAndAppliances();

        try {
            const response = await fetch('/api/get-user-settings');
            if (response.ok) {
                const settings = await response.json();
                window.RelayConfig.userEmail = settings.email;
            }
        } catch (e) {
            console.warn("Could not fetch user settings. Email notifications may not work.");
        }
        
        // Set up periodic data refresh
        setInterval(() => {
            window.ApplianceAPI.fetchRoomsAndAppliances();
        }, 3000);
        
        console.log('Relay Control Panel initialized successfully');
    }
};

// Make global functions available for onclick handlers in HTML
window.showAppliances = window.RoomRenderer.showAppliances;
window.openRoomSettings = window.RoomSettings.openRoomSettings;
window.openApplianceSettings = window.ApplianceSettings.openApplianceSettings;
window.openTimerModal = window.TimerModal.openTimerModal;
window.openConfirmationModal = window.ConfirmationModal.openConfirmationModal;
window.toggleLock = window.ApplianceActions.toggleLock;
window.toggleMonitoring = window.AIMonitoring.toggleMonitoring;

// Initialize app when DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
    window.RelayApp.init();
});
