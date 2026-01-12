/**
 * Quick Add Component - v0.47a
 *
 * Global capture bar with auto-classification.
 * Ctrl+Shift+A to activate anywhere in Marcus.
 *
 * Flow:
 * 1. User types/pastes content
 * 2. Item auto-classified via backend
 * 3. If confidence >= 0.90: auto-filed with toast + undo
 * 4. If confidence < 0.90: sent to inbox for review
 */

class QuickAdd {
    constructor() {
        this.isVisible = false;
        this.undoTimer = null;
        this.lastAutoFiledItem = null;

        this.init();
    }

    init() {
        this.createUI();
        this.bindKeyboardShortcut();
    }

    createUI() {
        // Quick Add overlay
        const overlay = document.createElement('div');
        overlay.id = 'quick-add-overlay';
        overlay.className = 'quick-add-overlay hidden';
        overlay.innerHTML = `
            <div class="quick-add-container">
                <div class="quick-add-header">
                    <h3>Quick Add</h3>
                    <span class="quick-add-shortcut">Ctrl+Shift+A</span>
                    <button class="quick-add-close" aria-label="Close">&times;</button>
                </div>

                <div class="quick-add-body">
                    <textarea
                        id="quick-add-input"
                        placeholder="Type anything... Marcus will figure out where it goes.&#10;&#10;Examples:&#10;• Notes: 'Studied PHYS214 chapter 3 on momentum'&#10;• Tasks: 'Submit ECE347 homework by Friday'&#10;• Events: 'Office hours tomorrow at 2pm'&#10;• Documents: Just paste or drag files"
                        rows="6"
                    ></textarea>

                    <div class="quick-add-actions">
                        <button id="quick-add-submit" class="btn btn-primary">
                            Add <span class="shortcut-hint">Enter</span>
                        </button>
                        <span class="quick-add-hint">Marcus will auto-classify and route this</span>
                    </div>
                </div>

                <div class="quick-add-status hidden" id="quick-add-status"></div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Toast notification container
        const toastContainer = document.createElement('div');
        toastContainer.id = 'quick-add-toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);

        // Bind events
        overlay.querySelector('.quick-add-close').addEventListener('click', () => this.hide());
        overlay.querySelector('#quick-add-submit').addEventListener('click', () => this.submit());

        const input = overlay.querySelector('#quick-add-input');
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.submit();
            } else if (e.key === 'Escape') {
                this.hide();
            }
        });

        // Click outside to close
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.hide();
            }
        });
    }

    bindKeyboardShortcut() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+A (or Cmd+Shift+A on Mac)
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.show();
            }
        });
    }

    show() {
        const overlay = document.getElementById('quick-add-overlay');
        overlay.classList.remove('hidden');

        // Focus input
        const input = document.getElementById('quick-add-input');
        input.focus();
        input.select();

        this.isVisible = true;
    }

    hide() {
        const overlay = document.getElementById('quick-add-overlay');
        overlay.classList.add('hidden');

        // Clear input
        document.getElementById('quick-add-input').value = '';
        document.getElementById('quick-add-status').classList.add('hidden');

        this.isVisible = false;
    }

    async submit() {
        const input = document.getElementById('quick-add-input');
        const text = input.value.trim();

        if (!text) {
            this.showStatus('Please enter some content', 'error');
            return;
        }

        this.showStatus('Processing...', 'loading');

        try {
            const response = await fetch('/api/inbox/quick-add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Failed to add item');
            }

            const result = await response.json();

            if (result.auto_filed) {
                // Auto-filed: show success toast with undo option
                this.lastAutoFiledItem = result;
                this.showAutoFiledToast(result);
                this.hide();
            } else {
                // Sent to inbox: show message and optionally redirect
                this.showStatus('Added to inbox for review', 'success');
                setTimeout(() => {
                    this.hide();
                    // Optionally navigate to inbox
                    if (window.confirm('Item sent to inbox. View now?')) {
                        this.navigateToInbox();
                    }
                }, 1500);
            }

        } catch (error) {
            console.error('Quick Add error:', error);
            this.showStatus('Failed to add item. Please try again.', 'error');
        }
    }

    showStatus(message, type) {
        const status = document.getElementById('quick-add-status');
        status.textContent = message;
        status.className = 'quick-add-status ' + type;
        status.classList.remove('hidden');
    }

    showAutoFiledToast(result) {
        const container = document.getElementById('quick-add-toast-container');

        const toast = document.createElement('div');
        toast.className = 'toast toast-success';

        const classification = result.classification;
        const contextLabel = this.formatContextLabel(classification.context_kind, classification.context_id);

        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">✓</div>
                <div class="toast-message">
                    <strong>Auto-filed</strong>
                    <span>${classification.item_type} → ${contextLabel}</span>
                    <small>Confidence: ${(classification.confidence * 100).toFixed(0)}%</small>
                </div>
                <button class="toast-undo" data-item-id="${result.item_id}">Undo</button>
            </div>
            <div class="toast-progress"></div>
        `;

        container.appendChild(toast);

        // Bind undo button
        const undoBtn = toast.querySelector('.toast-undo');
        undoBtn.addEventListener('click', () => {
            this.undoAutoFile(result.item_id);
            this.removeToast(toast);
        });

        // Auto-remove after 10 seconds
        this.undoTimer = setTimeout(() => {
            this.removeToast(toast);
        }, 10000);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
    }

    removeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);

        if (this.undoTimer) {
            clearTimeout(this.undoTimer);
            this.undoTimer = null;
        }
    }

    async undoAutoFile(itemId) {
        try {
            // Move item back to inbox
            await fetch(`/api/inbox/items/${itemId}`, {
                method: 'DELETE'
            });

            this.showUndoConfirmation();

        } catch (error) {
            console.error('Undo error:', error);
            alert('Failed to undo. The item may have been filed.');
        }
    }

    showUndoConfirmation() {
        const container = document.getElementById('quick-add-toast-container');

        const toast = document.createElement('div');
        toast.className = 'toast toast-info show';
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">↶</div>
                <div class="toast-message">Item removed</div>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    formatContextLabel(contextKind, contextId) {
        if (contextKind === 'class' && contextId) {
            // TODO: Fetch class name from cache or API
            return `Class #${contextId}`;
        } else if (contextKind === 'project' && contextId) {
            return `Project #${contextId}`;
        } else if (contextKind === 'personal') {
            return 'Personal';
        } else {
            return 'General';
        }
    }

    navigateToInbox() {
        // Trigger inbox navigation
        if (window.MarcusApp && window.MarcusApp.showInbox) {
            window.MarcusApp.showInbox();
        }
    }
}

// Initialize Quick Add when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.QuickAdd = new QuickAdd();
    });
} else {
    window.QuickAdd = new QuickAdd();
}
