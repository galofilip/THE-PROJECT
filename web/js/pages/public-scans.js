const PublicScansPage = {
    _data: [],

    async render() {
        const el = document.getElementById('page-public-scans');
        el.innerHTML = `
            <div class="section-header">
                <h2>Public IP Scans</h2>
                <button class="btn btn-sm btn-outline-secondary" id="pub-refresh">Refresh</button>
            </div>
            <div class="filter-bar">
                <div class="row g-2 align-items-end">
                    <div class="col-auto">
                        <label class="form-label small text-muted">Risk Level</label>
                        <select class="form-select form-select-sm" id="pub-filter-risk">
                            <option value="">All</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                            <option value="none">None</option>
                        </select>
                    </div>
                    <div class="col-auto">
                        <label class="form-label small text-muted">Country</label>
                        <input type="text" class="form-control form-control-sm" id="pub-filter-country" placeholder="e.g. IL">
                    </div>
                    <div class="col-auto">
                        <label class="form-label small text-muted">Batch ID</label>
                        <input type="text" class="form-control form-control-sm" id="pub-filter-batch" placeholder="Batch ID">
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-sm btn-outline-primary" id="pub-apply-filters">Filter</button>
                        <button class="btn btn-sm btn-outline-secondary" id="pub-clear-filters">Clear</button>
                    </div>
                    <div class="col-auto ms-auto">
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">Export</button>
                            <ul class="dropdown-menu dropdown-menu-dark">
                                <li><a class="dropdown-item" href="#" id="pub-export-csv">CSV</a></li>
                                <li><a class="dropdown-item" href="#" id="pub-export-json">JSON</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div id="pub-table-container">${B33Utils.loading()}</div>
        `;
        this._attachHandlers();
        await this.loadData();
    },

    _attachHandlers() {
        document.getElementById('pub-apply-filters').addEventListener('click', () => this.loadData(this._getFilters()));
        document.getElementById('pub-clear-filters').addEventListener('click', () => {
            document.getElementById('pub-filter-risk').value = '';
            document.getElementById('pub-filter-country').value = '';
            document.getElementById('pub-filter-batch').value = '';
            this.loadData();
        });
        document.getElementById('pub-refresh').addEventListener('click', () => this.loadData(this._getFilters()));
        document.getElementById('pub-export-csv').addEventListener('click', (e) => { e.preventDefault(); B33Utils.exportCSV(this._data, 'public_scans_' + new Date().toISOString().slice(0, 10)); });
        document.getElementById('pub-export-json').addEventListener('click', (e) => { e.preventDefault(); B33Utils.exportJSON(this._data, 'public_scans_' + new Date().toISOString().slice(0, 10)); });
    },

    _getFilters() {
        return {
            risk_level: document.getElementById('pub-filter-risk').value,
            country_code: document.getElementById('pub-filter-country').value.trim(),
            scan_batch_id: document.getElementById('pub-filter-batch').value.trim()
        };
    },

    async loadData(filters = {}) {
        const container = document.getElementById('pub-table-container');
        container.innerHTML = B33Utils.loading();
        try {
            const res = await B33Api.getPublicScans(filters);
            this._data = res.data || [];
            this._renderTable();
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${B33Utils.escapeHtml(err.message)}</div>`;
        }
    },

    _renderTable() {
        const container = document.getElementById('pub-table-container');
        if (this._data.length === 0) { container.innerHTML = B33Utils.emptyState('No scans found'); return; }

        container.innerHTML = `
            <div class="table-responsive">
                <table class="table b33-table table-sm">
                    <thead><tr><th>IP Address</th><th>Country</th><th>City</th><th>Ports</th><th>Services</th><th>Vulns</th><th>Risk</th><th>Date</th><th>Actions</th></tr></thead>
                    <tbody>${this._data.map((s, i) => this._renderRow(s, i)).join('')}</tbody>
                </table>
            </div>
        `;
        container.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const idx = parseInt(btn.dataset.idx);
                const scan = this._data[idx];
                if (btn.dataset.action === 'expand') this._toggleDetail(idx);
                else if (btn.dataset.action === 'exploit') this._handleExploit(scan);
                else if (btn.dataset.action === 'delete') this._handleDelete(scan);
            });
        });
    },

    _renderRow(scan, idx) {
        const ports = B33Utils.parseJsonField(scan.open_ports);
        const services = B33Utils.parseJsonField(scan.detected_services);
        const vulns = B33Utils.parseJsonField(scan.vulnerabilities_found);
        const hasVulns = vulns.length > 0;
        const country = B33Utils.deref(scan.country_code);

        return `
            <tr style="cursor:pointer" data-action="expand" data-idx="${idx}">
                <td class="mono">${B33Utils.escapeHtml(scan.target_ip)}</td>
                <td>${B33Utils.escapeHtml(country)}</td>
                <td>${B33Utils.escapeHtml(B33Utils.deref(scan.city))}</td>
                <td class="mono">${ports.length > 0 ? B33Utils.escapeHtml(ports.join(', ')) : '-'}</td>
                <td><span class="badge bg-secondary">${services.length}</span></td>
                <td><span class="badge ${hasVulns ? 'badge-' + (scan.risk_level || 'none').toLowerCase() : 'bg-secondary'}">${vulns.length}</span></td>
                <td>${B33Utils.riskBadge(scan.risk_level)}</td>
                <td>${B33Utils.timeAgo(scan.created_at)}</td>
                <td>
                    ${hasVulns ? `<button class="btn btn-exploit btn-sm me-1" data-action="exploit" data-idx="${idx}">Exploit</button>` : ''}
                    <button class="btn btn-outline-danger btn-sm" data-action="delete" data-idx="${idx}">Del</button>
                </td>
            </tr>
            <tr class="detail-row d-none" id="pub-detail-${idx}">
                <td colspan="9">
                    <div class="p-2">
                        <div class="row">
                            <div class="col-md-4"><h6 class="text-muted">Services</h6><pre>${B33Utils.escapeHtml(JSON.stringify(services, null, 2))}</pre></div>
                            <div class="col-md-4"><h6 class="text-muted">Vulnerabilities</h6><pre>${B33Utils.escapeHtml(JSON.stringify(vulns, null, 2))}</pre></div>
                            <div class="col-md-4">
                                <h6 class="text-muted">Details</h6>
                                <p class="small"><strong>Scan ID:</strong> <span class="mono">${B33Utils.escapeHtml(scan.scan_id)}</span></p>
                                <p class="small"><strong>Batch:</strong> ${B33Utils.escapeHtml(B33Utils.deref(scan.scan_batch_id))}</p>
                                <p class="small"><strong>Date:</strong> ${B33Utils.formatDate(scan.created_at)}</p>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    },

    _toggleDetail(idx) { const row = document.getElementById('pub-detail-' + idx); if (row) row.classList.toggle('d-none'); },

    async _handleExploit(scan) {
        const vulns = B33Utils.parseJsonField(scan.vulnerabilities_found);
        if (vulns.length === 0) return;
        const vuln = vulns[0];
        const confirmed = await B33Utils.confirm('Exploit & Deploy',
            `<p>Target: <strong class="mono">${B33Utils.escapeHtml(scan.target_ip)}</strong></p>
             <p>Vulnerability: <strong>${B33Utils.escapeHtml(vuln.cve || 'Unknown')}</strong></p>
             <p>This will create an exploitation task.</p>`);
        if (!confirmed) return;
        try {
            await B33Api.createTask({ task_type: 'exploit', target_ip: scan.target_ip, vulnerability_id: vuln.cve || null, payload: JSON.stringify({ deploy_backdoor: true }), assigned_to: 'pico' });
            B33Utils.showToast('Exploitation task queued', 'success');
        } catch (err) { B33Utils.showToast('Failed: ' + err.message, 'error'); }
    },

    async _handleDelete(scan) {
        const confirmed = await B33Utils.confirm('Delete Scan', `Delete scan for <strong class="mono">${B33Utils.escapeHtml(scan.target_ip)}</strong>?`);
        if (!confirmed) return;
        try {
            await B33Api.deletePublicScan(scan.scan_id);
            B33Utils.showToast('Scan deleted', 'success');
            this.loadData(this._getFilters());
        } catch (err) { B33Utils.showToast('Failed: ' + err.message, 'error'); }
    }
};
