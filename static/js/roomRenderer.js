// roomRenderer.js - Room and Board display management
window.RoomRenderer = {
    // Render rooms in the main view
    renderRooms(rooms) {
        const container = window.DOMHelpers.clearContainer('room-container');
        
        if (!container) {
            console.error('room-container element not found in DOM');
            setTimeout(() => {
                const retryContainer = document.getElementById('room-container');
                if (retryContainer) {
                    this.renderRooms(rooms);
                } else {
                    console.error('room-container still not found after retry');
                }
            }, 100);
            return;
        }
        
        if (rooms.length > 0) {
            window.DOMHelpers.toggleElementVisibility('rooms-view', true);
            window.DOMHelpers.toggleElementVisibility('appliances-view', false);
            
            // Global monitoring button state management
            this.updateGlobalMonitoringButtons();

            rooms.forEach(room => {
                const roomCard = this.createRoomCard(room);
                container.appendChild(roomCard);
            });
            
            // Initialize sortable functionality
            this.initializeRoomSortable(container);
        } else {
            container.innerHTML = `<p class="text-center text-gray-500 col-span-full">No rooms created yet. Click the '+' button to add one.</p>`;
        }
    },

    // Render boards in the boards view
    renderBoards(boards) {
        const container = window.DOMHelpers.clearContainer('boards-container');
        if (!container) return;

        if (boards.length > 0) {
            boards.forEach(board => {
                const boardCard = this.createBoardCard(board);
                container.appendChild(boardCard);
            });
        } else {
            container.innerHTML = `<p class="text-center text-gray-500 col-span-full">No boards registered to your account yet.</p>`;
        }
    },

    // Create individual room card
    createRoomCard(room) {
        const isCurrentlyMonitored = window.RelayConfig.activeMonitors.has(room.id);
        const aiControlText = isCurrentlyMonitored ? 'AI Enabled' : 'AI Disabled';
        const aiStatusColor = isCurrentlyMonitored ? 'text-green-500' : 'text-gray-500';
        const stats = this.calculateRoomStats(room.id);
        
        const roomCard = window.DOMHelpers.createElement('div', {
            'data-slot': 'card',
            'data-id': room.id,
            className: "bg-card text-card-foreground rounded-xl border p-6 shadow-sm transition-all relative flex flex-col",
            innerHTML: `
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold cursor-pointer hover:underline" onclick="window.RoomRenderer.showAppliances('${room.id}')">${room.name}</h3>
                    <div class="flex space-x-2">
                        <button class="p-1 rounded-full hover:bg-muted transition-colors flex-shrink-0" title="Room Settings" onclick="event.stopPropagation(); window.RoomSettings ? window.RoomSettings.openRoomSettings('${room.id}') : window.Modals.openRoomSettings('${room.id}')">
                            <i class="h-4 w-4 fas fa-cog text-gray-400"></i>
                        </button>
                    </div>
                </div>
                <div class="text-sm text-muted-foreground space-y-1 flex-grow">
                    <p><strong>${stats.applianceCount}</strong> Appliances</p>
                    <p><strong>${stats.boardCount}</strong> Boards (${stats.totalRelays} Relays)</p>
                    <p><strong>${stats.occupiedRelays}</strong> Relays in Use</p>
                    <p class="mt-2"><span class="font-semibold ${aiStatusColor}">${aiControlText}</span></p>
                </div>
            `
        });
        
        return roomCard;
    },

    // Create individual board card
    createBoardCard(board) {
        const roomName = board.room_id ? window.RelayConfig.allRoomsData.find(r => r.id === board.room_id)?.name || 'N/A' : 'Unassigned';
        return window.DOMHelpers.createElement('div', {
            'data-id': board.board_id,
            className: "bg-card text-card-foreground rounded-xl border p-6 shadow-sm transition-all flex flex-col",
            innerHTML: `
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold font-mono">${board.board_id}</h3>
                    <button class="p-1 rounded-full hover:bg-muted" title="Unregister Board" onclick="window.Modals.openConfirmationModal('unregister-board', '${board.board_id}')"><i class="fas fa-trash-alt text-red-400"></i></button>
                </div>
                <div class="text-sm text-muted-foreground space-y-1 flex-grow">
                    <p>Assigned to: <strong>${roomName}</strong></p>
                    <p><strong>${board.number_of_relays}</strong> Relays Total</p>
                </div>
            `
        });
    },
    
    // Calculate room statistics
    calculateRoomStats(roomId) {
        const room = window.RelayConfig.allRoomsData.find(r => r.id === roomId);
        const boardsInRoom = window.RelayConfig.allBoardsData ? window.RelayConfig.allBoardsData.filter(b => b.room_id === roomId) : [];
        
        const applianceCount = room ? room.appliances.length : 0;
        const boardCount = boardsInRoom.length;
        const totalRelays = boardsInRoom.reduce((sum, board) => sum + board.number_of_relays, 0);
        const occupiedRelays = applianceCount; // Since each appliance takes one relay

        return { applianceCount, boardCount, totalRelays, occupiedRelays };
    },

    // Update global monitoring button states
    updateGlobalMonitoringButtons() {
        const globalMonitoringBtn = document.getElementById('global-start-monitoring-btn');
        const globalMonitoringCard = document.getElementById('global-monitoring-card');
        
        if (window.RelayConfig.isGlobalMonitoring) {
            if (globalMonitoringBtn) {
                globalMonitoringBtn.innerHTML = '<i class="fas fa-video-slash mr-2"></i>Stop Global Monitoring';
            }
            if (globalMonitoringCard) {
                globalMonitoringCard.classList.remove('hidden');
            }
        } else {
            if (globalMonitoringBtn) {
                globalMonitoringBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>Start Global Monitoring';
            }
            if (globalMonitoringCard) {
                globalMonitoringCard.classList.add('hidden');
            }
        }
    },

    // Initialize sortable functionality for rooms
    initializeRoomSortable(container) {
        if (window.RelayConfig.roomSortable) {
            window.RelayConfig.roomSortable.destroy();
        }
        window.RelayConfig.roomSortable = new Sortable(container, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: async (evt) => {
                if (evt.oldIndex !== evt.newIndex) {
                    const newOrder = Array.from(container.children).map(child => child.dataset.id);
                    await window.ApplianceAPI.saveNewRoomOrder(newOrder);
                }
            }
        });
    },
    
    // Show appliances for a specific room
    showAppliances(roomId) {
        const room = window.RelayConfig.allRoomsData.find(r => r.id === roomId);
        if (room) {
            window.RelayConfig.currentRoomId = roomId;
            window.ApplianceRenderer.renderAppliances(room.appliances, room.name);
        }
    },

    // Navigate back to rooms view
    backToRooms() {
        window.RelayConfig.currentRoomId = null;
        window.DOMHelpers.toggleElementVisibility('rooms-view', true);
        window.DOMHelpers.toggleElementVisibility('appliances-view', false);
    }
};
