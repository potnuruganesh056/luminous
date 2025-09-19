// webcam.js - Webcam and camera management
window.WebcamManager = {
    // Toggle global webcam
    async toggleGlobalWebcam() {
        const webcamContainer = document.getElementById('global-webcam-container') || document.getElementById('webcam-card-container');
        const videoElement = document.getElementById('global-webcam-video') || document.getElementById('webcam-video-live');
        const button = document.getElementById('global-open-webcam-btn');
        
        const currentStream = window.RelayConfig.webcamStream || window.RelayConfig.globalWebcamStream;
        
        if (currentStream) {
            // Stop webcam
            currentStream.getTracks().forEach(track => track.stop());
            
            window.RelayConfig.webcamStream = null;
            window.RelayConfig.globalWebcamStream = null;
            
            if (videoElement) {
                videoElement.srcObject = null;
            }
            
            if (webcamContainer) {
                webcamContainer.classList.add('hidden');
                webcamContainer.removeAttribute('data-global');
            }
            
            if (button) {
                button.innerHTML = '<i class="fas fa-camera mr-2"></i>Open Webcam';
            }
            
            window.NotificationSystem.showNotification('Global webcam closed.', 'on');
            
        } else {
            // Start webcam
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                
                window.RelayConfig.webcamStream = stream;
                window.RelayConfig.globalWebcamStream = stream;
                
                if (!videoElement) {
                    throw new Error('Webcam video element not found');
                }
                
                videoElement.srcObject = stream;
                
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(new Error('Video metadata loading timeout'));
                    }, 5000);
                    
                    videoElement.onloadedmetadata = () => {
                        clearTimeout(timeout);
                        resolve();
                    };
                    
                    if (videoElement.readyState >= 1) {
                        clearTimeout(timeout);
                        resolve();
                    }
                });
                
                if (webcamContainer) {
                    webcamContainer.classList.remove('hidden');
                    webcamContainer.setAttribute('data-global', 'true');
                }
                
                if (button) {
                    button.innerHTML = '<i class="fas fa-video-slash mr-2"></i>Close Webcam';
                }
                
                window.NotificationSystem.showNotification('Global webcam opened.', 'on');
                
            } catch (err) {
                console.error("Error accessing webcam:", err);
                
                let errorMessage = 'Failed to access webcam. Please check permissions.';
                if (err.name === 'NotAllowedError') {
                    errorMessage = 'Camera permission denied.';
                } else if (err.name === 'NotFoundError') {
                    errorMessage = 'No camera device found.';
                } else if (err.name === 'NotReadableError') {
                    errorMessage = 'Camera is already in use by another application.';
                } else if (err.message.includes('not found')) {
                    errorMessage = 'Webcam video element not found in the page.';
                } else if (err.message.includes('timeout')) {
                    errorMessage = 'Camera initialization timeout. Please try again.';
                }
                
                window.NotificationSystem.showNotification(errorMessage, 'off');
                
                // Clean up on error
                if (window.RelayConfig.webcamStream) {
                    window.RelayConfig.webcamStream.getTracks().forEach(track => track.stop());
                    window.RelayConfig.webcamStream = null;
                }
                if (window.RelayConfig.globalWebcamStream) {
                    window.RelayConfig.globalWebcamStream.getTracks().forEach(track => track.stop());
                    window.RelayConfig.globalWebcamStream = null;
                }
                
                if (webcamContainer) {
                    webcamContainer.classList.add('hidden');
                    webcamContainer.removeAttribute('data-global');
                }
                if (button) {
                    button.innerHTML = '<i class="fas fa-camera mr-2"></i>Open Webcam';
                }
            }
        }
    },

    // Toggle regular webcam
    async toggleWebcam() {
        const liveWebcamVideo = document.getElementById('webcam-video-live');
        const webcamCardContainer = document.getElementById('webcam-card-container');
        const webcamBtn = document.getElementById('open-webcam-btn');
        
        if (window.RelayConfig.webcamStream) {
            // Stop webcam
            window.RelayConfig.webcamStream.getTracks().forEach(track => track.stop());
            window.RelayConfig.webcamStream = null;
            
            if (liveWebcamVideo) {
                liveWebcamVideo.srcObject = null;
            }
            
            if (webcamCardContainer) {
                webcamCardContainer.classList.add('hidden');
            }
            if (webcamBtn) {
                webcamBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Open Webcam';
            }
            window.NotificationSystem.showNotification('Webcam turned off.', 'on');
            
        } else {
            // Start webcam
            try {
                let videoConstraints = { video: true };
                
                try {
                    videoConstraints = {
                        video: {
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        }
                    };
                    
                    const stream = await navigator.mediaDevices.getUserMedia(videoConstraints);
                    window.RelayConfig.webcamStream = stream;
                } catch (qualityError) {
                    console.warn('High quality video failed, falling back to basic video:', qualityError);
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    window.RelayConfig.webcamStream = stream;
                }
                
                if (!liveWebcamVideo) {
                    console.error('Live webcam video element not found');
                    window.NotificationSystem.showNotification('Webcam video element not found.', 'off');
                    window.RelayConfig.webcamStream.getTracks().forEach(track => track.stop());
                    window.RelayConfig.webcamStream = null;
                    return;
                }
                
                liveWebcamVideo.srcObject = window.RelayConfig.webcamStream;
                
                try {
                    await new Promise((resolve, reject) => {
                        const timeoutId = setTimeout(() => {
                            reject(new Error('Video load timeout'));
                        }, 5000);
                        
                        liveWebcamVideo.onloadedmetadata = () => {
                            clearTimeout(timeoutId);
                            resolve();
                        };
                        
                        liveWebcamVideo.onerror = (err) => {
                            clearTimeout(timeoutId);
                            reject(err);
                        };
                    });
                } catch (loadError) {
                    console.warn('Video metadata loading failed, proceeding anyway:', loadError);
                }
                
                if (webcamCardContainer) {
                    webcamCardContainer.classList.remove('hidden');
                }
                if (webcamBtn) {
                    webcamBtn.innerHTML = '<i class="fas fa-video-slash mr-2"></i>Close Webcam';
                }
                window.NotificationSystem.showNotification('Webcam turned on.', 'on');
                
            } catch (err) {
                console.error("Error accessing webcam:", err);
                
                let errorMessage = 'Failed to access webcam.';
                if (err.name === 'NotAllowedError') {
                    errorMessage = 'Camera permission denied. Please allow camera access.';
                } else if (err.name === 'NotFoundError') {
                    errorMessage = 'No camera found on this device.';
                } else if (err.name === 'NotReadableError') {
                    errorMessage = 'Camera is already in use by another application.';
                } else if (err.name === 'OverconstrainedError') {
                    errorMessage = 'Camera does not support requested quality. Please try again.';
                } else if (err.message === 'MediaDevices API not supported') {
                    errorMessage = 'Your browser does not support camera access.';
                } else if (err.message === 'Video load timeout') {
                    errorMessage = 'Camera took too long to initialize.';
                } else {
                    errorMessage = 'Failed to access webcam. Please check permissions.';
                }
                
                window.NotificationSystem.showNotification(errorMessage, 'off');
                
                if (window.RelayConfig.webcamStream) {
                    window.RelayConfig.webcamStream.getTracks().forEach(track => track.stop());
                    window.RelayConfig.webcamStream = null;
                }
            }
        }
    },

    // Stop all streams
    stopAllStreams() {
        if (window.RelayConfig.webcamStream) {
            window.RelayConfig.webcamStream.getTracks().forEach(track => track.stop());
            window.RelayConfig.webcamStream = null;
        }
        if (window.RelayConfig.globalWebcamStream) {
            window.RelayConfig.globalWebcamStream.getTracks().forEach(track => track.stop());
            window.RelayConfig.globalWebcamStream = null;
        }
        if (window.RelayConfig.isMonitoring) {
            window.RelayConfig.isMonitoring = false;
            if (window.RelayConfig.monitoringStream) {
                window.RelayConfig.monitoringStream.getTracks().forEach(track => track.stop());
                window.RelayConfig.monitoringStream = null;
            }
            if (window.RelayConfig.monitoringIntervalId) {
                clearTimeout(window.RelayConfig.monitoringIntervalId);
                window.RelayConfig.monitoringIntervalId = null;
            }
        }
    }
};
