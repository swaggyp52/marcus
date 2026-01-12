/**
 * Inbox UI Component - v0.47a
 *
 * Displays inbox items and provides Accept/Change/Snooze/Pin actions.
 * Integrates with Quick Add component for capture workflow.
 */

class InboxUI {
    constructor() {
        this.items = [];
        this.classes = [];
    }

    async init() {
        await this.loadClasses();
        await this.refresh();
    }

    async loadClasses() {
        try {
            const response = await fetch('/api/classes');
            if (response.ok) {
                this.classes = await response.json();
            }
        } catch (error) {
            console.error('Failed to load classes:', error);
        }
    }

    async refresh() {
        try {
            const response = await fetch('/api/inbox/items?status=inbox');
            if (!response.ok) throw new Error('Failed to load inbox items');

            this.items = await response.json();
            this.render();
            this.updateBadge();

        } catch (error) {
            console.error('Inbox refresh error:', error);
            this.renderError('Failed to load inbox items');
        }
    }

    render() {
        const container = document.getElementById('inboxList');

        if (this.items.length === 0) {
            container.innerHTML = `
                <div class="no-content">
                    <p style="font-size: 18px; margin-bottom: 10px;">📭 Inbox is empty</p>
                    <p>Use <strong>Ctrl+Shift+A</strong> to quickly add items</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.items.map(item => this.renderItem(item)).join('');
    }

    renderItem(item) {
        const classification = item.suggested_route_json ? JSON.parse(item.suggested_route_json) : null;
        const confidencePercent = item.confidence ? (item.confidence * 100).toFixed(0) : 0;
        const confidenceClass = item.confidence >= 0.75 ? 'high' : item.confidence >= 0.50 ? 'medium' : 'low';

        const contextLabel = this.formatContextLabel(item.context_kind, item.context_id);
        const typeLabel = item.item_type.charAt(0).toUpperCase() + item.item_type.slice(1);

        return `
            <div class="inbox-item" data-item-id="${item.id}">
                <div class="inbox-item-header">
                    <div class="inbox-item-title">
                        ${item.pinned ? '📌 ' : ''}${this.escapeHtml(item.title)}
                    </div>
                    <div class="inbox-item-badges">
                        <span class="badge badge-type">${typeLabel}</span>
                        <span class="badge badge-confidence badge-confidence-${confidenceClass}">
                            ${confidencePercent}% confident
                        </span>
                    </div>
                </div>

                ${item.content_md ? `
                    <div class="inbox-item-content">
                        ${this.escapeHtml(item.content_md.substring(0, 200))}${item.content_md.length > 200 ? '...' : ''}
                    </div>
                ` : ''}

                <div class="inbox-item-classification">
                    <div class="classification-info">
                        <span class="classification-label">Suggested route:</span>
                        <strong>${contextLabel}</strong>
                        ${classification && classification.reasoning ? `
                            <small style="display: block; color: #888; margin-top: 4px;">
                                ${this.escapeHtml(classification.reasoning)}
                            </small>
                        ` : ''}
                    </div>
                </div>

                <div class="inbox-item-actions">
                    <button class="btn btn-small btn-success" onclick="inboxUI.acceptItem(${item.id})">
                        ✓ Accept
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="inboxUI.showChangeDialog(${item.id})">
                        ↻ Change Route
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="inboxUI.showSnoozeDialog(${item.id})">
                        💤 Snooze
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="inboxUI.togglePin(${item.id}, ${!item.pinned})">
                        ${item.pinned ? '📌 Unpin' : '📌 Pin'}
                    </button>
                    <button class="btn btn-small btn-danger" onclick="inboxUI.deleteItem(${item.id})">
                        Delete
                    </button>
                </div>

                <div class="inbox-item-meta">
                    <span>Created ${new Date(item.created_at).toLocaleString()}</span>
                    ${item.tags && item.tags.length > 0 ? `
                        <span class="inbox-tags">
                            ${item.tags.map(tag => `<span class="tag">#${tag}</span>`).join(' ')}
                        </span>
                    ` : ''}
                </div>
            </div>
        `;
    }

    formatContextLabel(contextKind, contextId) {
        if (contextKind === 'class' && contextId) {
            const cls = this.classes.find(c => c.id === contextId);
            return cls ? `📚 ${cls.class_code || cls.name}` : `Class #${contextId}`;
        } else if (contextKind === 'project' && contextId) {
            return `🛠️ Project #${contextId}`;
        } else if (contextKind === 'personal') {
            return '👤 Personal';
        } else {
            return '📂 General';
        }
    }

    async acceptItem(itemId) {
        try {
            const response = await fetch('/api/inbox/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId })
            });

            if (!response.ok) throw new Error('Failed to accept item');

            this.showToast('Item filed successfully', 'success');
            await this.refresh();

        } catch (error) {
            console.error('Accept error:', error);
            this.showToast('Failed to accept item', 'error');
        }
    }

    showChangeDialog(itemId) {
        const item = this.items.find(i => i.id === itemId);
        if (!item) return;

        const classOptions = this.classes.map(c =>
            `<option value="${c.id}">${c.class_code || c.name}</option>`
        ).join('');

        const dialog = `
            <div class="modal-overlay" id="changeRouteModal" onclick="if(event.target === this) this.remove()">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Change Route</h3>
                        <button class="modal-close" onclick="document.getElementById('changeRouteModal').remove()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p style="margin-bottom: 15px;">Reclassify item: <strong>${this.escapeHtml(item.title)}</strong></p>

                        <div class="form-group">
                            <label>Context Type</label>
                            <select id="changeContextKind" class="form-control">
                                <option value="class">Class</option>
                                <option value="project">Project</option>
                                <option value="personal">Personal</option>
                                <option value="none">General</option>
                            </select>
                        </div>

                        <div class="form-group" id="changeContextIdGroup">
                            <label>Class</label>
                            <select id="changeContextId" class="form-control">
                                <option value="">Select class...</option>
                                ${classOptions}
                            </select>
                        </div>

                        <div class="button-group">
                            <button class="btn btn-primary" onclick="inboxUI.submitChangeRoute(${itemId})">Save</button>
                            <button class="btn btn-secondary" onclick="document.getElementById('changeRouteModal').remove()">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialog);

        // Handle context kind change
        document.getElementById('changeContextKind').addEventListener('change', (e) => {
            const contextIdGroup = document.getElementById('changeContextIdGroup');
            contextIdGroup.style.display = e.target.value === 'class' ? 'block' : 'none';
        });
    }

    async submitChangeRoute(itemId) {
        const contextKind = document.getElementById('changeContextKind').value;
        const contextId = contextKind === 'class' ? parseInt(document.getElementById('changeContextId').value) || null : null;

        try {
            const response = await fetch('/api/inbox/change-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    item_id: itemId,
                    context_kind: contextKind,
                    context_id: contextId
                })
            });

            if (!response.ok) throw new Error('Failed to change route');

            document.getElementById('changeRouteModal').remove();
            this.showToast('Route changed successfully', 'success');
            await this.refresh();

        } catch (error) {
            console.error('Change route error:', error);
            this.showToast('Failed to change route', 'error');
        }
    }

    showSnoozeDialog(itemId) {
        const item = this.items.find(i => i.id === itemId);
        if (!item) return;

        const now = new Date();
        const presets = [
            { label: 'Later today (6pm)', hours: 18 - now.getHours() },
            { label: 'Tomorrow morning (9am)', hours: 24 + (9 - now.getHours()) },
            { label: 'Next week', hours: 7 * 24 },
        ];

        const dialog = `
            <div class="modal-overlay" id="snoozeModal" onclick="if(event.target === this) this.remove()">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Snooze Item</h3>
                        <button class="modal-close" onclick="document.getElementById('snoozeModal').remove()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p style="margin-bottom: 15px;">Snooze until:</p>

                        <div class="button-group" style="flex-direction: column; align-items: stretch;">
                            ${presets.map(preset => `
                                <button class="btn btn-secondary" onclick="inboxUI.snoozeItem(${itemId}, ${preset.hours})">
                                    ${preset.label}
                                </button>
                            `).join('')}
                        </div>

                        <button class="btn btn-secondary" onclick="document.getElementById('snoozeModal').remove()" style="margin-top: 10px; width: 100%;">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialog);
    }

