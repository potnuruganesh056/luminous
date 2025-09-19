// api.js - API communication functions
window.ApplianceAPI = {
    // Fetch rooms and appliances data
    async fetchRoomsAndAppliances() {
        try {
            const roomContainer = document.getElementById('room-container');
            const roomsView = document.getElementById('rooms-view');
            const appliancesView = document.getElementById('appliances-view');
            
            if (!roomContainer || !roomsView || !appliancesView) {
                console.warn('Essential DOM elements not found, skipping fetch');
                return;
            }
            
            const response = await fetch('/api/get-rooms-and-appliances');
            if (!response.ok) {
                throw new Error('Failed to fetch rooms and appliances');
            }
            const rooms = await response.json();
            window.RelayConfig.allRoomsData = rooms;
            window.RoomRenderer.renderRooms(rooms);
            
            if (window.RelayConfig.currentRoomId) {
                const room = rooms.find(r => r.id === window.RelayConfig.currentRoomId);
                if (room) {
                    window.ApplianceRenderer.renderAppliances(room.appliances, room.name);
                } else {
                    window.RelayConfig.currentRoomId = null;
                    roomsView.classList.remove('hidden');
                    appliancesView.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('Error fetching data:', error);
            window.NotificationSystem.showNotification('Failed to load data.', 'off');
        }
    },

    // Send appliance state change
    async sendApplianceState(roomId, applianceId, state) {
        try {
            const response = await fetch('/api/set-appliance-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_id: roomId, appliance_id: applianceId, state: state })
            });
            const result = await response.json();
            if (response.ok) {
                window.NotificationSystem.showNotification(result.message, state ? 'on' : 'off');
                this.fetchRoomsAndAppliances();
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to send command.', 'off');
        }
    },

    // Save room order
    async saveNewRoomOrder(newOrder) {
        try {
            await fetch('/api/save-room-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order: newOrder })
            });
        } catch (error) {
            console.error("Failed to save new room order:", error);
        }
    },

    // Save appliance order
    async saveNewApplianceOrder(roomId, newOrder) {
        try {
            await fetch('/api/save-appliance-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_id: roomId, order: newOrder })
            });
        } catch (error) {
            console.error("Failed to save new appliance order:", error);
        }
    },

    // Update room settings
    async updateRoomSettings(roomId, name, aiControl) {
        const response = await fetch('/api/update-room-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                room_id: roomId, 
                name: name, 
                ai_control: aiControl 
            })
        });
        return response;
    },

    // Delete room
    async deleteRoom(roomId) {
        const response = await fetch('/api/delete-room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId })
        });
        return response;
    },

    // Add new room
    async addRoom(roomName) {
        const response = await fetch('/api/add-room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: roomName })
        });
        return response;
    },

    // Add new appliance
    async addAppliance(roomId, applianceName, relayNumber) {
        const response = await fetch('/api/add-appliance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, name: applianceName, relay_number: relayNumber })
        });
        return response;
    },

    // Update appliance settings
    async updateApplianceSettings(roomId, applianceId, name, relayNumber, newRoomId) {
        const response = await fetch('/api/update-appliance-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                room_id: roomId, 
                appliance_id: applianceId, 
                name: name, 
                relay_number: relayNumber, 
                new_room_id: newRoomId 
            })
        });
        return response;
    },

    // Delete appliance
    async deleteAppliance(roomId, applianceId) {
        const response = await fetch('/api/delete-appliance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, appliance_id: applianceId })
        });
        return response;
    },

    // Set timer
    async setTimer(roomId, applianceId, timer) {
        const response = await fetch('/api/set-timer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, appliance_id: applianceId, timer: timer })
        });
        return response;
    },

    // Set lock state
    async setLock(roomId, applianceId, locked) {
        const response = await fetch('/api/set-lock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, appliance_id: applianceId, locked: locked })
        });
        return response;
    },

    // Get available relays
    async getAvailableRelays(roomId) {
        const response = await fetch(`/api/available-relays/${roomId}`);
        return response;
    },

    // Add board via QR
    async addBoard(roomId, qrData) {
        const response = await fetch('/api/add-board', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, qr_data: qrData })
        });
        return response;
    },

    // AI detection signals
    async sendAIDetectionSignal(roomId, state) {
        await fetch('/api/ai-detection-signal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, state: state })
        });
    },

    async sendGlobalAISignal(state) {
        await fetch('/api/global-ai-signal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: state })
        });
    },

    // Send detection email
    async sendDetectionEmail(imageData, roomName, roomId, isGlobal) {
        await fetch('/api/send-detection-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_data: imageData,
                room_name: roomName,
                room_id: roomId,
                is_global: isGlobal
            })
        });
    },

    // Set global AI control
    async setGlobalAIControl(state) {
        const response = await fetch('/api/set-global-ai-control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: state })
        });
        return response;
    }
};
