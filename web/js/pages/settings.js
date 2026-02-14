const SettingsPage = {
    render() {
        const el = document.getElementById('page-settings');
        const expiry = B33Api.getTokenExpiry();

        el.innerHTML = `
            <div class="section-header"><h2>Settings</h2></div>
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="b33-card p-3">
                        <h6 class="text-muted mb-3">Server Configuration</h6>
                        <div class="mb-3">
                            <label class="form-label small">Server URL</label>
                            <input type="text" class="form-control form-control-sm" id="settings-url" value="${B33Utils.escapeHtml(B33Api.getServerUrl())}">
                        </div>
                        <div class="d-flex gap-2 align-items-center">
                            <button class="btn btn-sm btn-outline-primary" id="settings-save-url">Save</button>
                            <button class="btn btn-sm btn-outline-secondary" id="settings-test">Test Connection</button>
                            <span id="settings-status"></span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="b33-card p-3">
                        <h6 class="text-muted mb-3">Session</h6>
                        <p class="small mb-1"><strong>Token expires:</strong> ${expiry ? expiry.toLocaleString() : 'Unknown'}</p>
                        <p class="small mb-3"><strong>Server:</strong> ${B33Utils.escapeHtml(B33Api.getServerUrl())}</p>
                        <button class="btn btn-sm btn-outline-danger" id="settings-logout">Logout</button>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="b33-card p-3">
                        <h6 class="text-muted mb-3">About</h6>
                        <p class="small mb-1"><strong>B33</strong> - Portable Penetration Testing Device</p>
                        <p class="small mb-1">Educational use only</p>
                        <p class="small text-muted">Web Interface v1.0</p>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('settings-save-url').addEventListener('click', () => {
            const url = document.getElementById('settings-url').value.trim();
            if (url) {
                B33Api.setServerUrl(url);
                B33Utils.showToast('Server URL saved', 'success');
            }
        });

        document.getElementById('settings-test').addEventListener('click', async () => {
            const statusEl = document.getElementById('settings-status');
            statusEl.innerHTML = '<span class="spinner-border spinner-border-sm text-secondary"></span>';
            try {
                await B33Api.checkHealth();
                statusEl.innerHTML = '<span class="badge bg-success">Connected</span>';
            } catch {
                statusEl.innerHTML = '<span class="badge bg-danger">Failed</span>';
            }
        });

        document.getElementById('settings-logout').addEventListener('click', () => App.logout());
    }
};
