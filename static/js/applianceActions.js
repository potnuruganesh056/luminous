// applianceActions.js - Appliance action functions
window.ApplianceActions = {
    // Toggle appliance lock state
    async toggleLock(roomId, applianceId) {
        try {
            const response = await window.ApplianceAPI.fetchRoomsAndAppliances();
            const rooms = window.RelayConfig.allRoomsData;
            const appliance = rooms.find(r => r.id === roomId).appliances.find(a => a.id === applianceId);
            const newState = !appliance.locked;

            const lockResponse = await window.ApplianceAPI.setLock(roomId, applianceId, newState);
            const result = await lockResponse.json();
            if (lockResponse.ok) {
                window.NotificationSystem.showNotification(`Appliance is now ${newState ? 'locked' : 'unlocked'}.`, 'on');
                window.ApplianceAPI.fetchRoomsAndAppliances();
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to update lock state.', 'off');
        }
    },

    // Save appliance name
    async saveApplianceName(inputElement) {
        const roomId = window.RelayConfig.currentRoomId;
        const applianceId = inputElement.dataset.applianceId;
        const newName = inputElement.value;

        if (newName === "") {
            inputElement.value = "Unnamed Appliance";
            window.NotificationSystem.showNotification("Appliance name cannot be empty.", "off");
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
                window.NotificationSystem.showNotification(`Appliance name updated to "${newName}".`, 'on');
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to update appliance name.', 'off');
        } finally {
            inputElement.disabled = true;
        }
    },

    // Handle add appliance button click
    async handleAddAppliance() {
        window.DOMHelpers.toggleElementVisibility('add-appliance-modal', true);
        try {
            const response = await window.ApplianceAPI.getAvailableRelays(window.RelayConfig.currentRoomId);
            if (!response.ok) throw new Error('Failed to fetch relays');
            const availableRelays = await response.json();
            
            const relaySelect = document.getElementById('new-appliance-relay');
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
            window.NotificationSystem.showNotification('Could not load available relays.', 'off');
        }
    },

    // Handle add appliance form submission
    async handleAddApplianceSubmit(e) {
        e.preventDefault();
        const applianceName = document.getElementById('new-appliance-name').value;
        const relayNumber = document.getElementById('new-appliance-relay').value;
        
        try {
            const response = await window.ApplianceAPI.addAppliance(window.RelayConfig.currentRoomId, applianceName, relayNumber);
            const result = await response.json();
            if (response.ok) {
                window.DOMHelpers.toggleElementVisibility('add-appliance-modal', false);
                window.ApplianceAPI.fetchRoomsAndAppliances();
                window.NotificationSystem.showNotification('Appliance added successfully!', 'on');
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to add appliance.', 'off');
        }
    }
};

window.RoomActions = {
    // Handle add room form submission
    async handleAddRoomSubmit(e) {
        e.preventDefault();
        const roomName = document.getElementById('new-room-name').value;
        
        try {
            const response = await window.ApplianceAPI.addRoom(roomName);
            const result = await response.json();
            if (response.ok) {
                window.DOMHelpers.toggleElementVisibility('add-room-modal', false);
                window.ApplianceAPI.fetchRoomsAndAppliances();
                window.NotificationSystem.showNotification('Room added successfully!', 'on');
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to add room.', 'off');
        }
    }
};
