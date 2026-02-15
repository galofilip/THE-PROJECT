const B33Api = {
    _serverUrl: localStorage.getItem('b33_server_url') || '',
    _token: localStorage.getItem('b33_token') || null,

    setServerUrl(url) {
        this._serverUrl = url.replace(/\/+$/, '');
        localStorage.setItem('b33_server_url', this._serverUrl);
    },

    getServerUrl() {
        return this._serverUrl;
    },

    async login(username, password) {
        const res = await fetch(this._serverUrl + '/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || 'Login failed');
        }
        const data = await res.json();
        this._token = data.token;
        localStorage.setItem('b33_token', this._token);
        return data;
    },

    logout() {
        this._token = null;
        localStorage.removeItem('b33_token');
    },

    isAuthenticated() {
        if (!this._token) return false;
        try {
            const payload = JSON.parse(atob(this._token.split('.')[1]));
            return payload.exp > Date.now() / 1000;
        } catch {
            return false;
        }
    },

    getTokenExpiry() {
        if (!this._token) return null;
        try {
            const payload = JSON.parse(atob(this._token.split('.')[1]));
            return new Date(payload.exp * 1000);
        } catch {
            return null;
        }
    },

    async _fetch(path, options = {}) {
        const url = this._serverUrl + path;
        const headers = { ...(options.headers || {}) };

        if (this._token) {
            headers['Authorization'] = 'Bearer ' + this._token;
        }
        if (options.method && options.method !== 'GET' && options.body) {
            headers['Content-Type'] = 'application/json';
        }

        let res;
        try {
            res = await fetch(url, { ...options, headers });
        } catch (e) {
            throw new Error('Network error - is the server running?');
        }

        if (res.status === 401) {
            this.logout();
            if (typeof App !== 'undefined') App.showLogin();
            throw new Error('Session expired - please login again');
        }

        const data = await res.json().catch(() => ({}));
        if (data.error) throw new Error(data.error);
        if (!res.ok) throw new Error(data.message || 'Request failed');
        return data;
    },

    // Health
    async checkHealth() {
        const res = await fetch(this._serverUrl + '/api/health');
        return await res.json();
    },

    // Private Scans
    async getPrivateScans(filters = {}) {
        const params = new URLSearchParams();
        if (filters.risk_level) params.set('risk_level', filters.risk_level);
        if (filters.network_ssid) params.set('network_ssid', filters.network_ssid);
        const qs = params.toString();
        return this._fetch('/api/scans/private' + (qs ? '?' + qs : ''));
    },

    async deletePrivateScan(scanId) {
        return this._fetch('/api/scans/private/' + scanId, { method: 'DELETE' });
    },

    // Public Scans
    async getPublicScans(filters = {}) {
        const params = new URLSearchParams();
        if (filters.risk_level) params.set('risk_level', filters.risk_level);
        if (filters.country_code) params.set('country_code', filters.country_code);
        if (filters.scan_batch_id) params.set('scan_batch_id', filters.scan_batch_id);
        const qs = params.toString();
        return this._fetch('/api/scans/public' + (qs ? '?' + qs : ''));
    },

    async deletePublicScan(scanId) {
        return this._fetch('/api/scans/public/' + scanId, { method: 'DELETE' });
    },

    // Tasks
    async getTasks(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.set('status', filters.status);
        if (filters.assigned_to) params.set('assigned_to', filters.assigned_to);
        const qs = params.toString();
        return this._fetch('/api/tasks' + (qs ? '?' + qs : ''));
    },

    async createTask(data) {
        return this._fetch('/api/tasks', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateTask(taskId, data) {
        return this._fetch('/api/tasks/' + taskId, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    // Infected PCs
    async getInfected(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.set('status', filters.status);
        const qs = params.toString();
        return this._fetch('/api/c2/infected' + (qs ? '?' + qs : ''));
    },

    async updateInfected(pcId, data) {
        return this._fetch('/api/c2/infected/' + pcId, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    async deleteInfected(pcId) {
        return this._fetch('/api/c2/infected/' + pcId, { method: 'DELETE' });
    },

    async sendCommand(pcId, commandType, commandData) {
        return this._fetch('/api/c2/infected/' + pcId + '/command', {
            method: 'POST',
            body: JSON.stringify({ command_type: commandType, command_data: commandData || null })
        });
    },

    // Logs
    async getExploitLogs(filters = {}) {
        const params = new URLSearchParams();
        if (filters.target_ip) params.set('target_ip', filters.target_ip);
        if (filters.success !== undefined && filters.success !== '') params.set('success', filters.success);
        const qs = params.toString();
        return this._fetch('/api/logs/exploits' + (qs ? '?' + qs : ''));
    },

    async getC2Logs(filters = {}) {
        const params = new URLSearchParams();
        if (filters.pc_id) params.set('pc_id', filters.pc_id);
        if (filters.status) params.set('status', filters.status);
        const qs = params.toString();
        return this._fetch('/api/logs/c2' + (qs ? '?' + qs : ''));
    }
};
