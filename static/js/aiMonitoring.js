// aiMonitoring.js - AI monitoring and human detection system
window.AIMonitoring = {
    // Load AI model
    async loadModel() {
        if (window.RelayConfig.model || window.RelayConfig.modelLoaded) return;
        try {
            window.NotificationSystem.showNotification('Loading AI model...', 'on');
            window.RelayConfig.model = await cocoSsd.load();
            window.RelayConfig.modelLoaded = true;
            window.NotificationSystem.showNotification('AI model loaded successfully.', 'on');
            console.log('AI model loaded successfully.');
        } catch (error) {
            console.error('Failed to load model:', error);
            window.NotificationSystem.showNotification('Failed to load AI model.', 'off');
        }
    },

    // Detect humans in video stream
    async detectHumans(roomId) {
        // Global monitoring case
        if (!roomId && window.RelayConfig.isGlobalMonitoringActive) {
            if (!window.RelayConfig.isMonitoring || !window.RelayConfig.model) return;
            
            const videoElement = window.RelayConfig.monitoringVideoElement;
            if (!videoElement.srcObject || videoElement.paused) {
                console.log("Global monitoring stream not available, stopping detection.");
                this.toggleGlobalMonitoring();
                return;
            }
            
            const canvas = document.createElement('canvas');
            canvas.width = video
