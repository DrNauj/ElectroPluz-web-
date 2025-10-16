// auth-modal.js
class AuthManager {
    constructor() {
        this.loginModal = document.getElementById('loginModal');
        this.loginForm = document.getElementById('loginForm');
        this.loginAlert = document.getElementById('loginAlert');
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    setupEventListeners() {
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Manejar cierre de sesión
        document.querySelectorAll('[data-action="logout"]').forEach(button => {
            button.addEventListener('click', (e) => this.handleLogout(e));
        });
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(this.loginForm);
        const username = formData.get('username');
        const password = formData.get('password');

        try {
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Si es empleado, mostrar modal de selección de vista
                if (data.user && data.user.rol === 'empleado') {
                    this.showAlert('success', `Bienvenido ${data.user.username}! ¿A qué vista desea acceder?`);
                    // Crear botones de selección
                    const buttonContainer = document.createElement('div');
                    buttonContainer.className = 'd-grid gap-2 mt-3';
                    
                    const clienteBtn = document.createElement('button');
                    clienteBtn.className = 'btn btn-outline-primary';
                    clienteBtn.textContent = 'Vista de Cliente';
                    clienteBtn.onclick = () => window.location.href = '/';
                    
                    const empleadoBtn = document.createElement('button');
                    empleadoBtn.className = 'btn btn-primary';
                    empleadoBtn.textContent = 'Vista de Empleado';
                    empleadoBtn.onclick = () => window.location.href = '/admin/dashboard/';
                    
                    buttonContainer.appendChild(clienteBtn);
                    buttonContainer.appendChild(empleadoBtn);
                    
                    const alertDiv = document.getElementById('loginAlert');
                    alertDiv.appendChild(buttonContainer);
                } else {
                    // Para otros usuarios, mostrar mensaje personalizado y redireccionar
                    const welcomeMessage = data.user ? 
                        `¡Bienvenido ${data.user.username}!` : 
                        'Inicio de sesión exitoso';
                    this.showAlert('success', welcomeMessage);
                    setTimeout(() => {
                        window.location.href = data.redirect_url || '/';
                    }, 1500);
                }
            } else {
                this.showAlert('danger', data.error || 'Error de autenticación');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('danger', 'Error al conectar con el servidor');
        }
    }

    async handleLogout(e) {
        e.preventDefault();

        try {
            const response = await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (response.ok) {
                window.location.href = data.redirect_url || '/';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status/');
            const data = await response.json();

            if (data.is_authenticated) {
                this.updateUI(data.user);
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
        }
    }

    updateUI(user) {
        // Actualizar elementos de UI según el rol del usuario
        const authElements = document.querySelectorAll('[data-auth-required]');
        const roleElements = document.querySelectorAll('[data-role-required]');

        authElements.forEach(el => {
            el.style.display = 'block';
        });

        roleElements.forEach(el => {
            const requiredRole = el.dataset.roleRequired;
            if (user.rol === requiredRole) {
                el.style.display = 'block';
            }
        });

        // Actualizar nombre de usuario si existe el elemento
        const userNameElement = document.getElementById('currentUserName');
        if (userNameElement && user.username) {
            userNameElement.textContent = user.username;
        }
    }

    showAlert(type, message) {
        if (this.loginAlert) {
            this.loginAlert.className = `alert alert-${type}`;
            this.loginAlert.textContent = message;
            this.loginAlert.classList.remove('d-none');
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});