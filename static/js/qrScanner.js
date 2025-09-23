// qrScanner.js - QR code scanner functionality
window.QRScanner = {
    // Initialize QR scanner
    init() {
        // The library is loaded via CDN, so we initialize it when needed.
        // This function can be expanded if more setup is required.
    },

    // Open QR scanner modal
    openQrScanner(targetInputId) {
        const qrModal = document.getElementById('qr-scanner-modal');
        if (!qrModal) return;

        if (!window.RelayConfig.html5QrCode) {
            window.RelayConfig.html5QrCode = new Html5Qrcode("qr-reader");
        }
        
        window.DOMHelpers.toggleElementVisibility('qr-scanner-modal', true);
        
        const onQrSuccess = (decodedText, decodedResult) => {
            window.RelayConfig.html5QrCode.stop().then(() => {
                window.DOMHelpers.toggleElementVisibility('qr-scanner-modal', false);
                // MODIFICATION: Directly populate the input field with the scanned board ID
                const targetInput = document.getElementById(targetInputId);
                if(targetInput) {
                    targetInput.value = decodedText;
                }
            }).catch(err => console.error("Failed to stop QR scanner.", err));
        };
        
        const config = { fps: 10, qrbox: { width: 250, height: 250 } };
        window.RelayConfig.html5QrCode.start({ facingMode: "environment" }, config, onQrSuccess);
    },

    closeQrScanner() {
        if (window.RelayConfig.html5QrCode) {
            window.RelayConfig.html5QrCode.stop().catch(err => {});
        }
        window.DOMHelpers.toggleElementVisibility('qr-scanner-modal', false);
    }

    // Close QR scanner modal
    closeQrScanner() {
        if (window.RelayConfig.html5QrCode) {
            window.RelayConfig.html5QrCode.stop().catch(err => {});
        }
        const qrModal = document.getElementById('qr-scanner-modal');
        if(qrModal) qrModal.classList.add('hidden');
    },

    // Handle QR code data by sending it to the backend for decryption
    async handleQrCodeData(encryptedText, roomId) {
        window.NotificationSystem.showLoading('Verifying board...');
        try {
            // Step 1: Send encrypted data to the server to get clean JSON
            const extractResponse = await fetch('/api/extract-qr-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ encrypted_data: encryptedText })
            });

            const decryptedData = await extractResponse.json();

            if (!extractResponse.ok) {
                throw new Error(decryptedData.error || 'Failed to decrypt board data.');
            }

            // Step 2: If decryption is successful, add the board to the room
            const addResponse = await window.ApplianceAPI.addBoard(roomId, decryptedData);
            const result = await addResponse.json();

            if (addResponse.ok) {
                window.NotificationSystem.showNotification(result.message, 'success');
                window.ApplianceAPI.fetchRoomsAndAppliances();
            } else {
                throw new Error(result.message || 'Failed to register board.');
            }

        } catch (error) {
            window.NotificationSystem.showNotification(error.message, 'error');
            console.error("QR Handling Error:", error);
        } finally {
            window.NotificationSystem.hideLoading();
        }
    }
};
