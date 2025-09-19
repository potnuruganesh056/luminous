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

    // Toggle global monitoring
    async toggleGlobalMonitoring() {
        const button = document.getElementById('global-start-monitoring-btn');
        
        // Stop global monitoring
        if (window.RelayConfig.isGlobalMonitoringActive) {
            window.RelayConfig.isGlobalMonitoringActive = false;
            window.RelayConfig.isMonitoring = false;
            if (window.RelayConfig.monitoringIntervalId) clearTimeout(window.RelayConfig.monitoringIntervalId);
            if (window.RelayConfig.monitoringStream) window.RelayConfig.monitoringStream.getTracks().forEach(track => track.stop());
            window.RelayConfig.monitoringStream = null;
            
            if (button) {
                button.innerHTML = '<i class="fas fa-eye mr-2"></i>Start Global Monitoring';
                button.classList.remove('monitoring-active-btn');
            }
            window.DOMHelpers.toggleElementVisibility('global-monitoring-card', false);
            window.NotificationSystem.showNotification('Global AI monitoring stopped.', 'on');
            window.ApplianceAPI.fetchRoomsAndAppliances();
            return;
        }

        // Start global monitoring
        try {
            // Shut down all active per-room monitors first
            if (window.RelayConfig.activeMonitors.size > 0) {
                console.log(`Overriding ${window.RelayConfig.activeMonitors.size} active room monitors...`);
                window.NotificationSystem.showNotification('Stopping all per-room monitors to start global session.', 'on');
                
                for (const [roomId, monitor] of window.RelayConfig.activeMonitors.entries()) {
                    if (monitor.isRunning) {
                        monitor.isRunning = false;
                        if (monitor.intervalId) clearTimeout(monitor.intervalId);
                        if (monitor.stream) monitor.stream.getTracks().forEach(track => track.stop());
                        if (monitor.videoElement) monitor.videoElement.remove();
                        
                        await window.ApplianceAPI.updateRoomSettings(roomId, null, false);
                    }
                }
                window.RelayConfig.activeMonitors.clear();
            }
            
            if (!window.RelayConfig.model) await this.loadModel();
            if (!window.RelayConfig.model) return;

            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            window.RelayConfig.monitoringStream = stream;
            window.RelayConfig.monitoringVideoElement.srcObject = stream;
            
            await new Promise(resolve => {
                window.RelayConfig.monitoringVideoElement.onloadedmetadata = () => {
                    resolve();
                };
            });
            
            await window.RelayConfig.monitoringVideoElement.play();

            window.RelayConfig.isGlobalMonitoringActive = true;
            window.RelayConfig.isMonitoring = true;
            
            if (button) {
                button.innerHTML = '<i class="fas fa-video-slash mr-2"></i>Stop Global Monitoring';
                button.classList.add('monitoring-active-btn');
            }
            window.DOMHelpers.toggleElementVisibility('global-monitoring-card', true);
            window.NotificationSystem.showNotification('Global AI monitoring started.', 'on');
            
            this.detectHumans();
            window.ApplianceAPI.fetchRoomsAndAppliances();

        } catch (err) {
            window.NotificationSystem.showNotification('Failed to start global monitoring. Check camera permissions.', 'off');
            console.error(err);
            window.RelayConfig.isGlobalMonitoringActive = false;
            window.RelayConfig.isMonitoring = false;
            if (button) {
                button.innerHTML = '<i class="fas fa-eye mr-2"></i>Start Global Monitoring';
                button.classList.remove('monitoring-active-btn');
            }
        }
    },

    // Toggle monitoring for specific room or scope
    async toggleMonitoring(scope) {
        if (!window.RelayConfig.modelLoaded) {
            window.RelayConfig.pendingGlobalAction = scope;
            window.NotificationSystem.showNotification('AI Model is loading, please wait...', 'on');
            this.loadModel();
            return;
        }

        const isGlobal = scope === 'global';
        const monitor = window.RelayConfig.activeMonitors.get(scope);
        
        // Stop monitoring session
        if (monitor && monitor.isRunning) {
            monitor.isRunning = false;
            if (monitor.intervalId) clearTimeout(monitor.intervalId);
            if (monitor.stream) monitor.stream.getTracks().forEach(track => track.stop());
            if (monitor.videoElement) monitor.videoElement.remove();
            window.RelayConfig.activeMonitors.delete(scope);

            const name = isGlobal ? 'Global' : window.RelayConfig.allRoomsData.find(r => r.id === scope)?.name || 'Room';
            window.NotificationSystem.showNotification(`AI monitoring stopped for ${name}.`, 'on');

            // Update backend state
            if (isGlobal) {
                await window.ApplianceAPI.setGlobalAIControl(false);
            } else {
                await window.ApplianceAPI.updateRoomSettings(scope, null, false);
            }
            
            window.ApplianceAPI.fetchRoomsAndAppliances();
            return;
        }

        // Start new monitoring session
        try {
            // Prevent conflicts between global and per-room monitoring
            if (isGlobal && window.RelayConfig.activeMonitors.size > 0) {
                window.NotificationSystem.showNotification('Please stop all active room monitors before starting global monitoring.', 'warning');
                return;
            }
            if (!isGlobal && window.RelayConfig.activeMonitors.has('global')) {
                window.NotificationSystem.showNotification('Global monitoring is active. Stop it to control individual rooms.', 'warning');
                return;
            }

            // Get camera stream and prepare video element
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const videoElement = document.createElement('video');
            videoElement.srcObject = stream;
            videoElement.style.display = 'none';
            document.body.appendChild(videoElement);

            await new Promise((resolve, reject) => {
                videoElement.onloadedmetadata = resolve;
                setTimeout(() => reject(new Error("Video load timeout")), 5000);
            });
            await videoElement.play();

            // Create a new monitor object
            const newMonitor = {
                stream, videoElement, isRunning: true,
                intervalId: null, lastEmailTime: null
            };
            window.RelayConfig.activeMonitors.set(scope, newMonitor);

            const name = isGlobal ? 'Global' : window.RelayConfig.allRoomsData.find(r => r.id === scope)?.name || 'Room';
            window.NotificationSystem.showNotification(`AI monitoring started for ${name}.`, 'on');
            
            // Update backend state
            if (isGlobal) {
                await window.ApplianceAPI.setGlobalAIControl(true);
            } else {
                await window.ApplianceAPI.updateRoomSettings(scope, null, true);
            }

            this.detectHumans(scope);
            window.ApplianceAPI.fetchRoomsAndAppliances();
            
        } catch (err) {
            const name = isGlobal ? 'Global' : window.RelayConfig.allRoomsData.find(r => r.id === scope)?.name || 'Room';
            window.NotificationSystem.showNotification(`Failed to start monitoring for ${name}. Check camera permissions.`, 'off');
            console.error(`Monitoring Error for scope "${scope}":`, err);
        }
    }
};

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
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            
            try {
                const predictions = await window.RelayConfig.model.detect(canvas);
                const humanDetections = predictions.filter(p => p.class === 'person');
                const humanDetected = predictions.some(p => p.class === 'person');
                const statusElement = document.getElementById('global-monitoring-status');
                
                if (statusElement) {
                    statusElement.textContent = humanDetected ? 'Human detected! Controlling all appliances.' : 'No human detected. Awaiting...';
                }
                
                await window.ApplianceAPI.sendGlobalAISignal(humanDetected);
                
                // Global email alerts - rate-limited to once every 10 minutes
                if (!window.globalLastEmailTime) {
                    window.globalLastEmailTime = null;
                }
                
                if (humanDetected && (window.globalLastEmailTime === null || (Date.now() - window.globalLastEmailTime) > 600000)) {
                    console.log("Global email time threshold passed. Sending alert...");
                    await this.sendDetectionAlert(videoElement, humanDetections, 'Global Monitoring', 'global', true);
                    window.globalLastEmailTime = Date.now();
                }
                
            } catch (error) {
                console.error("Error during global detection:", error);
            }
            
            // Reschedule the global loop
            if (window.RelayConfig.isGlobalMonitoringActive) {
                window.RelayConfig.monitoringIntervalId = setTimeout(() => this.detectHumans(), window.RelayConfig.aiControlInterval);
            }
            return;
        }
        
        // Per-room monitoring case
        if (roomId) {
            const monitor = window.RelayConfig.activeMonitors.get(roomId);
            if (!monitor || !monitor.isRunning) return;
            
            const videoElement = monitor.videoElement;
            if (!videoElement.srcObject || videoElement.paused) {
                console.error(`Stream for room ${roomId} is not available. Stopping monitor.`);
                this.toggleMonitoring(roomId);
                return;
            }
            
            const canvas = document.createElement('canvas');
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            
            try {
                const predictions = await window.RelayConfig.model.detect(canvas);
                const humanDetections = predictions.filter(p => p.class === 'person');
                const humanDetected = predictions.some(p => p.class === 'person');
                
                await window.ApplianceAPI.sendAIDetectionSignal(roomId, humanDetected);
                
                if (roomId === window.RelayConfig.currentRoomId) {
                    const currentRoom = window.RelayConfig.allRoomsData.find(r => r.id === roomId);
                    const roomName = currentRoom ? currentRoom.name : 'Unknown Room';
                    const statusElement = document.getElementById('monitoring-status');
                    
                    if (statusElement) {
                        if (humanDetected) {
                            statusElement.textContent = `Human detected in ${roomName}! AI is in control.`;
                        } else {
                            statusElement.textContent = `No human detected in ${roomName}. Awaiting...`;
                        }
                    }
                }
                
                // Rate-limit email alerts to once every 10 minutes per room
                if (!monitor.lastEmailTime) {
                    monitor.lastEmailTime = null;
                }
                
                if (humanDetected && (monitor.lastEmailTime === null || (Date.now() - monitor.lastEmailTime) > 600000)) {
                    const currentRoom = window.RelayConfig.allRoomsData.find(r => r.id === roomId);
                    const roomName = currentRoom ? currentRoom.name : 'Unknown Room';
                    
                    await this.sendDetectionAlert(videoElement, humanDetections, roomName, roomId, false);
                    monitor.lastEmailTime = Date.now();
                }
                
            } catch (error) {
                console.error(`Error during detection for room ${roomId}:`, error);
                
                if (roomId === window.RelayConfig.currentRoomId) {
                    const statusElement = document.getElementById('monitoring-status');
                    if (statusElement) {
                        statusElement.textContent = 'Error during detection.';
                    }
                }
            }
            
            // Reschedule the loop for this specific room
            if (monitor.isRunning) {
                monitor.intervalId = setTimeout(() => this.detectHumans(roomId), window.RelayConfig.aiControlInterval);
            }
        }
    },

    // Send detection alert email with image
    async sendDetectionAlert(videoElement, humanDetections, roomName, roomId, isGlobal) {
        try {
            const alertWidth = 640;
            const alertHeight = 360;
            const alertCanvas = document.createElement('canvas');
            alertCanvas.width = alertWidth;
            alertCanvas.height = alertHeight;
            const alertCtx = alertCanvas.getContext('2d');
            
            // Draw the video frame, scaling it down to the smaller canvas size
            alertCtx.drawImage(videoElement, 0, 0, alertWidth, alertHeight);
            
            // Draw bounding boxes around each detected person
            alertCtx.strokeStyle = 'red';
            alertCtx.lineWidth = 2;
            alertCtx.font = '14px Arial';
            
            humanDetections.forEach((detection, index) => {
                const scaleX = alertWidth / videoElement.videoWidth;
                const scaleY = alertHeight / videoElement.videoHeight;
                const [x, y, width, height] = detection.bbox;
                const scaledX = x * scaleX;
                const scaledY = y * scaleY;
                const scaledWidth = width * scaleX;
                const scaledHeight = height * scaleY;
                
                // Draw the rectangle
                alertCtx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);
                
                // Add confidence score label
                const confidence = Math.round(detection.score * 100);
                const label = `Person ${confidence}%`;
                
                // Draw label background
                const textMetrics = alertCtx.measureText(label);
                alertCtx.fillStyle = 'red';
                alertCtx.fillRect(scaledX, Math.max(scaledY - 18, 0), textMetrics.width + 6, 18);
                
                // Draw label text
                alertCtx.fillStyle = 'white';
                alertCtx.fillText(label, scaledX + 3, Math.max(scaledY - 3, 15));
            });
            
            const imageData = alertCanvas.toDataURL('image/jpeg', 0.8);
            
            if (imageData && imageData.length > 100) {
                await window.ApplianceAPI.sendDetectionEmail(imageData, roomName, roomId, isGlobal);
                console.log(`Detection email sent successfully for ${isGlobal ? 'global' : `room ${roomId}`}`);
            } else {
                console.error(`Invalid image data for email in ${isGlobal ? 'global' : `room ${roomId}`}`);
            }
        } catch (emailError) {
            console.error(`Failed to send detection email:`, emailError);
        }
    },
