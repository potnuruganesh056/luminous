// config.js - Global configuration and state variables
window.RelayConfig = {
    // Timer intervals for each appliance
    timerIntervals: {},
    
    // All rooms data cache
    allRoomsData: [],
    
    // Current room being viewed
    currentRoomId: null,
    
    // Sortable instances
    roomSortable: null,
    applianceSortable: null,
    
    // AI Control settings
    aiControlInterval: 5000,
    lastEmailTime: null,
    
    // Global monitoring state
    isGlobalMonitoring: false,
    isGlobalMonitoringActive: false,
    globalMonitoringStream: null,
    globalMonitoringIntervalId: null,
    lastGlobalEmailTime: null,
    
    // Webcam related
    webcamStream: null,
    globalWebcamStream: null,
    
    // AI Model
    model: null,
    modelLoaded: false,
    
    // Monitoring
    activeMonitors: new Map(),
    isMonitoring: false,
    monitoringStream: null,
    monitoringIntervalId: null,
    monitoringVideoElement: document.createElement('video'),
    
    // Modal state
    currentAction: null,
    currentData: null,
    pendingGlobalAction: null,

    userEmail: null,
    
    // QR Scanner
    html5QrCode: null
};
