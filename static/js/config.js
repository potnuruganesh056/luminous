// config.js - Global configuration and state variables
window.RelayConfig = {
    // Data Caches
    allRoomsData: [],
    allBoardsData: [],
    userEmail: null, // To check if email notifications can be sent

    // Current State
    currentRoomId: null,

    // Sortable Instances
    roomSortable: null,
    applianceSortable: null,
    
    // Timer intervals for each appliance
    timerIntervals: {},
    
    // AI Model & Settings
    model: null,
    modelLoaded: false,
    aiControlInterval: 5000,
    lastEmailTime: null,
    
    // Global Monitoring State
    isGlobalMonitoring: false,
    isGlobalMonitoringActive: false,
    globalMonitoringStream: null,
    globalMonitoringIntervalId: null,
    lastGlobalEmailTime: null,
    globalWebcamStream: null,
    
    // Individual Room Monitoring
    activeMonitors: new Map(),
    isMonitoring: false,
    monitoringStream: null,
    monitoringIntervalId: null,
    monitoringVideoElement: document.createElement('video'),
    
    // Webcam & Camera
    webcamStream: null,

    // Modal State
    currentAction: null,
    currentData: null,
    pendingGlobalAction: null,
    
    // QR Scanner
    html5QrCode: null
};
