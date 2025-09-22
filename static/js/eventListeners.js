// eventListeners.js - Event listener management
window.EventListeners = {
    init() {
        // FAB Menu Logic with helper function
        const fabMainBtn = document.getElementById('fab-main-btn');
        const fabOptions = document.getElementById('fab-options');
        
        fabMainBtn.addEventListener('click', () => {
            const isVisible = fabOptions.style.display === 'flex';
            if (isVisible) {
                fabOptions.style.opacity = '0';
                fabOptions.style.transform = 'translateY(10px)';
                setTimeout(() => { fabOptions.style.display = 'none'; }, 200);
            } else {
                fabOptions.style.display = 'flex';
                setTimeout(() => {
                    fabOptions.style.opacity = '1';
                    fabOptions.style.transform = 'translateY(0)';
                }, 10);
            }
            fabMainBtn.classList.toggle('rotate-45');
        });

        // Helper function to hide FAB menu (your optimization)
        const hideFabMenu = () => {
            fabOptions.style.display = 'none';
            fabMainBtn.classList.remove('rotate-45');
        };

        // FAB Action Buttons
        document.getElementById('add-room-btn').addEventListener('click', () => {
            window.Modals.openAddRoomModal();
            hideFabMenu();
        });
        
        document.getElementById('add-appliance-btn').addEventListener('click', () => {
            window.Modals.openAddApplianceModal();
            hideFabMenu();
        });

        const registerBoardForm = document.getElementById('register-board-form');
        if (registerBoardForm) {
            registerBoardForm.addEventListener('submit', window.Modals.handleRegisterBoardSubmit);
        }
        
        document.getElementById('register-board-btn').addEventListener('click', () => {
            window.Modals.openRegisterBoardModal(window.RelayConfig.currentRoomId);
            hideFabMenu();
        });

        // Navigation
        document.getElementById('back-to-rooms-btn').addEventListener('click', window.RoomRenderer.backToRooms);

        // QR Scanner button inside the modal
        const scanQrForRegisterBtn = document.getElementById('scan-qr-for-register-btn');
        if(scanQrForRegisterBtn) {
            scanQrForRegisterBtn.addEventListener('click', () => {
                // Tell the scanner which input field to populate
                window.QRScanner.openQrScanner('board-id-manual');
            });
        }

        document.getElementById('add-appliance-form').addEventListener('submit', window.Modals.handleAddApplianceSubmit);
        // if (addApplianceForm) {
        //     addApplianceForm.addEventListener('submit', async (e) => {
        //         e.preventDefault();
        //         const roomId = window.RelayConfig.currentRoomId;
        //         const name = document.getElementById('new-appliance-name').value;
        //         const boardId = document.getElementById('board-selector').value;
        //         const relayId = document.getElementById('relay-selector').value;

        //         if (!name || !boardId || !relayId) {
        //             window.NotificationSystem.showNotification('Please fill out all fields.', 'error');
        //             return;
        //         }

        //         window.NotificationSystem.showLoading('Adding appliance...');
        //         try {
        //             const response = await window.ApplianceAPI.addAppliance(roomId, name, boardId, relayId);
        //             const result = await response.json();
                    
        //             if (response.ok) {
        //                 window.NotificationSystem.showNotification(result.message, 'success');
                        
        //                 // --- THE FIX IS HERE ---
        //                 // 1. Close the modal so the user can't submit the same data again.
        //                 window.DOMHelpers.toggleElementVisibility('add-appliance-modal', false);
                        
        //                 // 2. Fetch fresh data to update the UI and available relay list.
        //                 await window.ApplianceAPI.fetchDashboardData();
        //                 // --- END OF FIX ---

        //             } else {
        //                 throw new Error(result.message);
        //             }
        //         } catch (error) {
        //             window.NotificationSystem.showNotification(error.message, 'error');
        //         } finally {
        //             window.NotificationSystem.hideLoading();
        //         }
        //     });
        // }

        // Initialize other listener groups
        this.initWebcamListeners();
        this.initMonitoringListeners();
        this.initModalListeners();
        this.initFormListeners();
        this.initQRListeners();
        this.initSpecialListeners();
    },

    // Webcam-related event listeners
    initWebcamListeners() {
        const globalWebcamBtn = document.getElementById('global-open-webcam-btn');
        const openWebcamBtn = document.getElementById('open-webcam-btn');
        const closeWebcamBtn = document.getElementById('close-webcam-btn');

        if (globalWebcamBtn) {
            globalWebcamBtn.addEventListener('click', window.WebcamManager.toggleGlobalWebcam);
        }
        if (openWebcamBtn) {
            openWebcamBtn.addEventListener('click', window.WebcamManager.toggleWebcam);
        }
        if (closeWebcamBtn) {
            closeWebcamBtn.addEventListener('click', window.WebcamManager.toggleWebcam);
        }
    },

    // Monitoring-related event listeners
    initMonitoringListeners() {
        const globalMonitoringBtn = document.getElementById('global-start-monitoring-btn');
        const startMonitoringBtn = document.getElementById('start-monitoring-btn');

        if (globalMonitoringBtn) {
            globalMonitoringBtn.addEventListener('click', () => window.AIMonitoring.toggleGlobalMonitoring());
        }
        if (startMonitoringBtn) {
            startMonitoringBtn.addEventListener('click', () => {
                window.AIMonitoring.toggleMonitoring(window.RelayConfig.currentRoomId);
            });
        }
    },

    // Modal-related event listeners
    initModalListeners() {
        // Cancel buttons for various modals
        const cancelButtons = [
            { id: 'cancel-room-btn', modal: 'add-room-modal' },
            { id: 'cancel-appliance-btn', modal: 'add-appliance-modal' },
            { id: 'cancel-room-settings-btn', modal: 'settings-room-modal' },
            { id: 'cancel-appliance-settings-btn', modal: 'settings-appliance-modal' },
            { id: 'cancel-timer-btn', modal: 'timer-modal' }
        ];

        cancelButtons.forEach(({ id, modal }) => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.addEventListener('click', () => {
                    window.DOMHelpers.toggleElementVisibility(modal, false);
                });
            }
        });

        // Delete buttons
        const deleteRoomBtn = document.getElementById('delete-room-btn');
        const deleteApplianceBtn = document.getElementById('delete-appliance-btn');
        
        if (deleteRoomBtn) {
            deleteRoomBtn.addEventListener('click', () => {
                const roomId = document.getElementById('edit-room-id').value;
                window.ConfirmationModal.openConfirmationModal('delete-room', roomId);
            });
        }
        
        if (deleteApplianceBtn) {
            deleteApplianceBtn.addEventListener('click', () => {
                const roomId = document.getElementById('settings-edit-room-id').value;
                const applianceId = document.getElementById('edit-appliance-id').value;
                window.ConfirmationModal.openConfirmationModal('delete-appliance', roomId, applianceId);
            });
        }

        // Confirmation modal
        const confirmCancelBtn = document.getElementById('confirm-cancel-btn');
        const confirmActionBtn = document.getElementById('confirm-action-btn');
        if (confirmCancelBtn) {
            confirmCancelBtn.addEventListener('click', window.ConfirmationModal.cancelConfirmation);
        }
        if (confirmActionBtn) {
            confirmActionBtn.addEventListener('click', window.ConfirmationModal.handleConfirmation);
        }
    },

    // Form event listeners
    initFormListeners() {
        const forms = [
            { id: 'add-room-form', handler: window.RoomActions.handleAddRoomSubmit },
            { id: 'add-appliance-form', handler: window.ApplianceActions.handleAddApplianceSubmit },
            { id: 'settings-room-form', handler: window.RoomSettings.handleRoomSettingsSubmit },
            { id: 'settings-appliance-form', handler: window.ApplianceSettings.handleApplianceSettingsSubmit },
            { id: 'timer-form', handler: window.TimerModal.handleTimerSubmit }
        ];

        forms.forEach(({ id, handler }) => {
            const form = document.getElementById(id);
            if (form) {
                form.addEventListener('submit', handler);
            }
        });
    },

    // QR-related event listeners
    initQRListeners() {
        const addBoardBtn = document.getElementById('add-board-btn');
        const closeScannerBtn = document.getElementById('close-scanner-btn');

        if (addBoardBtn) {
            addBoardBtn.addEventListener('click', () => {
                if (window.RelayConfig.currentRoomId) {
                    window.QRScanner.openQrScanner(window.RelayConfig.currentRoomId);
                }
            });
        }
        if (closeScannerBtn) {
            closeScannerBtn.addEventListener('click', window.QRScanner.closeQrScanner);
        }
    },

    // Special event listeners
    initSpecialListeners() {
        // AI Control Switch
        const aiControlSwitch = document.getElementById('ai-control-switch');
        if (aiControlSwitch) {
            aiControlSwitch.addEventListener('click', async (e) => {
                const switchBtn = e.currentTarget;
                const isChecked = switchBtn.dataset.state === 'checked';
                const roomId = document.getElementById('edit-room-id').value;

                try {
                    const response = await window.ApplianceAPI.updateRoomSettings(roomId, null, !isChecked);
                    const result = await response.json();
                    if (response.ok) {
                        if (isChecked) {
                            switchBtn.dataset.state = 'off';
                            switchBtn.classList.remove('data-[state=checked]');
                        } else {
                            switchBtn.dataset.state = 'checked';
                            switchBtn.classList.add('data-[state=checked]');
                        }
                        window.NotificationSystem.showNotification(`AI Control is now ${!isChecked ? 'ON' : 'OFF'}.`, 'on');
                        window.ApplianceAPI.fetchRoomsAndAppliances();
                    } else {
                        window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
                    }
                } catch (error) {
                    console.error(error);
                    window.NotificationSystem.showNotification('Failed to update AI control.', 'off');
                }
            });
        }

        // Window beforeunload to cleanup streams
        window.addEventListener('beforeunload', () => {
            window.WebcamManager.stopAllStreams();
        });
    }
};
