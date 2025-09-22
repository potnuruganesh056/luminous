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
            case 'unregister-board':
                confirmationTitle.textContent = 'Unregister Board';
                confirmationMessage.textContent = 'Are you sure you want to unregister this board? Any appliances using this board will be disconnected.';
                confirmActionBtn.textContent = 'Unregister Board';
                confirmActionBtn.className = 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors';
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
                    window.NotificationSystem.showNotification('Room deleted successfully!', 'success');
                    window.ApplianceAPI.fetchDashboardData();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to delete room.', 'error');
            }
        } else if (window.RelayConfig.currentAction === 'delete-appliance') {
            const [roomId, applianceId] = window.RelayConfig.currentData;
            try {
                const response = await window.ApplianceAPI.deleteAppliance(roomId, applianceId);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Appliance deleted successfully!', 'success');
                    window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', false);
                    window.ApplianceAPI.fetchDashboardData();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to delete appliance.', 'error');
            }
        } else if (window.RelayConfig.currentAction === 'cancel-timer') {
            const [roomId, applianceId] = window.RelayConfig.currentData;
            try {
                const response = await window.ApplianceAPI.setTimer(roomId, applianceId, null);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Timer cancelled.', 'success');
                    window.ApplianceAPI.fetchDashboardData();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to cancel timer.', 'error');
            }
        } else if (window.RelayConfig.currentAction === 'unregister-board') {
            const [boardId] = window.RelayConfig.currentData;
            try {
                const response = await window.ApplianceAPI.unregisterBoard(boardId);
                const result = await response.json();
                if (response.ok) {
                    window.NotificationSystem.showNotification('Board unregistered successfully!', 'success');
                    window.ApplianceAPI.fetchDashboardData();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to unregister board.', 'error');
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
                window.NotificationSystem.showNotification('Room settings updated!', 'success');
                window.DOMHelpers.toggleElementVisibility('settings-room-modal', false);
                window.ApplianceAPI.fetchDashboardData();
            } else {
                const result = await response.json();
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
            }
            
        } catch (error) {
            console.error('Form submission failed:', error);
            window.NotificationSystem.showNotification('Failed to save room settings. Check your connection.', 'error');
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
        
        document.getElementById('edit-appliance-id').value = appliance.id;
        document.getElementById('settings-edit-room-id').value = roomId;
        document.getElementById('edit-appliance-name').value = appliance.name;

        const roomSelector = document.getElementById('edit-room-selector');
        const boardSelector = document.getElementById('edit-board-selector');
        const relaySelector = document.getElementById('edit-relay-selector');

        
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
        if (advancedSettingsToggle && advancedSettings) {
            advancedSettingsToggle.onclick = () => {
                advancedSettings.classList.toggle('hidden');
            };
        }

        window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', true);
    },

    async handleAddApplianceSubmit(e) {
        e.preventDefault();
        const roomId = window.RelayConfig.currentRoomId;
        const name = document.getElementById('new-appliance-name').value;
        const boardId = document.getElementById('board-selector').value;
        const relayId = document.getElementById('relay-selector').value;

        // 1. Validate that all fields have been selected.
        if (!name || !boardId || !relayId) {
            window.NotificationSystem.showNotification('Please fill out all fields.', 'error');
            return;
        }

        window.NotificationSystem.showLoading('Adding appliance...');

        try {
            // 2. Send the data to the backend API.
            const response = await window.ApplianceAPI.addAppliance(roomId, name, boardId, relayId);
            const result = await response.json();
            
            if (response.ok) {
                window.NotificationSystem.showNotification(result.message, 'success');
                
                // --- THE FIX IS HERE ---
                // 3. Close the modal to prevent the user from resubmitting the same data.
                window.DOMHelpers.toggleElementVisibility('add-appliance-modal', false);
                
                // 4. Fetch all data again. This is the critical step that refreshes the
                //    list of available relays for the next time the modal is opened.
                await window.ApplianceAPI.fetchDashboardData();
                // --- END OF FIX ---

            } else {
                // If the server returns an error (like 409), throw it to the catch block.
                throw new Error(result.message || 'An unknown error occurred.');
            }
        } catch (error) {
            // 5. Display any errors to the user.
            window.NotificationSystem.showNotification(error.message, 'error');
            console.error("Failed to add appliance:", error);
        } finally {
            // 6. Always remove the loading indicator.
            window.NotificationSystem.hideLoading();
        }
    },
    
    // Handle appliance settings form submission
    async handleApplianceSettingsSubmit(e) {
        e.preventDefault();
        const roomId = document.getElementById('settings-edit-room-id').value;
        const applianceId = document.getElementById('edit-appliance-id').value;
        const newName = document.getElementById('edit-appliance-name').value;
        const newRoomId = document.getElementById('edit-room-selector').value;
        
        // Handle both legacy and new board/relay system
        let boardId, relayId;
        if (document.getElementById('edit-appliance-relay')) {
            // Legacy system
            relayId = document.getElementById('edit-appliance-relay').value;
        } else {
            // New system
            boardId = document.getElementById('edit-appliance-board').value;
            relayId = document.getElementById('edit-appliance-relay-id').value;
        }
        
        try {
            const response = await window.ApplianceAPI.updateApplianceSettings(roomId, applianceId, newName, boardId, relayId, newRoomId);
            const result = await response.json();
            if (response.ok) {
                window.NotificationSystem.showNotification('Appliance settings updated!', 'success');
                window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', false);
                window.ApplianceAPI.fetchDashboardData();
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error(error);
            window.NotificationSystem.showNotification('Failed to save settings.', 'error');
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
                    window.NotificationSystem.showNotification('Timer set successfully!', 'success');
                    window.DOMHelpers.toggleElementVisibility('timer-modal', false);
                    window.ApplianceAPI.fetchDashboardData();
                } else {
                    window.NotificationSystem.showNotification(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                console.error(error);
                window.NotificationSystem.showNotification('Failed to set timer.', 'error');
            }
        } else {
            window.NotificationSystem.showNotification('Please set a valid future time or duration.', 'warning');
        }
    }
};

// Extended Modals system with additional functionality
window.Modals = {

    openAddRoomModal() {
        const form = document.getElementById('add-room-form');
        if(form) form.reset();
        window.DOMHelpers.toggleElementVisibility('add-room-modal', true);
    },

    async handleAddRoomSubmit(e) {
        e.preventDefault();
        const roomNameInput = document.getElementById('new-room-name');
        if (!roomNameInput.value) {
            window.NotificationSystem.showNotification('Room name cannot be empty.', 'error');
            return;
        }

        window.NotificationSystem.showLoading('Creating room...');
        try {
            const response = await window.ApplianceAPI.addRoom(roomNameInput.value);
            const result = await response.json();

            if (response.ok) {
                window.NotificationSystem.showNotification('Room added successfully!', 'success');
                window.DOMHelpers.toggleElementVisibility('add-room-modal', false);
                // Fetch all data again to update the UI
                await window.ApplianceAPI.fetchDashboardData();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            window.NotificationSystem.showNotification(error.message, 'error');
        } finally {
            window.NotificationSystem.hideLoading();
        }
    },
    
    // Open add appliance modal with dynamic board/relay loading
    async openAddApplianceModal() {
        const roomId = window.RelayConfig.currentRoomId;
        if (!roomId) {
            window.NotificationSystem.showNotification('Please select a room first.', 'warning');
            return;
        }
        
        const form = document.getElementById('add-appliance-form');
        if (form) form.reset();

        const boardSelector = document.getElementById('board-selector');
        const relaySelector = document.getElementById('relay-selector');
        
        if (boardSelector && relaySelector) {
            boardSelector.innerHTML = '<option value="" disabled selected>Loading boards...</option>';
            relaySelector.innerHTML = '<option value="" disabled selected>Select a board first...</option>';
            relaySelector.disabled = true;
        }

        window.DOMHelpers.toggleElementVisibility('add-appliance-modal', true);

        try {
            const response = await window.ApplianceAPI.getAvailableRelays(roomId);
            const available = await response.json();
            
            if (boardSelector) {
                boardSelector.innerHTML = '<option value="" disabled selected>Select a board...</option>';

                if (available.length > 0) {
                    available.forEach(board => {
                        const option = document.createElement('option');
                        option.value = board.board_id;
                        option.textContent = `Board ${board.board_id.substring(0,8)}... (${board.relays.length} free)`;
                        option._relays = board.relays; // Store relay data on the option
                        boardSelector.appendChild(option);

                        boardSelector.onchange = () => {
                            const selectedOption = boardSelector.options[boardSelector.selectedIndex];
                            const relays = selectedOption._relays; // Retrieve the stored relay data
        
                            relaySelector.innerHTML = ''; // Clear previous options
                            if (relays && relays.length > 0) {
                                relaySelector.disabled = false;
                                relaySelector.innerHTML = '<option value="" disabled selected>Select a relay...</option>';
                                relays.forEach(relay => {
                                    const relayOption = document.createElement('option');
                                    relayOption.value = relay.id;
                                    // Display a user-friendly name, e.g., "Relay 1"
                                    relayOption.textContent = `Relay ${relay.id.substring(0, 8)}...`; 
                                    relaySelector.appendChild(relayOption);
                                });
                            } else {
                                relaySelector.disabled = true;
                                relaySelector.innerHTML = '<option value="" disabled selected>No free relays on this board</option>';
                            }
                        };
                    });
                } else {
                    boardSelector.innerHTML = '<option value="" disabled selected>No boards with free relays in this room</option>';
                }
            }
        } catch (error) {
            console.error('Failed to load available relays:', error);
            if (boardSelector) {
                boardSelector.innerHTML = '<option value="" disabled selected>Error loading boards</option>';
            }
        }
    },

    // Open register board modal
    openRegisterBoardModal(roomId) {
        document.getElementById('register-board-form').reset();
        document.getElementById('register-board-room-id').value = roomId;
        window.DOMHelpers.toggleElementVisibility('register-board-modal', true);
    },
    // --- NEW FUNCTION: Handles the logic for the register board form ---
    async handleRegisterBoardSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const roomId = form.querySelector('#register-board-room-id').value;
        const boardId = form.querySelector('#board-id-manual').value;

        if (!boardId) {
            window.NotificationSystem.showNotification('Please enter or scan a Board ID.', 'error');
            return;
        }

        window.NotificationSystem.showLoading('Registering board...');

        try {
            const response = await window.ApplianceAPI.registerBoard(roomId, boardId);
            const result = await response.json();

            if (response.ok) {
                window.NotificationSystem.showNotification(result.message, 'success');
                window.DOMHelpers.toggleElementVisibility('register-board-modal', false);
                // Fetch all data again to update both the rooms and boards sections
                window.ApplianceAPI.fetchDashboardData();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            window.NotificationSystem.showNotification(error.message, 'error');
            console.error("Board registration failed:", error);
        } finally {
            window.NotificationSystem.hideLoading();
        }
    },

    // Open room settings (alias for backward compatibility)
    openRoomSettings(roomId) {
        window.RoomSettings.openRoomSettings(roomId);
    },

    // Open appliance settings (alias for backward compatibility)
    openApplianceSettings(roomId, applianceId) {
        window.ApplianceSettings.openApplianceSettings(roomId, applianceId);
    },

    // Open confirmation modal (alias for backward compatibility)
    openConfirmationModal(action, ...data) {
        window.ConfirmationModal.openConfirmationModal(action, ...data);
    }
};
