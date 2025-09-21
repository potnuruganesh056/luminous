// applianceRenderer.js - Appliance display and management
window.ApplianceRenderer = {
    // Render appliances for a specific room
    renderAppliances(appliances, roomName) {
        const container = window.DOMHelpers.clearContainer('appliance-container');
        
        // Update appliances heading with room name
        const appliancesHeading = document.getElementById('appliances-heading');
        if (appliancesHeading) {
            appliancesHeading.textContent = `${roomName} Appliances`;
        }
            
        // Switch views from rooms to appliances
        window.DOMHelpers.toggleElementVisibility('rooms-view', false);
        window.DOMHelpers.toggleElementVisibility('appliances-view', true);

        // Update monitoring button logic
        this.updateMonitoringButton();

        if (appliances.length > 0) {
            appliances.forEach(appliance => {
                const applianceCard = this.createApplianceCard(appliance);
                container.appendChild(applianceCard);
                
                // Add toggle event listener for appliance state changes
                const toggleInput = applianceCard.querySelector('input[type="checkbox"]');
                toggleInput.onchange = () => {
                    const newState = toggleInput.checked;
                    window.ApplianceAPI.sendApplianceState(window.RelayConfig.currentRoomId, appliance.id, newState);
                };
                
                // Update timer display for this appliance
                window.DOMHelpers.updateTimerDisplay(applianceCard, appliance);
            });

            // Initialize sortable functionality
            this.initializeApplianceSortable(container);
            
        } else {
            container.innerHTML = `
                <p class="text-center text-gray-500 col-span-full">
                    No appliances in this room yet. Click "Add Appliance" to get started!
                </p>
            `;
        }

        // Update monitoring UI state
        window.DOMHelpers.updateMonitoringUIState();

        window.DOMHelpers.updateFabVisibility('appliances');
    },

    // Create individual appliance card
    createApplianceCard(appliance) {
        const is_on = appliance.state;
        const is_locked = appliance.locked;
        
        const applianceCard = window.DOMHelpers.createElement('div', {
            'data-slot': 'card',
            'data-id': appliance.id,
            className: "bg-card text-card-foreground rounded-xl border py-6 px-6 shadow-sm transition-all flex flex-col items-stretch relative",
            innerHTML: `
                <div class="flex items-center justify-between mb-4">
                    <div data-slot="card-title" class="leading-none font-semibold pr-2 flex items-center">
                        <span class="appliance-name">${appliance.name}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button class="p-1 rounded-full hover:bg-muted transition-colors flex-shrink-0" 
                                title="Set Manual Override" 
                                onclick="window.ApplianceActions.toggleLock('${window.RelayConfig.currentRoomId}', '${appliance.id}')">
                            <i id="lock-icon-${appliance.id}" 
                               class="h-4 w-4 fas ${is_locked ? 'fa-lock text-red-500' : 'fa-unlock text-gray-400'}"></i>
                        </button>
                        <button class="p-1 rounded-full hover:bg-muted transition-colors flex-shrink-0" 
                                title="Set Timer" 
                                onclick="window.TimerModal.openTimerModal('${window.RelayConfig.currentRoomId}', '${appliance.id}')">
                            <i class="h-4 w-4 fas fa-clock text-gray-400"></i>
                        </button>
                        <button class="p-1 rounded-full hover:bg-muted transition-colors flex-shrink-0" 
                                title="Appliance Settings" 
                                onclick="window.ApplianceSettings.openApplianceSettings('${window.RelayConfig.currentRoomId}', '${appliance.id}')">
                            <i class="h-4 w-4 fas fa-cog text-gray-400"></i>
                        </button>
                        <button class="p-1 rounded-full hover:bg-muted transition-colors flex-shrink-0 cancel-timer-btn hidden" 
                                title="Cancel Timer" 
                                onclick="window.ConfirmationModal.openConfirmationModal('cancel-timer', '${window.RelayConfig.currentRoomId}', '${appliance.id}')">
                            <i class="h-4 w-4 fas fa-times-circle text-red-400"></i>
                        </button>
                    </div>
                </div>
                <div data-slot="card-content" class="flex-grow flex items-center justify-between">
                    <i class="fas fa-lightbulb text-2xl ${is_on ? 'text-primary-accent' : 'text-gray-400 dark:text-gray-600'} transition-colors"></i>
                    <label class="custom-toggle-switch">
                        <input type="checkbox" 
                               data-room-id="${window.RelayConfig.currentRoomId}" 
                               data-appliance-id="${appliance.id}" 
                               ${is_on ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
                <span class="timer-display absolute bottom-2 left-2 text-xs font-semibold text-primary-accent hidden"></span>
            `
        });
        
        return applianceCard;
    },

    // Update monitoring button state
    updateMonitoringButton() {
        const monitoringBtn = document.getElementById('start-monitoring-btn');
        if (monitoringBtn) {
            if (window.RelayConfig.activeMonitors.has(window.RelayConfig.currentRoomId)) {
                monitoringBtn.innerHTML = '<i class="fas fa-video-slash mr-2"></i>Stop Monitoring';
                monitoringBtn.classList.replace('bg-primary-accent', 'bg-red-500');
            } else {
                monitoringBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>Start Monitoring';
                monitoringBtn.classList.replace('bg-red-500', 'bg-primary-accent');
            }
            // Disable the button if global monitoring is active
            monitoringBtn.disabled = window.RelayConfig.isGlobalMonitoringActive;
            monitoringBtn.title = window.RelayConfig.isGlobalMonitoringActive ? "Stop global monitoring to enable this." : "";
        }
    },

    // Initialize sortable functionality for appliances
    initializeApplianceSortable(container) {
        if (window.RelayConfig.applianceSortable) {
            window.RelayConfig.applianceSortable.destroy();
        }
        
        window.RelayConfig.applianceSortable = new Sortable(container, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: async (evt) => {
                if (evt.oldIndex !== evt.newIndex) {
                    const newOrder = Array.from(container.children).map(child => child.dataset.id);
                    await window.ApplianceAPI.saveNewApplianceOrder(window.RelayConfig.currentRoomId, newOrder);
                }
            }
        });
    }
};
