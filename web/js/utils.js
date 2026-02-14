const B33Utils = {
    parseJsonField(value) {
        if (!value) return [];
        try {
            const parsed = JSON.parse(value);
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            return [];
        }
    },

    formatDate(isoString) {
        if (!isoString) return '-';
        const d = new Date(isoString.replace(' ', 'T') + (isoString.includes('Z') ? '' : 'Z'));
        if (isNaN(d.getTime())) return isoString;
        return d.toLocaleString('en-GB', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
    },

    timeAgo(isoString) {
        if (!isoString) return '-';
        const d = new Date(isoString.replace(' ', 'T') + (isoString.includes('Z') ? '' : 'Z'));
        if (isNaN(d.getTime())) return isoString;
        const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
        if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
        return Math.floor(seconds / 86400) + 'd ago';
    },

    riskBadge(level) {
        const l = (level || 'none').toLowerCase();
        return `<span class="badge badge-${l}">${l.toUpperCase()}</span>`;
    },

    statusBadge(status) {
        const s = (status || 'unknown').toLowerCase();
        const cls = { active: 'badge-active', inactive: 'badge-inactive', removed: 'badge-removed',
                      pending: 'bg-warning text-dark', assigned: 'bg-info text-dark',
                      in_progress: 'bg-primary', completed: 'bg-success', failed: 'bg-danger',
                      sent: 'bg-info text-dark', received: 'bg-primary' };
        return `<span class="badge ${cls[s] || 'bg-secondary'}">${s}</span>`;
    },

    exportCSV(data, filename) {
        if (!data || data.length === 0) return;
        const headers = Object.keys(data[0]);
        const rows = data.map(row =>
            headers.map(h => {
                let val = row[h] == null ? '' : String(row[h]);
                if (val.includes(',') || val.includes('"') || val.includes('\n')) {
                    val = '"' + val.replace(/"/g, '""') + '"';
                }
                return val;
            }).join(',')
        );
        const csv = [headers.join(','), ...rows].join('\n');
        this._download(csv, filename + '.csv', 'text/csv');
    },

    exportJSON(data, filename) {
        this._download(JSON.stringify(data, null, 2), filename + '.json', 'application/json');
    },

    _download(content, filename, mime) {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const colors = { info: 'text-bg-primary', success: 'text-bg-success', error: 'text-bg-danger', warning: 'text-bg-warning' };
        const id = 'toast-' + Date.now();
        container.insertAdjacentHTML('beforeend', `
            <div id="${id}" class="toast ${colors[type] || colors.info}" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${this.escapeHtml(message)}</div>
                    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);
        const toastEl = document.getElementById(id);
        const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    },

    confirm(title, message) {
        return new Promise(resolve => {
            document.getElementById('confirm-modal-title').textContent = title;
            document.getElementById('confirm-modal-body').innerHTML = message;
            const modal = new bootstrap.Modal(document.getElementById('confirm-modal'));
            const okBtn = document.getElementById('confirm-modal-ok');
            const handler = () => { resolve(true); modal.hide(); okBtn.removeEventListener('click', handler); };
            okBtn.addEventListener('click', handler);
            document.getElementById('confirm-modal').addEventListener('hidden.bs.modal', () => {
                okBtn.removeEventListener('click', handler);
                resolve(false);
            }, { once: true });
            modal.show();
        });
    },

    truncate(str, maxLen = 50) {
        if (!str) return '-';
        return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
    },

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    deref(val, fallback = '-') {
        return val != null ? val : fallback;
    },

    loading() {
        return '<div class="loading-container"><div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    },

    emptyState(message = 'No data found') {
        return `<div class="empty-state"><h5>${this.escapeHtml(message)}</h5></div>`;
    }
};
