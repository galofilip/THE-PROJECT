const App = {
    _currentPage: null,

    _pages: {
        'dashboard': DashboardPage,
        'private-scans': PrivateScansPage,
        'public-scans': PublicScansPage,
        'infected': InfectedPage,
        'logs': LogsPage,
        'settings': SettingsPage
    },

    init() {
        LoginPage.init();

        if (B33Api.isAuthenticated()) {
            this._showApp();
            this.navigate('dashboard');
        } else {
            this.showLogin();
        }

        // Nav link handlers
        document.querySelectorAll('[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigate(link.dataset.page);
            });
        });

        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
    },

    navigate(page) {
        // Cleanup previous page
        if (this._currentPage && this._pages[this._currentPage] && this._pages[this._currentPage].cleanup) {
            this._pages[this._currentPage].cleanup();
        }

        // Hide all sections
        document.querySelectorAll('main > section').forEach(s => s.classList.add('d-none'));

        // Show target section
        const section = document.getElementById('page-' + page);
        if (section) section.classList.remove('d-none');

        // Update nav active state
        document.querySelectorAll('[data-page]').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Render page
        this._currentPage = page;
        const pageModule = this._pages[page];
        if (pageModule && pageModule.render) {
            pageModule.render();
        }

        // Close mobile nav
        const navCollapse = document.getElementById('navbarNav');
        if (navCollapse.classList.contains('show')) {
            bootstrap.Collapse.getInstance(navCollapse)?.hide();
        }
    },

    onLoginSuccess() {
        this._showApp();
        this.navigate('dashboard');
    },

    showLogin() {
        document.getElementById('login-page').style.display = '';
        document.getElementById('app').classList.add('d-none');
        document.getElementById('login-username').value = '';
        document.getElementById('login-password').value = '';
        document.getElementById('login-error').classList.add('d-none');
    },

    _showApp() {
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('app').classList.remove('d-none');
    },

    logout() {
        if (this._currentPage && this._pages[this._currentPage] && this._pages[this._currentPage].cleanup) {
            this._pages[this._currentPage].cleanup();
        }
        B33Api.logout();
        this.showLogin();
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
