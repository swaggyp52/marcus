/**
 * Inbox Keyboard Navigation & Bulk Actions - v0.48
 * 
 * Keyboard bindings:
 * - j/k or arrow down/up: move selection
 * - Enter: open item
 * - A: accept
 * - C: change context
 * - S: snooze
 * - P: pin
 * - D: delete (with confirm)
 * - Ctrl+A: select all
 * - Shift+Click: multi-select range
 */

class InboxKeyboardController {
    constructor(containerId = 'inboxList') {
        this.container = document.getElementById(containerId);
        this.selectedIndices = new Set();
        this.focusedIndex = 0;
        this.items = [];
        
        this.setupKeyBindings();
        this.setupMouseSelection();
    }

    setupKeyBindings() {
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    setupMouseSelection() {
        if (!this.container) return;
        
        this.container.addEventListener('click', (e) => {
            const itemEl = e.target.closest('[data-item-id]');
            if (!itemEl) return;

            const itemId = itemEl.getAttribute('data-item-id');
            const index = this.items.findIndex(i => i.id == itemId);
            
            if (e.ctrlKey || e.metaKey) {
                this.toggleSelection(index);
            } else if (e.shiftKey) {
                this.selectRange(this.focusedIndex, index);
            } else {
                this.focusItem(index);
            }
        });
    }

    handleKeyDown(e) {
        // Don't trigger in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            // Allow Ctrl+A in inputs
            if (!(e.ctrlKey && e.key === 'a')) return;
        }

        const key = e.key.toLowerCase();

        // Navigation
        if (key === 'j' || e.code === 'ArrowDown') {
            e.preventDefault();
            this.moveFocus(1);
        } else if (key === 'k' || e.code === 'ArrowUp') {
            e.preventDefault();
            this.moveFocus(-1);
        }
        
        // Actions (only if something is selected)
        else if (this.selectedIndices.size > 0 || this.focusedIndex >= 0) {
            switch (key) {
                case 'enter':
                    e.preventDefault();
                    this.openSelected();
                    break;
                case 'a':
                    e.preventDefault();
                    this.acceptSelected();
                    break;
                case 'c':
                    e.preventDefault();
                    this.changeContextSelected();
                    break;
                case 's':
                    e.preventDefault();
                    this.snoozeSelected();
                    break;
                case 'p':
                    e.preventDefault();
                    this.pinSelected();
                    break;
                case 'd':
                    e.preventDefault();
                    this.deleteSelected();
                    break;
            }
        }

        // Select all
        if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            this.selectAll();
        }
    }

    moveFocus(direction) {
        const newIndex = Math.max(0, Math.min(this.items.length - 1, this.focusedIndex + direction));
        this.focusItem(newIndex);
    }

    focusItem(index) {
        this.focusedIndex = Math.max(0, Math.min(this.items.length - 1, index));
        this.updateUI();
    }

    toggleSelection(index) {
        if (this.selectedIndices.has(index)) {
            this.selectedIndices.delete(index);
        } else {
            this.selectedIndices.add(index);
        }
        this.updateUI();
    }

    selectRange(from, to) {
        const start = Math.min(from, to);
        const end = Math.max(from, to);
        
        for (let i = start; i <= end; i++) {
            this.selectedIndices.add(i);
        }
        this.focusedIndex = to;
        this.updateUI();
    }

    selectAll() {
        for (let i = 0; i < this.items.length; i++) {
            this.selectedIndices.add(i);
        }
        this.updateUI();
    }

    updateUI() {
        const items = this.container?.querySelectorAll('[data-item-id]');
        if (!items) return;

        items.forEach((el, idx) => {
            el.classList.toggle('focused', idx === this.focusedIndex);
            el.classList.toggle('selected', this.selectedIndices.has(idx));
        });
    }

    getSelectedItems() {
        const indices = this.selectedIndices.size > 0 ? 
            Array.from(this.selectedIndices) : 
            [this.focusedIndex];
        
        return indices.map(i => this.items[i]).filter(Boolean);
    }

    // Action handlers
    async openSelected() {
        const items = this.getSelectedItems();
        if (items.length !== 1) return;
        
        const item = items[0];
        // Dispatch custom event for app to handle
        document.dispatchEvent(new CustomEvent('inboxItemOpen', { detail: { item } }));
    }

    async acceptSelected() {
        const items = this.getSelectedItems();
        if (items.length === 0) return;

        try {
            await apiCall('/inbox/bulk/accept', {
                method: 'POST',
                body: JSON.stringify({ item_ids: items.map(i => i.id) })
            });
            showSuccess(`Accepted ${items.length} item(s)`);
            await refreshInboxUI();
        } catch (error) {
            showError('Failed to accept items');
        }
    }

    async changeContextSelected() {
        const items = this.getSelectedItems();
        if (items.length === 0) return;

        const context = prompt('Change context to:');
        if (!context) return;

        try {
            for (const item of items) {
                await apiCall(`/inbox/${item.id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ context })
                });
            }
            showSuccess(`Changed context for ${items.length} item(s)`);
            await refreshInboxUI();
        } catch (error) {
            showError('Failed to change context');
        }
    }

    async snoozeSelected() {
        const items = this.getSelectedItems();
        if (items.length === 0) return;

        const minutes = prompt('Snooze for how many minutes?', '30');
        if (!minutes) return;

        try {
            await apiCall('/inbox/bulk/snooze', {
                method: 'POST',
                body: JSON.stringify({
                    item_ids: items.map(i => i.id),
                    minutes: parseInt(minutes)
                })
            });
            showSuccess(`Snoozed ${items.length} item(s)`);
            await refreshInboxUI();
        } catch (error) {
            showError('Failed to snooze items');
        }
    }

    async pinSelected() {
        const items = this.getSelectedItems();
        if (items.length === 0) return;

        try {
            for (const item of items) {
                const newPinned = !item.pinned;
                await apiCall(`/inbox/${item.id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ pinned: newPinned })
                });
            }
            showSuccess(`Updated pins for ${items.length} item(s)`);
            await refreshInboxUI();
        } catch (error) {
            showError('Failed to update pins');
        }
    }

    async deleteSelected() {
        const items = this.getSelectedItems();
        if (items.length === 0) return;

        if (!confirm(`Delete ${items.length} item(s)? (This can be undone for 10 seconds)`)) {
            return;
        }

        try {
            for (const item of items) {
                await apiCall(`/inbox/${item.id}`, {
                    method: 'DELETE'
                });
            }
            showSuccess(`Deleted ${items.length} item(s). [Undo]`);
            await refreshInboxUI();
        } catch (error) {
            showError('Failed to delete items');
        }
    }

    setItems(items) {
        this.items = items;
        this.selectedIndices.clear();
        this.focusedIndex = 0;
        this.updateUI();
    }
}

// Export for use in app.js
window.InboxKeyboardController = InboxKeyboardController;
