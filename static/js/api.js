// api.js - All API communication functions
window.ApplianceAPI = {
    // Fetches both rooms and boards owned by the user
    async fetchDashboardData() {
        try {
            const [roomsResponse, boardsResponse] = await Promise.all([
                fetch('/api/get-rooms-and-appliances'),
                fetch('/api/my-boards')
            ]);
            if (!roomsResponse.ok || !boardsResponse.ok) throw new Error('Failed to fetch dashboard data');
            
            const rooms = await roomsResponse.json();
            const boards = await boardsResponse.json();
            
            window.RelayConfig.allRoomsData = rooms;
            window.RelayConfig.allBoardsData = boards;
            
            window.RoomRenderer.renderRooms(rooms);
            window.RoomRenderer.renderBoards(boards);
            
            if (window.RelayConfig.currentRoomId) {
                const room = rooms.find(r => r.id === window.RelayConfig.currentRoomId);
                if (room) {
                    window.ApplianceRenderer.renderAppliances(room.appliances, room.name);
                } else {
                    window.RoomRenderer.backToRooms();
                }
            }
        } catch (error) {
            console.error('Error fetching data:', error);
            window.NotificationSystem.showNotification('Failed to load data.', 'error');
        }
    },

    // Fetch rooms and appliances data (legacy method)
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
    
    // Board management
    async registerBoard(roomId, boardId) {
        return await fetch('/api/register-board', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, board_id: boardId })
        });
    },

    async unregisterBoard(boardId) {
        return await fetch('/api/unregister-board', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ board_id: boardId })
        });
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
    
    async getAvailableRelays(roomId) {
        return await fetch(`/api/available-relays/${roomId}`);
    },

    // Appliance state management
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
            return response;
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to send command.', 'off');
            throw error;
        }
    },

    // Room management
    async addRoom(roomName) {
        return await fetch('/api/add-room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: roomName })
        });
    },

    async deleteRoom(roomId) {
        return await fetch('/api/delete-room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId })
        });
    },

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

    // Appliance management
    async addAppliance(roomId, name, boardId, relayId) {
        return await fetch('/api/add-appliance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                room_id: roomId, 
                name: name, 
                board_id: boardId, 
                relay_id: relayId 
            })
        });
    },

    async deleteAppliance(roomId, applianceId) {
         return await fetch('/api/delete-appliance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, appliance_id: applianceId })
        });
    },
    
    async updateApplianceSettings(roomId, applianceId, name, boardId, relayId, newRoomId) {
        return await fetch('/api/update-appliance-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                room_id: roomId, 
                appliance_id: applianceId, 
                name: name, 
                board_id: boardId, 
                relay_id: relayId, 
                new_room_id: newRoomId 
            })
        });
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

    // Timer and lock management
    async setTimer(roomId, applianceId, timer) {
        const response = await fetch('/api/set-timer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, appliance_id: applianceId, timer: timer })
        });
        return response;
    },

    async setLock(roomId, applianceId, locked) {
        const response = await fetch('/api/set-lock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ room_id: roomId, appliance_id: applianceId, locked: locked })
        });
        return response;
    },

    // AI detection and control
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

    async setGlobalAIControl(state) {
        const response = await fetch('/api/set-global-ai-control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: state })
        });
        return response;
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
    }
};