    async snoozeItem(itemId, hours) {
        const snoozeUntil = new Date(Date.now() + hours * 60 * 60 * 1000).toISOString();

        try {
            const response = await fetch('/api/inbox/snooze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId, snooze_until: snoozeUntil })
            });

            if (!response.ok) throw new Error('Failed to snooze item');

            document.getElementById('snoozeModal')?.remove();
            this.showToast('Item snoozed', 'success');
            await this.refresh();

        } catch (error) {
            console.error('Snooze error:', error);
            this.showToast('Failed to snooze item', 'error');
        }
    }

    async togglePin(itemId, pinned) {
        try {
            const response = await fetch('/api/inbox/pin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId, pinned })
            });

            if (!response.ok) throw new Error('Failed to toggle pin');

            this.showToast(pinned ? 'Item pinned' : 'Item unpinned', 'success');
            await this.refresh();

        } catch (error) {
            console.error('Pin toggle error:', error);
            this.showToast('Failed to toggle pin', 'error');
        }
    }

    async deleteItem(itemId) {
        if (!confirm('Delete this item permanently?')) return;

        try {
            const response = await fetch(`/api/inbox/items/${itemId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to delete item');

            this.showToast('Item deleted', 'success');
            await this.refresh();

        } catch (error) {
            console.error('Delete error:', error);
            this.showToast('Failed to delete item', 'error');
        }
    }

    updateBadge() {
        const badge = document.getElementById('inboxCountBadge');
        if (badge) {
            badge.textContent = this.items.length;
            badge.style.display = this.items.length > 0 ? 'inline' : 'none';
        }
    }

    renderError(message) {
        const container = document.getElementById('inboxList');
        container.innerHTML = `
            <div class="error-message">
                <p>${this.escapeHtml(message)}</p>
                <button class="btn btn-secondary" onclick="inboxUI.refresh()">Retry</button>
            </div>
        `;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('quick-add-toast-container') || this.createToastContainer();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} show`;
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</div>
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'quick-add-toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.inboxUI = new InboxUI();
    });
} else {
    window.inboxUI = new InboxUI();
}
