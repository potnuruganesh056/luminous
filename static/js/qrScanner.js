// qrScanner.js - QR code scanner functionality
window.QRScanner = {
    // Initialize QR scanner
    init() {
        window.RelayConfig.html5QrCode = new Html5Qrcode("qr-reader");
    },

    // Open QR scanner modal
    openQrScanner(roomId) {
        const qrModal = document.getElementById('qr-scanner-modal');
        qrModal.classList.remove('hidden');
        const config = { fps: 10, qrbox: { width: 250, height: 250 } };
        
        const onQrSuccess = (decodedText, decodedResult) => {
            window.RelayConfig.html5QrCode.stop().then(() => {
                qrModal.classList.add('hidden');
                this.handleQrCodeData(decodedText, roomId);
            }).catch(err => console.error("Failed to stop QR scanner.", err));
        };
        
        window.RelayConfig.html5QrCode.start({ facingMode: "environment" }, config, onQrSuccess);
    },

    // Close QR scanner modal
    closeQrScanner() {
        window.RelayConfig.html5QrCode.stop().catch(err => {});
        document.getElementById('qr-scanner-modal').classList.add('hidden');
    },

    // Decrypt QR code data
    decryptQrData(encryptedText) {
        // This is a placeholder. Replace with actual decryption logic.
        try {
            // This example assumes the QR code contains Base64 encoded JSON.
            const jsonString = atob(encryptedText);
            return JSON.parse(jsonString);
        } catch (e) {
            console.error("Decryption/Parsing failed:", e);
            return null;
        }
    },

    // Handle QR code data
    async handleQrCodeData(qrText, roomId) {
        const decryptedData = this.decryptQrData(qrText);

        // Validate using the new field name 'board_id'
        if (!decryptedData || !decryptedData.board_id) {
            window.NotificationSystem.showNotification('Invalid or unrecognized QR Code format.', 'off');
            return;
        }

        try {
            const response = await window.ApplianceAPI.addBoard(roomId, decryptedData);
            const result = await response.json();
            if (response.ok) {
                window.NotificationSystem.showNotification(result.message, 'on');
                window.ApplianceAPI.fetchRoomsAndAppliances();
            } else {
                window.NotificationSystem.showNotification(`Error: ${result.message}`, 'off');
            }
        } catch (error) {
            window.NotificationSystem.showNotification('Failed to add board to the server.', 'off');
        }
    }
};
