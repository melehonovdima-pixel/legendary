// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';
const TOKEN_KEY = 'auth_token';

// API Helper Class
class API {
    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    setToken(token) {
        localStorage.setItem(TOKEN_KEY, token);
    }

    removeToken() {
        localStorage.removeItem(TOKEN_KEY);
    }

    async request(endpoint, options = {}) {
        const token = this.getToken();
        
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            }
        };

        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            
            if (response.status === 401) {
                this.removeToken();
                window.location.href = 'index.html';
                return null;
            }

            if (response.status === 204) {
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth
    async register(username, password, fullname, address) {
        return this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, fullname, address })
        });
    }

    async login(username, password) {
        const data = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (data && data.access_token) {
            this.setToken(data.access_token);
        }
        
        return data;
    }

    async getCurrentUser() {
        return this.request('/api/auth/me');
    }

    // Users
    async getUsers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/users${queryString ? '?' + queryString : ''}`);
    }

    async updateUser(id, data) {
        return this.request(`/api/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async updateUserAdmin(id, data) {
        return this.request(`/api/users/${id}/admin`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Requests
    async getRequests(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/requests${queryString ? '?' + queryString : ''}`);
    }

    async createRequest(type, description) {
        return this.request('/api/requests', {
            method: 'POST',
            body: JSON.stringify({ type, description })
        });
    }

    async updateRequest(id, data) {
        return this.request(`/api/requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async assignExecutor(requestId, executorId) {
        return this.request(`/api/requests/${requestId}/assign`, {
            method: 'POST',
            body: JSON.stringify({ executor_id: executorId })
        });
    }

    // Stats
    async getDashboardStats() {
        return this.request('/api/stats/dashboard');
    }

    // Settings
    async getSettings() {
        return this.request('/api/settings');
    }

    async updateSetting(key, value) {
        return this.request(`/api/settings/${key}`, {
            method: 'PUT',
            body: JSON.stringify({ value })
        });
    }
}

const api = new API();
