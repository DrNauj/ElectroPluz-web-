// Popup Flotante
function showFloatingPopup(message, type = 'info') {
    const popup = document.createElement('div');
    popup.className = `floating-popup ${type}`;
    popup.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="me-3">${message}</div>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    document.body.appendChild(popup);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => popup.remove(), 5000);
}

// Barra lateral desplegable
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar-drawer');
    sidebar.classList.toggle('active');
}

// Isla flotante
function showFloatingIsland(content, duration = 5000) {
    const island = document.createElement('div');
    island.className = 'floating-island';
    island.innerHTML = content;
    document.body.appendChild(island);
    
    if (duration) {
        setTimeout(() => island.remove(), duration);
    }
}

// Sistema de notificaciones Toast
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast show bg-${type}`;
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
}

// Ejemplo de uso para el carrito
function updateCart(productId) {
    // Simular agregar al carrito
    showToast('Producto agregado al carrito', 'success');
    showFloatingIsland('<i class="fas fa-cart-plus"></i> ¡Producto agregado!');
}

// Observador de scroll para mostrar/ocultar elementos
const scrollObserver = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    },
    { threshold: 0.1 }
);

// Aplicar animaciones al scroll
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        scrollObserver.observe(el);
    });
});