// domHelpers.js - DOM manipulation and UI utility functions
window.DOMHelpers = {
    // Get DOM elements with error handling
    getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with id '${id}' not found`);
        }
        return element;
    },

    // Show/hide elements with classes
    toggleElementVisibility(elementId, show) {
        const element = this.getElementById(elementId);
        if (element) {
            if (show) {
                element.classList.remove('hidden');
            } else {
                element.classList.add('hidden');
            }
        }
    },

    // Update button text and classes
    updateButton(buttonId, innerHTML, addClasses = [], removeClasses = []) {
        const button = this.getElementById(buttonId);
        if (button) {
            button.innerHTML = innerHTML;
            if (removeClasses.length) {
                button.classList.remove(...removeClasses);
            }
            if (addClasses.length) {
                button.classList.add(...addClasses);
            }
        }
    },

    // Clear container content
    clearContainer(containerId) {
        const container = this.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
        return container;
    },

    // Create DOM elements with attributes
    createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (content && !attributes.innerHTML) {
            element.textContent = content;
        }
        
        return element;
    },

    // Update timer display for appliances
    updateTimerDisplay(card, appliance) {
        const timerElement = card.querySelector('.timer-display');
        const cancelButton = card.querySelector('.cancel-timer-btn');
        const toggleInput = card.querySelector('input[type="checkbox"]');
        
        if (!timerElement || !cancelButton || !toggleInput) return;

        clearInterval(window.RelayConfig.timerIntervals[appliance.id]);

        if (appliance.timer && appliance.state) {
            const update = () => {
                const timeLeft = Math.floor(appliance.timer - Date.now() / 1000);
                if (timeLeft > 0) {
                    const minutes = Math.floor(timeLeft / 60);
                    const seconds = timeLeft % 60;
                    timerElement.textContent = `Timer: ${minutes}m ${seconds}s`;
                    timerElement.classList.remove('hidden');
                    cancelButton.classList.remove('hidden');
                } else {
                    timerElement.textContent = `Timer Off`;
                    clearInterval(window.RelayConfig.timerIntervals[appliance.id]);
                    cancelButton.classList.add('hidden');
                    window.ApplianceAPI.sendApplianceState(window.RelayConfig.currentRoomId, appliance.id, false);
                    toggleInput.checked = false;
                }
            };
            update();
            window.RelayConfig.timerIntervals[appliance.id] = setInterval(update, 1000);
        } else {
            timerElement.classList.add('hidden');
            cancelButton.classList.add('hidden');
        }
    },

    // Update monitoring UI state
    updateMonitoringUIState() {
        const monitoringIndicators = document.querySelectorAll('.monitoring-indicator');
        monitoringIndicators.forEach(indicator => {
            if (window.RelayConfig.isGlobalMonitoring) {
                indicator.classList.add('global-active');
                indicator.setAttribute('title', 'Global monitoring is active');
            } else {
                indicator.classList.remove('global-active');
                indicator.removeAttribute('title');
            }
        });

        const roomControls = document.querySelectorAll('.room-specific-control');
        roomControls.forEach(control => {
            if (window.RelayConfig.isGlobalMonitoring) {
                control.classList.add('disabled-by-global');
                control.setAttribute('disabled', 'true');
            } else {
                control.classList.remove('disabled-by-global');
                control.removeAttribute('disabled');
            }
        });
    }
};
