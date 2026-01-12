/**
 * Main application module
 * Coordinates the UI, API calls, and globe visualization
 */

import { Globe } from './globe.js';
import { API } from './api.js';

class MarcusApp {
    constructor() {
        this.globe = null;
        this.items = [];
        this.modal = null;
        this.init();
    }

    async init() {
        // Initialize globe
        this.globe = new Globe('globe');
        this.globe.animate();

        // Initialize modal
        this.modal = document.getElementById('addItemModal');
        this.setupEventListeners();

        // Load initial data
        await this.checkAPIStatus();
        await this.loadItems();
    }

    setupEventListeners() {
        // Add item button
        document.getElementById('addItemBtn').addEventListener('click', () => {
            this.showModal();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadItems();
        });

        // Modal close button
        document.querySelector('.close').addEventListener('click', () => {
            this.hideModal();
        });

        // Cancel button
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.hideModal();
        });

        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === this.modal) {
                this.hideModal();
            }
        });

        // Form submission
        document.getElementById('addItemForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleFormSubmit(e);
        });
    }

    showModal() {
        this.modal.style.display = 'block';
        document.getElementById('addItemForm').reset();
    }

    hideModal() {
        this.modal.style.display = 'none';
    }

    async checkAPIStatus() {
        try {
            const health = await API.checkHealth();
            const statusElement = document.getElementById('apiStatus');
            statusElement.textContent = health.status === 'ok' ? '✓ Online' : '✗ Offline';
            statusElement.style.color = health.status === 'ok' ? '#00ff88' : '#ff0000';
        } catch (error) {
            const statusElement = document.getElementById('apiStatus');
            statusElement.textContent = '✗ Offline';
            statusElement.style.color = '#ff0000';
        }
    }

    async loadItems() {
        try {
            this.items = await API.getItems();
            this.updateItemsList();
            this.updateGlobeMarkers();
            document.getElementById('itemsCount').textContent = this.items.length;
        } catch (error) {
            console.error('Failed to load items:', error);
            this.showError('Failed to load items');
        }
    }

    updateItemsList() {
        const itemsList = document.getElementById('itemsList');
        
        if (this.items.length === 0) {
            itemsList.innerHTML = '<p style="text-align: center; color: #a0a0a0; padding: 20px;">No items yet. Add your first item!</p>';
            return;
        }

        itemsList.innerHTML = this.items.map(item => `
            <div class="item-card">
                <div class="item-name">${this.escapeHtml(item.name)}</div>
                ${item.description ? `<div class="item-description">${this.escapeHtml(item.description)}</div>` : ''}
                ${item.latitude !== null && item.longitude !== null ? 
                    `<div class="item-coords">📍 ${item.latitude.toFixed(2)}°, ${item.longitude.toFixed(2)}°</div>` : ''}
                <div class="item-actions">
                    <button class="neon-button secondary" onclick="app.deleteItem(${item.id})">Delete</button>
                </div>
            </div>
        `).join('');
    }

    updateGlobeMarkers() {
        this.globe.clearMarkers();
        
        for (const item of this.items) {
            if (item.latitude !== null && item.longitude !== null) {
                this.globe.addMarker(item.latitude, item.longitude, item.name);
            }
        }
    }

    async handleFormSubmit(event) {
        const formData = new FormData(event.target);
        const item = {
            name: formData.get('name'),
            description: formData.get('description') || null,
            latitude: formData.get('latitude') ? parseFloat(formData.get('latitude')) : null,
            longitude: formData.get('longitude') ? parseFloat(formData.get('longitude')) : null,
        };

        try {
            await API.createItem(item);
            this.hideModal();
            await this.loadItems();
            this.showSuccess('Item created successfully!');
        } catch (error) {
            console.error('Failed to create item:', error);
            this.showError('Failed to create item');
        }
    }

    async deleteItem(id) {
        if (!confirm('Are you sure you want to delete this item?')) {
            return;
        }

        try {
            await API.deleteItem(id);
            await this.loadItems();
            this.showSuccess('Item deleted successfully!');
        } catch (error) {
            console.error('Failed to delete item:', error);
            this.showError('Failed to delete item');
        }
    }

    showError(message) {
        // Simple alert for now, could be replaced with a toast notification
        alert('Error: ' + message);
    }

    showSuccess(message) {
        // Simple alert for now, could be replaced with a toast notification
        console.log('Success: ' + message);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
let app;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        app = new MarcusApp();
        window.app = app; // Make globally accessible for onclick handlers
    });
} else {
    app = new MarcusApp();
    window.app = app;
}

export default MarcusApp;
