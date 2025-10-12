// cart.js - Manejo del carrito de compras
function addToCart(productId, form = null) {
    const quantity = form ? form.querySelector('input[name="quantity"]').value : 1;
    const csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar contador del carrito
            updateCartCount();
            
            // Mostrar notificación de éxito
            const toast = new bootstrap.Toast(document.getElementById('cartToast'));
            document.querySelector('#cartToast .toast-body').textContent = data.message;
            toast.show();
        } else {
            throw new Error(data.error || 'Error al añadir al carrito');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const toast = new bootstrap.Toast(document.getElementById('errorToast'));
        document.querySelector('#errorToast .toast-body').textContent = error.message;
        toast.show();
    });
}

function updateCartQuantity(productId, newQuantity) {
    const csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    if (newQuantity <= 0) {
        removeFromCart(productId);
        return;
    }

    fetch('/api/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: newQuantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar total y subtotales
            updateCartTotals();
            
            // Actualizar contador del carrito
            updateCartCount();
            
            // Mostrar notificación
            const toast = new bootstrap.Toast(document.getElementById('cartToast'));
            document.querySelector('#cartToast .toast-body').textContent = 'Carrito actualizado';
            toast.show();
        } else {
            throw new Error(data.error || 'Error al actualizar el carrito');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const toast = new bootstrap.Toast(document.getElementById('errorToast'));
        document.querySelector('#errorToast .toast-body').textContent = error.message;
        toast.show();
    });
}

function removeFromCart(productId) {
    const csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    fetch('/api/cart/remove/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Eliminar la fila del producto
            const productRow = document.getElementById(`cart-item-${productId}`);
            if (productRow) {
                productRow.remove();
            }
            
            // Actualizar totales y contador
            updateCartTotals();
            updateCartCount();
            
            // Mostrar notificación
            const toast = new bootstrap.Toast(document.getElementById('cartToast'));
            document.querySelector('#cartToast .toast-body').textContent = 'Producto eliminado del carrito';
            toast.show();
            
            // Si el carrito está vacío, recargar la página
            if (data.is_empty) {
                location.reload();
            }
        } else {
            throw new Error(data.error || 'Error al eliminar del carrito');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const toast = new bootstrap.Toast(document.getElementById('errorToast'));
        document.querySelector('#errorToast .toast-body').textContent = error.message;
        toast.show();
    });
}

function updateCartCount() {
    fetch('/api/cart/count/')
        .then(response => response.json())
        .then(data => {
            const cartBadge = document.querySelector('#cartBadge');
            if (cartBadge) {
                cartBadge.textContent = data.count;
                cartBadge.style.display = data.count > 0 ? 'block' : 'none';
            }
        })
        .catch(error => console.error('Error:', error));
}

function updateCartTotals() {
    fetch('/api/cart/total/')
        .then(response => response.json())
        .then(data => {
            // Actualizar subtotal
            const subtotalElement = document.getElementById('cartSubtotal');
            if (subtotalElement) {
                subtotalElement.textContent = `$${data.subtotal}`;
            }

            // Actualizar total con envío
            const totalElement = document.getElementById('cartTotal');
            if (totalElement) {
                totalElement.textContent = `$${data.total}`;
            }

            // Actualizar costo de envío si existe
            const shippingElement = document.getElementById('cartShipping');
            if (shippingElement && data.shipping_cost) {
                shippingElement.textContent = `$${data.shipping_cost}`;
            }

            // Actualizar descuento si existe
            const discountElement = document.getElementById('cartDiscount');
            if (discountElement && data.discount) {
                discountElement.textContent = `-$${data.discount}`;
            }
        })
        .catch(error => console.error('Error:', error));
}

// Inicializar tooltips de Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar conteo del carrito
    updateCartCount();
});