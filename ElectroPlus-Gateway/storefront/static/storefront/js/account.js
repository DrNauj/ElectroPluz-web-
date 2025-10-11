document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginAlert = document.getElementById('loginAlert');
    const loginToast = document.getElementById('loginToast');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');

    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Reset alert
            loginAlert.classList.add('d-none');
            
            const formData = new FormData(loginForm);
            try {
                const response = await fetch('/auth/api/login/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: formData.get('username'),
                        password: formData.get('password')
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Éxito
                    showToast('Éxito', 'Sesión iniciada correctamente', 'success');
                    // Cerrar modal
                    const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
                    loginModal.hide();
                    // Recargar página después de un breve delay
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    // Error
                    showAlert(data.message || 'Error al iniciar sesión', 'danger');
                }
            } catch (error) {
                showAlert('Error de conexión', 'danger');
                console.error('Error:', error);
            }
        });
    }

    // Función para mostrar alertas en el modal
    function showAlert(message, type) {
        loginAlert.textContent = message;
        loginAlert.className = `alert alert-${type}`;
        loginAlert.classList.remove('d-none');
    }

    // Función para mostrar notificaciones toast
    function showToast(title, message, type) {
        toastTitle.textContent = title;
        toastMessage.textContent = message;
        const toast = bootstrap.Toast.getOrCreateInstance(loginToast);
        loginToast.className = `toast bg-${type === 'success' ? 'success' : 'danger'} text-white`;
        toast.show();
    }
});