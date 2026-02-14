const LogsPage = {
    async render() {
        const el = document.getElementById('page-logs');
        el.innerHTML = `
            <div class="section-header"><h2>Logs</h2></div>
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#tab-exploit-logs">Exploitation Logs</a></li>
                <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-c2-logs">C2 Command Logs</a></li>
            </ul>
            <div class="tab-content">
                <div class="tab-pane fade show active" id="tab-exploit-logs">
                    <div class="filter-bar mt-3">
                        <div class="row g-2 align-items-end">
                            <div class="col-auto">
                                <label class="form-label small text-muted">Target IP</label>
                                <input type="text" class="form-control form-control-sm" id="log-exploit-ip" placeholder="IP address">
                            </div>
                            <div class="col-auto">
                                <label class="form-label small text-muted">Success</label>
                                <select class="form-select form-select-sm" id="log-exploit-success">
                                    <option value="">All</option>
                                    <option value="1">Yes</option>
                                    <option value="0">No</option>
                                </select>
                            </div>
                            <div class="col-auto">
                                <button class="btn btn-sm btn-outline-primary" id="log-exploit-filter">Filter</button>
                                <button class="btn btn-sm btn-outline-secondary" id="log-exploit-clear">Clear</button>
                            </div>
                        </div>
                    </div>
                    <div id="exploit-logs-container">${B33Utils.loading()}</div>
                </div>
                <div class="tab-pane fade" id="tab-c2-logs">
                    <div class="filter-bar mt-3">
                        <div class="row g-2 align-items-end">
                            <div class="col-auto">
                                <label class="form-label small text-muted">PC ID</label>
                                <input type="text" class="form-control form-control-sm" id="log-c2-pcid" placeholder="PC ID">
                            </div>
                            <div class="col-auto">
                                <label class="form-label small text-muted">Status</label>
                                <select class="form-select form-select-sm" id="log-c2-status">
                                    <option value="">All</option>
                                    <option value="sent">Sent</option>
                                    <option value="received">Received</option>
                                    <option value="completed">Completed</option>
                                    <option value="failed">Failed</option>
                                </select>
                            </div>
                            <div class="col-auto">
                                <button class="btn btn-sm btn-outline-primary" id="log-c2-filter">Filter</button>
                                <button class="btn btn-sm btn-outline-secondary" id="log-c2-clear">Clear</button>
                            </div>
                        </div>
                    </div>
                    <div id="c2-logs-container">${B33Utils.loading()}</div>
                </div>
            </div>
        `;

        // Exploit log handlers
        document.getElementById('log-exploit-filter').addEventListener('click', () => this._loadExploitLogs());
        document.getElementById('log-exploit-clear').addEventListener('click', () => {
            document.getElementById('log-exploit-ip').value = '';
            document.getElementById('log-exploit-success').value = '';
            this._loadExploitLogs();
        });

        // C2 log handlers
        document.getElementById('log-c2-filter').addEventListener('click', () => this._loadC2Logs());
        document.getElementById('log-c2-clear').addEventListener('click', () => {
            document.getElementById('log-c2-pcid').value = '';
            document.getElementById('log-c2-status').value = '';
            this._loadC2Logs();
        });

        // Load on tab switch
        document.querySelector('[href="#tab-c2-logs"]').addEventListener('shown.bs.tab', () => this._loadC2Logs());

        await this._loadExploitLogs();
    },

    async _loadExploitLogs() {
        const container = document.getElementById('exploit-logs-container');
        container.innerHTML = B33Utils.loading();
        try {
            const filters = {
                target_ip: document.getElementById('log-exploit-ip').value.trim(),
                success: document.getElementById('log-exploit-success').value
            };
            const res = await B33Api.getExploitLogs(filters);
            const logs = res.data || [];
            if (logs.length === 0) { container.innerHTML = B33Utils.emptyState('No exploitation logs'); return; }

            container.innerHTML = `
                <div class="table-responsive">
                    <table class="table b33-table table-sm">
                        <thead><tr><th>Date</th><th>Target</th><th>CVE</th><th>Method</th><th>Success</th><th>Backdoor</th><th>PC ID</th><th>Error</th></tr></thead>
                        <tbody>
                            ${logs.map(l => `
                                <tr>
                                    <td>${B33Utils.formatDate(l.created_at)}</td>
                                    <td class="mono">${B33Utils.escapeHtml(l.target_ip)}</td>
                                    <td>${B33Utils.escapeHtml(B33Utils.deref(l.vulnerability_id))}</td>
                                    <td>${B33Utils.escapeHtml(B33Utils.deref(l.exploit_method))}</td>
                                    <td>${l.success ? '<span class="text-success">YES</span>' : '<span class="text-danger">NO</span>'}</td>
                                    <td>${l.backdoor_deployed ? '<span class="text-success">YES</span>' : '<span class="text-muted">NO</span>'}</td>
                                    <td class="mono">${B33Utils.escapeHtml(B33Utils.deref(l.pc_id))}</td>
                                    <td>${B33Utils.escapeHtml(B33Utils.deref(l.error_message))}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${B33Utils.escapeHtml(err.message)}</div>`;
        }
    },

    async _loadC2Logs() {
        const container = document.getElementById('c2-logs-container');
        container.innerHTML = B33Utils.loading();
        try {
            const filters = {
                pc_id: document.getElementById('log-c2-pcid').value.trim(),
                status: document.getElementById('log-c2-status').value
            };
            const res = await B33Api.getC2Logs(filters);
            const logs = res.data || [];
            if (logs.length === 0) { container.innerHTML = B33Utils.emptyState('No C2 command logs'); return; }

            container.innerHTML = `
                <div class="table-responsive">
                    <table class="table b33-table table-sm">
                        <thead><tr><th>Date</th><th>PC ID</th><th>Type</th><th>Command</th><th>Status</th><th>Result</th><th>Completed</th></tr></thead>
                        <tbody>
                            ${logs.map(l => `
                                <tr>
                                    <td>${B33Utils.formatDate(l.created_at)}</td>
                                    <td class="mono">${B33Utils.escapeHtml(l.pc_id)}</td>
                                    <td><span class="badge bg-secondary">${B33Utils.escapeHtml(l.command_type)}</span></td>
                                    <td class="mono">${B33Utils.escapeHtml(B33Utils.truncate(B33Utils.deref(l.command_data), 40))}</td>
                                    <td>${B33Utils.statusBadge(l.status)}</td>
                                    <td>${l.result ? `<div class="command-output">${B33Utils.escapeHtml(l.result)}</div>` : '-'}</td>
                                    <td>${B33Utils.formatDate(l.completed_at)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${B33Utils.escapeHtml(err.message)}</div>`;
        }
    }
};
