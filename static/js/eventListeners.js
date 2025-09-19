// eventListeners.js - Event listener management
window.EventListeners = {
    // Initialize all event listeners
    init() {
        this.initWebcamListeners();
        this.initMonitoringListeners();
        this.initNavigationListeners();
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
            globalMonitoringBtn.addEventListener('click', window.AIMonitoring.toggleGlobalMonitoring);
        }
        if (startMonitoringBtn) {
            startMonitoringBtn.addEventListener('click', () => {
                window.AIMonitoring.toggleMonitoring(window.RelayConfig.currentRoomId);
            });
        }
    },

    // Navigation event listeners
    initNavigationListeners() {
        const backToRoomsBtn = document.getElementById('back-to-rooms-btn');
        if (backToRoomsBtn) {
            backToRoomsBtn.addEventListener('click', window.RoomRenderer.backToRooms);
        }
    },

    // Modal-related event listeners
    initModalListeners() {
        // Add Room Modal
        const addRoomBtn = document.getElementById('add-room-btn');
        const cancelRoomBtn = document.getElementById('cancel-room-btn');
        if (addRoomBtn) {
            addRoomBtn.addEventListener('click', () => {
                window.DOMHelpers.toggleElementVisibility('add-room-modal', true);
            });
        }
        if (cancelRoomBtn) {
            cancelRoomBtn.addEventListener('click', () => {
                window.DOMHelpers.toggleElementVisibility('add-room-modal', false);
            });
        }

        // Add Appliance Modal
        const addApplianceBtn = document.getElementById('add-appliance-btn');
        const cancelApplianceBtn = document.getElementById('cancel-appliance-btn');
        if (addApplianceBtn) {
            addApplianceBtn.addEventListener('click', window.ApplianceActions.handleAddAppliance);
        }
        if (cancelApplianceBtn) {
            cancelApplianceBtn.addEventListener('click', () => {
                window.DOMHelpers.toggleElementVisibility('add-appliance-modal', false);
            });
        }

        // Room Settings Modal
        const cancelRoomSettingsBtn = document.getElementById('cancel-room-settings-btn');
        const deleteRoomBtn = document.getElementById('delete-room-btn');
        if (cancelRoomSettingsBtn) {
            cancelRoomSettingsBtn.addEventListener('click', () => {
                window.DOMHelpers.toggleElementVisibility('settings-room-modal', false);
            });
        }
        if (deleteRoomBtn) {
            deleteRoomBtn.addEventListener('click', () => {
                const roomId = document.getElementById('edit-room-id').value;
                window.ConfirmationModal.openConfirmationModal('delete-room', roomId);
            });
        }

        // Appliance Settings Modal
        const cancelApplianceSettingsBtn = document.getElementById('cancel-appliance-settings-btn');
        const deleteApplianceBtn = document.getElementById('delete-appliance-btn');
        if (cancelApplianceSettingsBtn) {
            cancelApplianceSettingsBtn.addEventListener('click', () => {
                window.DOMHelpers.toggleElementVisibility('settings-appliance-modal', false);
            });
        }
        if (deleteApplianceBtn) {
            deleteApplianceBtn.addEventListener('click', () => {
                const roomId = document.getElementById('settings-edit-room-id').value;
                const applianceId = document.getElementById('edit-appliance-id').value;
                window.ConfirmationModal.openConfirmationModal('delete-appliance', roomId, applianceId);
            });
        }

        // Timer Modal
        const cancelTimerBtn = document.getElementById('cancel-timer-btn');
        if (cancelTimerBtn) {
            cancelTimerBtn.addEventListener('click', () => {
                window.DOMHelpers.toggleElementVisibility('timer-modal', false);
            });
        }

        // Confirmation Modal
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
        // Add Room Form
        const addRoomForm = document.getElementById('add-room-form');
        if (addRoomForm) {
            addRoomForm.addEventListener('submit', window.RoomActions.handleAddRoomSubmit);
        }

        // Add Appliance Form
        const addApplianceForm = document.getElementById('add-appliance-form');
        if (addApplianceForm) {
            addApplianceForm.addEventListener('submit', window.ApplianceActions.handleAddApplianceSubmit);
        }

        // Room Settings Form
        const settingsRoomForm = document.getElementById('settings-room-form');
        if (settingsRoomForm) {
            settingsRoomForm.addEventListener('submit', window.RoomSettings.handleRoomSettingsSubmit);
        }

        // Appliance Settings Form
        const settingsApplianceForm = document.getElementById('settings-appliance-form');
        if (settingsApplianceForm) {
            settingsApplianceForm.addEventListener('submit', window.ApplianceSettings.handleApplianceSettingsSubmit);
        }

        // Timer Form
        const timerForm = document.getElementById('timer-form');
        if (timerForm) {
            timerForm.addEventListener('submit', window.TimerModal.handleTimerSubmit);
        }
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
