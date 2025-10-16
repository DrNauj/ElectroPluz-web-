// CSRF cookie helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Funciones para el carrito
function updateQuantity(productId, quantity) {
    fetch(`/tienda/carrito/agregar/${productId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar contador del carrito
            document.getElementById('cart-badge').textContent = data.cart_total;
            // Mostrar mensaje de éxito
            alert(data.message);
        }
    });
}

// Funciones para la lista de deseos
function toggleWishlist(productId, button) {
    fetch(`/tienda/wishlist/toggle/${productId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar el ícono del botón
            const icon = button.querySelector('i');
            if (data.in_wishlist) {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
            } else {
                icon.classList.remove('bi-heart-fill');
                icon.classList.add('bi-heart');
            }
        }
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Botones de cantidad en el carrito
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.dataset.productId;
            updateQuantity(productId, this.value);
        });
    });

    // Botones de la lista de deseos
    const wishlistButtons = document.querySelectorAll('.toggle-wishlist');
    wishlistButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            toggleWishlist(productId, this);
        });
    });
});