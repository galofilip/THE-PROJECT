const DashboardPage = {
    _charts: {},

    async render() {
        const el = document.getElementById('page-dashboard');
        el.innerHTML = B33Utils.loading();

        try {
            const [privateRes, publicRes, infectedRes, tasksRes, exploitRes] = await Promise.all([
                B33Api.getPrivateScans(),
                B33Api.getPublicScans(),
                B33Api.getInfected(),
                B33Api.getTasks(),
                B33Api.getExploitLogs()
            ]);

            const privateScans = privateRes.data || [];
            const publicScans = publicRes.data || [];
            const infected = infectedRes.data || [];
            const tasks = tasksRes.data || [];
            const exploitLogs = exploitRes.data || [];

            const allScans = [...privateScans, ...publicScans];
            const totalScans = allScans.length;
            const totalVulns = allScans.reduce((acc, s) => acc + B33Utils.parseJsonField(s.vulnerabilities_found).length, 0);
            const activeBackdoors = infected.filter(p => (p.status || '').toLowerCase() === 'active').length;
            const pendingTasks = tasks.filter(t => t.status === 'pending').length;

            // Risk distribution
            const riskCounts = { none: 0, low: 0, medium: 0, high: 0, critical: 0 };
            allScans.forEach(s => { const r = (s.risk_level || 'none').toLowerCase(); if (riskCounts[r] !== undefined) riskCounts[r]++; });

            // Task status distribution
            const taskCounts = { pending: 0, assigned: 0, in_progress: 0, completed: 0, failed: 0 };
            tasks.forEach(t => { if (taskCounts[t.status] !== undefined) taskCounts[t.status]++; });

            // Recent activity
            const recent = [];
            privateScans.slice(0, 5).forEach(s => recent.push({ time: s.created_at, type: 'Scan', target: s.target_ip, status: s.risk_level || 'none', detail: 'Private' }));
            publicScans.slice(0, 5).forEach(s => recent.push({ time: s.created_at, type: 'Scan', target: s.target_ip, status: s.risk_level || 'none', detail: 'Public' }));
            tasks.slice(0, 5).forEach(t => recent.push({ time: t.created_at, type: 'Task', target: B33Utils.deref(t.target_ip, '-'), status: t.status, detail: t.task_type }));
            exploitLogs.slice(0, 5).forEach(l => recent.push({ time: l.created_at, type: 'Exploit', target: l.target_ip, status: l.success ? 'completed' : 'failed', detail: B33Utils.deref(l.vulnerability_id, '-') }));
            recent.sort((a, b) => (b.time || '').localeCompare(a.time || ''));

            el.innerHTML = `
                <div class="section-header"><h2>Dashboard</h2></div>
                <div class="row g-3 mb-4">
                    <div class="col-6 col-md-3"><div class="stat-card stat-scans"><div class="stat-value">${totalScans}</div><div class="stat-label">Total Scans</div></div></div>
                    <div class="col-6 col-md-3"><div class="stat-card stat-vulns"><div class="stat-value">${totalVulns}</div><div class="stat-label">Vulns Found</div></div></div>
                    <div class="col-6 col-md-3"><div class="stat-card stat-active"><div class="stat-value">${activeBackdoors}</div><div class="stat-label">Active Backdoors</div></div></div>
                    <div class="col-6 col-md-3"><div class="stat-card stat-tasks"><div class="stat-value">${pendingTasks}</div><div class="stat-label">Pending Tasks</div></div></div>
                </div>
                <div class="row g-3 mb-4">
                    <div class="col-12 col-md-6">
                        <div class="b33-card p-3"><h6 class="text-muted">Risk Distribution</h6><div class="chart-container"><canvas id="chart-risk"></canvas></div></div>
                    </div>
                    <div class="col-12 col-md-6">
                        <div class="b33-card p-3"><h6 class="text-muted">Task Status</h6><div class="chart-container"><canvas id="chart-tasks"></canvas></div></div>
                    </div>
                </div>
                <div class="b33-card p-3">
                    <h6 class="text-muted mb-3">Recent Activity</h6>
                    ${recent.length === 0 ? B33Utils.emptyState('No recent activity') : `
                    <div class="table-responsive">
                        <table class="table b33-table table-sm mb-0">
                            <thead><tr><th>Time</th><th>Type</th><th>Target</th><th>Status</th><th>Detail</th></tr></thead>
                            <tbody>
                                ${recent.slice(0, 10).map(r => `
                                    <tr>
                                        <td>${B33Utils.timeAgo(r.time)}</td>
                                        <td><span class="badge bg-secondary">${B33Utils.escapeHtml(r.type)}</span></td>
                                        <td class="mono">${B33Utils.escapeHtml(r.target)}</td>
                                        <td>${B33Utils.statusBadge(r.status)}</td>
                                        <td>${B33Utils.escapeHtml(r.detail)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>`}
                </div>
            `;

            this._renderCharts(riskCounts, taskCounts);
        } catch (err) {
            el.innerHTML = `<div class="alert alert-danger">Failed to load dashboard: ${B33Utils.escapeHtml(err.message)}</div>`;
        }
    },

    _renderCharts(riskCounts, taskCounts) {
        // Destroy old charts
        Object.values(this._charts).forEach(c => c.destroy());
        this._charts = {};

        const riskCanvas = document.getElementById('chart-risk');
        if (riskCanvas) {
            this._charts.risk = new Chart(riskCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['None', 'Low', 'Medium', 'High', 'Critical'],
                    datasets: [{
                        data: [riskCounts.none, riskCounts.low, riskCounts.medium, riskCounts.high, riskCounts.critical],
                        backgroundColor: ['#8b949e', '#58a6ff', '#d29922', '#db6d28', '#f85149']
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { color: '#e6edf3' } } }
                }
            });
        }

        const taskCanvas = document.getElementById('chart-tasks');
        if (taskCanvas) {
            this._charts.tasks = new Chart(taskCanvas, {
                type: 'bar',
                data: {
                    labels: ['Pending', 'Assigned', 'In Progress', 'Completed', 'Failed'],
                    datasets: [{
                        data: [taskCounts.pending, taskCounts.assigned, taskCounts.in_progress, taskCounts.completed, taskCounts.failed],
                        backgroundColor: ['#d29922', '#58a6ff', '#1f6feb', '#3fb950', '#f85149']
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#8b949e', stepSize: 1 }, grid: { color: '#30363d' } },
                        x: { ticks: { color: '#8b949e' }, grid: { display: false } }
                    }
                }
            });
        }
    },

    cleanup() {
        Object.values(this._charts).forEach(c => c.destroy());
        this._charts = {};
    }
};
