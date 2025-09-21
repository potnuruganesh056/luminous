// applianceActions.js - Appliance action functions and form handlers
window.ApplianceActions = {
    // Toggle appliance lock state
    async toggleLock(roomId, applianceId) {
        try {
            const rooms = window.RelayConfig.allRoomsData;
            const room = rooms.find(r => r.id === roomId);
            if (!room) {
                window.NotificationSystem.showNotification('Room not found.', 'error');
                return;
            }
            
            const appliance = room.appliances.find(a => a.id === applianceId);
            if (!appliance) {
                window.NotificationSystem.showNotification('Appliance not found.', 'error');
                return;
            }
            
            const newState = !appliance.locked;

            const lockResponse = await window.ApplianceAPI.setLock(roomId, applianceId, newState);
            const result = await lockResponse.json();
            if (lockResponse.ok) {
                window.NotificationSystem.showNotification(`Appliance is now ${newState ? 'locked' : 'unlocked'}.`, 'success');
                
                // Update lock icon immediately for better UX
                const lockIcon = document.getElementById(`lock-icon-${applianceId}`);
                if (lockIcon) {
                    lockIcon.className = `h-4 w-4 fas ${newState ? 'fa-lock text-red-500' : 'fa-unlock text-gray-400'}`;
                }
                
                window.ApplianceAPI.fetchDashboardData();
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to update lock state.', 'error');
        }
    },

    // Save appliance name (legacy function)
    async saveApplianceName(inputElement) {
        const roomId = window.RelayConfig.currentRoomId;
        const applianceId = inputElement.dataset.applianceId;
        const newName = inputElement.value;

        if (newName === "") {
            inputElement.value = "Unnamed Appliance";
            window.NotificationSystem.showNotification("Appliance name cannot be empty.", "error");
            return;
        }

        try {
            const response = await fetch('/api/set-appliance-name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_id: roomId, appliance_id: applianceId, name: newName })
            });
            const result = await response.json();
            if (response.ok) {
                window.NotificationSystem.showNotification(`Appliance name updated to "${newName}".`, 'success');
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to update appliance name.', 'error');
        } finally {
            inputElement.disabled = true;
        }
    },

    // Handle add appliance button click (legacy method)
    async handleAddAppliance() {
        window.DOMHelpers.toggleElementVisibility('add-appliance-modal', true);
        try {
            const response = await window.ApplianceAPI.getAvailableRelays(window.RelayConfig.currentRoomId);
            if (!response.ok) throw new Error('Failed to fetch relays');
            const availableRelays = await response.json();
            
            const relaySelect = document.getElementById('new-appliance-relay');
            if (!relaySelect) return;
            
            relaySelect.innerHTML = '<option value="" disabled selected>Select an available relay</option>';

            if (availableRelays.length === 0) {
                relaySelect.innerHTML += '<option value="" disabled>No available relays in this room</option>';
                return;
            }

            availableRelays.forEach(board => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = `Board ${board.board_id.substring(0, 6)}...`;
                board.relays.forEach(relay => {
                    const option = document.createElement('option');
                    option.value = `${board.board_id}-${relay.id}`;
                    option.textContent = relay.name;
                    optgroup.appendChild(option);
                });
                relaySelect.appendChild(optgroup);
            });

        } catch (error) {
            console.error("Failed to fetch available relays", error);
            window.NotificationSystem.showNotification('Could not load available relays.', 'error');
        }
    },

    // Modern add appliance form submission handler
    async handleAddApplianceSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const name = form.querySelector('#new-appliance-name').value;
        const boardSelector = form.querySelector('#board-selector');
        const relaySelector = form.querySelector('#relay-selector');
        const roomId = window.RelayConfig.currentRoomId;

        // Handle both modern board/relay selectors and legacy relay selector
        let boardId, relayId;
        
        if (boardSelector && relaySelector) {
            // Modern system
            boardId = boardSelector.value;
            relayId = relaySelector.value;
        } else {
            // Legacy system - extract from combined value
            const legacyRelaySelect = form.querySelector('#new-appliance-relay');
            if (legacyRelaySelect && legacyRelaySelect.value) {
                const [extractedBoardId, extractedRelayId] = legacyRelaySelect.value.split('-');
                boardId = extractedBoardId;
                relayId = extractedRelayId;
            }
        }

        if (!roomId || !name || !boardId || !relayId) {
            window.NotificationSystem.showNotification('All fields are required.', 'error');
            return;
        }

        try {
            const response = await window.ApplianceAPI.addAppliance(roomId, name, boardId, relayId);
            const result = await response.json();

            if (response.ok) {
                window.NotificationSystem.showNotification('Appliance added successfully!', 'success');
                window.DOMHelpers.toggleElementVisibility('add-appliance-modal', false);
                window.ApplianceAPI.fetchDashboardData();
            } else {
                window.NotificationSystem.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to add appliance.', 'error');
        }
    },
    
    // Handle board registration form submission
    async handleRegisterBoardSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const roomId = form.querySelector('#register-board-room-id').value;
        const boardId = form.querySelector('#board-id-manual').value;

        if (!roomId || !boardId) {
            window.NotificationSystem.showNotification('Room and Board ID are required.', 'error');
            return;
        }
        
        try {
            const response = await window.ApplianceAPI.registerBoard(roomId, boardId);
            const result = await response.json();

            if (response.ok) {
                window.NotificationSystem.showNotification(result.message, 'success');
                window.DOMHelpers.toggleElementVisibility('register-board-modal', false);
                window.ApplianceAPI.fetchDashboardData();
            } else {
                window.NotificationSystem.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to register board.', 'error');
        }
    }
};

window.RoomActions = {
    // Handle add room form submission
    async handleAddRoomSubmit(e) {
        e.preventDefault();
        const roomName = document.getElementById('new-room-name').value;
        
        if (!roomName.trim()) {
            window.NotificationSystem.showNotification('Room name is required.', 'error');
            return;
        }
        
        try {
            const response = await window.ApplianceAPI.addRoom(roomName);
            const result = await response.json();
            if (response.ok) {
                window.DOMHelpers.toggleElementVisibility('add-room-modal', false);
                window.ApplianceAPI.fetchDashboardData();
                window.NotificationSystem.showNotification('Room added successfully!', 'success');
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to add room.', 'error');
        }
    }
};
