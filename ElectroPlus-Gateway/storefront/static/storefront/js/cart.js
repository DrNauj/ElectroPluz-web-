// cart.js - Manejo del carrito de compras
// Constantes para URLs de la API
const API_URLS = {
    ADD_TO_CART: '/api/cart/add/',
    UPDATE_CART: '/api/cart/update/',
    REMOVE_FROM_CART: '/api/cart/remove/',
    GET_CART_COUNT: '/api/cart/count/',
    GET_CART_TOTAL: '/api/cart/total/'
};

document.addEventListener('DOMContentLoaded', function() {
    // Agregar listeners a todos los botones de agregar al carrito
    document.addEventListener('click', function(e) {
        const button = e.target.closest('.add-to-cart-btn');
        if (button) {
            e.preventDefault();
            const form = button.closest('.cart-add-form');
            if (form) {
                const productId = form.dataset.productId;
                console.log('Adding to cart:', productId); // Debug
                addToCart(productId, form);
            }
        }
    });

    // Inicializar tooltips y contador
    initializeCart();
});

function initializeCart() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar conteo del carrito
    updateCartCount();
}

function updateCartCount() {
    fetch(API_URLS.GET_CART_COUNT)
        .then(response => response.json())
        .then(data => {
            console.log('Cart count response:', data); // Debug log
            
            // Actualizar todos los posibles contadores del carrito
            ['#cart-counter', '#cartBadge', '#cartCounter'].forEach(selector => {
                const counter = document.querySelector(selector);
                if (counter) {
                    counter.textContent = data.count || '0';
                    // Manejar visibilidad
                    if (counter.classList.contains('d-none')) {
                        counter.classList.toggle('d-none', !data.count);
                    } else if (counter.style.display) {
                        counter.style.display = data.count ? 'block' : 'none';
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error updating cart count:', error);
            // En caso de error, asumimos carrito vacío
            const counter = document.querySelector('#cart-counter');
            if (counter) {
                counter.textContent = '0';
                counter.classList.add('d-none');
            }
        });
}

function addToCart(productId, form = null) {
    const quantity = form ? form.querySelector('input[name="quantity"]').value : 1;
    const csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    console.log('Sending cart request:', {
        productId,
        quantity,
        url: API_URLS.ADD_TO_CART
    });

    fetch(API_URLS.ADD_TO_CART, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: parseInt(quantity)
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