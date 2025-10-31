// Función para manejar los formularios de autenticación
function handleAuthForm(formId, action) {
    const form = document.getElementById(formId);
    const alertDiv = form.querySelector('.alert-danger');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        try {
            const response = await fetch(action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                // Cerrar el modal correspondiente
                const modalId = formId === 'loginForm' ? '#loginModal' : '#registerModal';
                const modal = bootstrap.Modal.getInstance(document.querySelector(modalId));
                if (modal) {
                    modal.hide();
                }

                // Mostrar mensaje de éxito usando Bootstrap toast
                const toast = new bootstrap.Toast(document.createElement('div'));
                toast._element.classList.add('toast', 'position-fixed', 'top-0', 'end-0', 'm-3');
                toast._element.innerHTML = `
                    <div class="toast-header bg-success text-white">
                        <strong class="me-auto">¡Éxito!</strong>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">${data.message}</div>
                `;
                document.body.appendChild(toast._element);
                toast.show();

                // Recargar la página después de un breve delay para actualizar la navbar
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // Mostrar errores
                alertDiv.style.display = 'block';
                if (data.errors) {
                    alertDiv.textContent = Object.values(data.errors).flat().join('\n');
                } else {
                    alertDiv.textContent = data.message || 'Ha ocurrido un error. Por favor, intenta nuevamente.';
                }
            }
        } catch (error) {
            alertDiv.style.display = 'block';
            alertDiv.textContent = 'Error de conexión. Por favor, verifica tu conexión a internet.';
        }
    });
}

// Inicializar los manejadores cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        handleAuthForm('loginForm', loginForm.action);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        handleAuthForm('registerForm', registerForm.action);
    }
});