// modals.js - Modal management system
window.ConfirmationModal = {
    // Open universal confirmation modal
    openConfirmationModal(action, ...data) {
        const confirmationModal = document.getElementById('confirmation-modal');
        const confirmationTitle = document.getElementById('confirmation-title');
        const confirmationMessage = document.getElementById('confirmation-message');
        const confirmActionBtn = document.getElementById('confirm-action-btn');
        
        window.RelayConfig.currentAction = action;
        window.RelayConfig.currentData = data;
        
        // Set title and message based on action
        switch(action) {
            case 'delete-room':
                confirmationTitle.textContent = 'Delete Room';
                confirmationMessage.textContent = 'Are you sure you want to delete this room? This action cannot be undone and will also delete all appliances in this room.';
                confirmActionBtn.textContent = 'Delete Room';
                confirmActionBtn.className = 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors';
                break;
            case 'delete-appliance':
                confirmationTitle.textContent = 'Delete Appliance';
                confirmationMessage.textContent = 'Are you sure you want to delete this appliance? This action cannot be undone.';
                confirmActionBtn.textContent = 'Delete Appliance';
                confirmActionBtn.className = 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors';
                break;
            case 'cancel-timer':
                confirmationTitle.textContent = 'Cancel Timer';
                confirmationMessage.textContent = 'Are you sure you want to cancel the timer for this appliance?';
                confirmActionBtn.textContent = 'Cancel Timer';
                confirmActionBtn.className = 'px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors';
                break;
            default:
                confirmationTitle.textContent = 'Confirm Action';
                confirmationMessage.textContent = 'Are you sure you want to proceed?';
                confirmActionBtn.textContent = 'Confirm';
                confirmActionBtn.className = 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors';
        }
        
        confirmationModal.classList.remove('hidden');
    },

    // Handle confirmation action
    async handleConfirmation() {
        const confirmationModal = document.getElementById('confirmation-modal');
        confirmationModal.classList.add('hidden');
        
        if (window.RelayConfig.currentAction === 'delete-room') {
            const [roomId] = window.RelayConfig.currentData;
            try {
                const response = await window.ApplianceAPI.deleteRoom(roomId);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Room deleted successfully!', 'on');
                    window.ApplianceAPI.fetchRoomsAndAppliances();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to delete room.', 'off');
            }
        } else if (window.RelayConfig.currentAction === 'delete-appliance') {
            const [roomId, applianceId] = window.RelayConfig.currentData;
            try {
                const response = await window.ApplianceAPI.deleteAppliance(roomId, applianceId);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Appliance deleted successfully!', 'on');
                    window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', false);
                    window.ApplianceAPI.fetchRoomsAndAppliances();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to delete appliance.', 'off');
            }
        } else if (window.RelayConfig.currentAction === 'cancel-timer') {
            const [roomId, applianceId] = window.RelayConfig.currentData;
            try {
                const response = await window.ApplianceAPI.setTimer(roomId, applianceId, null);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Timer cancelled.', 'on');
                    window.ApplianceAPI.fetchRoomsAndAppliances();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to cancel timer.', 'off');
            }
        }
        
        window.RelayConfig.currentAction = null;
        window.RelayConfig.currentData = null;
    },

    // Cancel confirmation
    cancelConfirmation() {
        document.getElementById('confirmation-modal').classList.add('hidden');
        window.RelayConfig.currentAction = null;
        window.RelayConfig.currentData = null;
    }
};

