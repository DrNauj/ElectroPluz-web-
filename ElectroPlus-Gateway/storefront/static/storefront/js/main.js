// Funciones de utilidad para la interfaz
document.addEventListener('DOMContentLoaded', function() {
    // Activar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Activar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Marcar el ítem activo en el menú
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Función para formatear números como moneda
    window.formatCurrency = function(number) {
        return new Intl.NumberFormat('es-PE', {
            style: 'currency',
            currency: 'PEN'
        }).format(number);
    }

    // Función para formatear fechas
    window.formatDate = function(dateString) {
        return new Date(dateString).toLocaleDateString('es-PE', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
});

// Función para confirmar acciones destructivas
function confirmarAccion(mensaje = '¿Está seguro de realizar esta acción?') {
    return confirm(mensaje);
}

// Función para actualizar el carrito de compras
function actualizarCarrito(productId, cantidad) {
    fetch('/api/carrito/actualizar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            producto_id: productId,
            cantidad: cantidad
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Actualizar el contador del carrito
            document.getElementById('cart-count').textContent = data.total_items;
            // Actualizar el total
            document.getElementById('cart-total').textContent = formatCurrency(data.total);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al actualizar el carrito');
    });
}

// Función para buscar productos
function buscarProductos(query) {
    fetch(`/api/productos/buscar/?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
        const resultadosDiv = document.getElementById('resultados-busqueda');
        resultadosDiv.innerHTML = '';
        
        data.productos.forEach(producto => {
            resultadosDiv.innerHTML += `
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">${producto.nombre}</h5>
                            <p class="card-text">${producto.descripcion}</p>
                            <p class="card-text">
                                <strong>Precio:</strong> ${formatCurrency(producto.precio)}
                                <br>
                                <strong>Stock:</strong> ${producto.stock}
                            </p>
                            <button onclick="agregarAlCarrito(${producto.id})" 
                                    class="btn btn-primary"
                                    ${producto.stock < 1 ? 'disabled' : ''}>
                                Agregar al carrito
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al buscar productos');
    });
}