/**
 * Trust Bar / Safety Strip - v0.48
 *
 * Persistent component showing:
 * - Offline/Online mode
 * - "No background actions" guarantee
 * - Undo available indicator
 * - Link to Audit Log
 */

class TrustBar {
    constructor() {
        this.isOnlineMode = false;
        this.undoAvailable = false;
        this.undoSecondsRemaining = 0;
        this.undoCountdownInterval = null;
    }

    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Trust bar container not found');
            return;
        }

        this.render();
        this.startStatusPolling();
    }

    render() {
        this.container.innerHTML = `
            <div class="trust-bar">
                <div class="trust-bar-left">
                    <div class="trust-indicator">
                        <span class="trust-badge" id="trustOnlineMode">
                            <span class="badge-dot">●</span>
                            OFFLINE
                        </span>
                    </div>
                    <div class="trust-statement">
                        ✓ No background actions
                    </div>
                </div>

                <div class="trust-bar-right">
                    <div class="trust-undo" id="trustUndo" style="display: none;">
                        <button class="trust-undo-btn" onclick="undoLastAction()">
                            ↶ Undo
                            <span class="undo-countdown" id="undoCountdown"></span>
                        </button>
                    </div>
                    <div class="trust-links">
                        <a href="/audit" class="trust-link">Audit Log</a>
                    </div>
                </div>
            </div>
        `;

        // Sync with global online mode state
        this.syncOnlineMode();
    }

    /**
     * Start polling for system status (undo, online mode)
     */
    startStatusPolling() {
        // Poll every 500ms for undo status
        setInterval(() => this.updateUndoStatus(), 500);
    }

    /**
     * Update undo status from backend
     */
    async updateUndoStatus() {
        try {
            const response = await fetch('/api/undo/status');
            if (!response.ok) return;

            const status = await response.json();
            this.setUndoStatus(status);
        } catch (e) {
            // Graceful failure
        }
    }

    /**
     * Set undo status based on API response
     */
    setUndoStatus(status) {
        const undoEl = document.getElementById('trustUndo');
        const countdownEl = document.getElementById('undoCountdown');

        if (status.undo_available) {
            if (undoEl) {
                undoEl.style.display = 'block';
            }

            // Update countdown
            if (countdownEl && status.seconds_remaining > 0) {
                countdownEl.textContent = `(${status.seconds_remaining}s)`;
            }

            this.undoAvailable = true;
            this.undoSecondsRemaining = status.seconds_remaining;
        } else {
            if (undoEl) {
                undoEl.style.display = 'none';
            }
            this.undoAvailable = false;
        }
    }

    /**
     * Sync with online mode toggle
     */
    syncOnlineMode() {
        const badge = document.getElementById('trustOnlineMode');
        if (!badge) return;

        // Check global onlineMode variable (from app.js)
        if (typeof onlineMode !== 'undefined' && onlineMode) {
            badge.textContent = '🌐 ONLINE';
            badge.classList.add('online');
        } else {
            badge.textContent = '● OFFLINE';
            badge.classList.remove('online');
        }
    }

    /**
     * Update online mode display
     */
    setOnlineMode(isOnline) {
        this.isOnlineMode = isOnline;
        this.syncOnlineMode();
    }
}

// Initialize trust bar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.trustBar = new TrustBar();
        window.trustBar.init('trustBarContainer');
    });
} else {
    window.trustBar = new TrustBar();
    window.trustBar.init('trustBarContainer');
}

/**
 * Global undo function (called from trust bar button)
 */
async function undoLastAction() {
    try {
        const response = await fetch('/api/undo/last', { method: 'POST' });
        if (!response.ok) return;

        const result = await response.json();
        if (result.success) {
            showSuccess(`Undid: ${result.message}`);
            // Refresh UI
            if (window.agentChat) {
                window.agentChat.addMessage({
                    type: 'system',
                    message: `✓ Undid: ${result.message}`,
                    timestamp: new Date()
                });
            }
        } else {
            showError(result.message);
        }
    } catch (e) {
        console.error('Undo failed:', e);
        showError('Undo failed. Please try again.');
    }
}