window.RoomSettings = {
    // Open room settings modal
    openRoomSettings(roomId) {
        const room = window.RelayConfig.allRoomsData.find(r => r.id === roomId);
        if (!room) return;
        
        document.getElementById('edit-room-id').value = roomId;
        document.getElementById('edit-room-name').value = room.name;
        
        const aiControlSwitch = document.getElementById('ai-control-switch');
        aiControlSwitch.dataset.state = room.ai_control ? 'checked' : 'off';
        if (room.ai_control) {
            aiControlSwitch.classList.add('data-[state=checked]');
        } else {
            aiControlSwitch.classList.remove('data-[state=checked]');
        }
        
        window.DOMHelpers.toggleElementVisibility('settings-room-modal', true);
    },

    // Handle room settings form submission
    async handleRoomSettingsSubmit(e) {
        e.preventDefault();
        
        const submitButton = e.currentTarget.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        
        submitButton.disabled = true;
        submitButton.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>Saving...`;
        
        const roomId = document.getElementById('edit-room-id').value;
        const newName = document.getElementById('edit-room-name').value;
        const aiControl = document.getElementById('ai-control-switch').dataset.state === 'checked';
        
        try {
            const response = await window.ApplianceAPI.updateRoomSettings(roomId, newName, aiControl);
            
            if (response.ok) {
                window.NotificationSystem.showNotification('Room settings updated!', 'on');
                window.DOMHelpers.toggleElementVisibility('settings-room-modal', false);
                window.ApplianceAPI.fetchRoomsAndAppliances();
            } else {
                const result = await response.json();
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
            
        } catch (error) {
            console.error('Form submission failed:', error);
            window.NotificationSystem.showNotification('Failed to save room settings. Check your connection.', 'off');
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    }
};

window.ApplianceSettings = {
    // Open appliance settings modal
    openApplianceSettings(roomId, applianceId) {
        const room = window.RelayConfig.allRoomsData.find(r => r.id === roomId);
        if (!room) return;
        const appliance = room.appliances.find(a => a.id === applianceId);
        
        document.getElementById('settings-edit-room-id').value = roomId;
        document.getElementById('edit-appliance-id').value = applianceId;
        document.getElementById('edit-appliance-name').value = appliance.name;
        document.getElementById('edit-appliance-relay').value = appliance.relay_number;
        
        const roomSelector = document.getElementById('edit-room-selector');
        roomSelector.innerHTML = '';
        window.RelayConfig.allRoomsData.forEach(r => {
            const option = document.createElement('option');
            option.value = r.id;
            option.textContent = r.name;
            if (r.id === roomId) {
                option.selected = true;
            }
            roomSelector.appendChild(option);
        });
        
        const advancedSettingsToggle = document.querySelector('.advanced-settings-toggle');
        const advancedSettings = document.getElementById('advanced-settings');
        advancedSettingsToggle.onclick = () => {
            advancedSettings.classList.toggle('hidden');
        };

        window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', true);
    },

    // Handle appliance settings form submission
    async handleApplianceSettingsSubmit(e) {
        e.preventDefault();
        const roomId = document.getElementById('settings-edit-room-id').value;
        const applianceId = document.getElementById('edit-appliance-id').value;
        const newName = document.getElementById('edit-appliance-name').value;
        const newRelay = document.getElementById('edit-appliance-relay').value;
        const newRoomId = document.getElementById('edit-room-selector').value;
        
        try {
            const response = await window.ApplianceAPI.updateApplianceSettings(roomId, applianceId, newName, newRelay, newRoomId);
            const result = await response.json();
            if (response.ok) {
                window.NotificationSystem.showNotification('Appliance settings updated!', 'on');
                window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', false);
                window.ApplianceAPI.fetchRoomsAndAppliances();
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to save settings.', 'off');
        }
    }
};

window.TimerModal = {
    // Open timer modal
    openTimerModal(roomId, applianceId) {
        document.getElementById('timer-room-id').value = roomId;
        document.getElementById('timer-appliance-id').value = applianceId;
        window.DOMHelpers.toggleElementVisibility('timer-modal', true);
    },

    // Handle timer form submission
    async handleTimerSubmit(e) {
        e.preventDefault();
        const roomId = document.getElementById('timer-room-id').value;
        const applianceId = document.getElementById('timer-appliance-id').value;
        
        let timerTimestamp = null;
        const hours = parseInt(document.getElementById('timer-duration-hours').value) || 0;
        const minutes = parseInt(document.getElementById('timer-duration-minutes').value) || 0;
        const datetimeInput = document.getElementById('timer-datetime').value;

        if (hours > 0 || minutes > 0) {
            const timerDurationMinutes = hours * 60 + minutes;
            if (timerDurationMinutes > 0) {
                timerTimestamp = Math.floor(Date.now() / 1000) + timerDurationMinutes * 60;
            }
        } else if (datetimeInput) {
            const futureDate = new Date(datetimeInput);
            if (futureDate.getTime() > Date.now()) {
                timerTimestamp = Math.floor(futureDate.getTime() / 1000);
            }
        }

        if (timerTimestamp) {
            try {
                const response = await window.ApplianceAPI.setTimer(roomId, applianceId, timerTimestamp);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Timer set successfully!', 'on');
                    window.DOMHelpers.toggleElementVisibility('timer-modal', false);
                    window.ApplianceAPI.fetchRoomsAndAppliances();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to set timer.', 'off');
            }
        } else {
            window.NotificationSystem.showNotification('Please set a valid future time or duration.', 'off');
        }
    }
};
