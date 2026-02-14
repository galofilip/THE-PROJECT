const LoginPage = {
    init() {
        const form = document.getElementById('login-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value;
            const errorEl = document.getElementById('login-error');
            const btn = document.getElementById('login-btn');

            errorEl.classList.add('d-none');
            btn.disabled = true;
            btn.textContent = 'Logging in...';

            try {
                await B33Api.login(username, password);
                App.onLoginSuccess();
            } catch (err) {
                errorEl.textContent = err.message;
                errorEl.classList.remove('d-none');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Login';
            }
        });

        // Server URL toggle
        document.getElementById('toggle-server-url').addEventListener('click', (e) => {
            e.preventDefault();
            const config = document.getElementById('server-url-config');
            config.classList.toggle('d-none');
            if (!config.classList.contains('d-none')) {
                document.getElementById('login-server-url').value = B33Api.getServerUrl();
            }
        });

        document.getElementById('save-server-url').addEventListener('click', () => {
            const url = document.getElementById('login-server-url').value.trim();
            if (url) {
                B33Api.setServerUrl(url);
                B33Utils.showToast('Server URL saved', 'success');
            }
        });
    }
};
