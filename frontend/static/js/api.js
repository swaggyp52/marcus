/**
 * API module for communicating with the FastAPI backend
 */

const API_BASE = '/api';

export class API {
    static async checkHealth() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            throw error;
        }
    }

    static async getItems() {
        try {
            const response = await fetch(`${API_BASE}/items`);
            if (!response.ok) throw new Error('Failed to fetch items');
            return await response.json();
        } catch (error) {
            console.error('Failed to get items:', error);
            throw error;
        }
    }

    static async createItem(item) {
        try {
            const response = await fetch(`${API_BASE}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(item),
            });
            if (!response.ok) throw new Error('Failed to create item');
            return await response.json();
        } catch (error) {
            console.error('Failed to create item:', error);
            throw error;
        }
    }

    static async updateItem(id, item) {
        try {
            const response = await fetch(`${API_BASE}/items/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(item),
            });
            if (!response.ok) throw new Error('Failed to update item');
            return await response.json();
        } catch (error) {
            console.error('Failed to update item:', error);
            throw error;
        }
    }

    static async deleteItem(id) {
        try {
            const response = await fetch(`${API_BASE}/items/${id}`, {
                method: 'DELETE',
            });
            if (!response.ok) throw new Error('Failed to delete item');
            return await response.json();
        } catch (error) {
            console.error('Failed to delete item:', error);
            throw error;
        }
    }
}
