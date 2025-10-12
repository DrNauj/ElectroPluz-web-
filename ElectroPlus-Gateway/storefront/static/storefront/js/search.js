// search.js - Manejo de búsqueda y sugerencias
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('input[name="search"]');
    const suggestionsContainer = document.getElementById('searchSuggestions');
    let debounceTimer;

    // Función para crear el HTML de una sugerencia
    function createSuggestionHTML(product) {
        return `
            <li>
                <a class="dropdown-item d-flex align-items-center py-2" href="${product.url}">
                    <div class="flex-shrink-0" style="width: 40px; height: 40px;">
                        ${product.imagen ? 
                          `<img src="${product.imagen}" class="img-fluid" alt="${product.nombre}" style="width: 100%; height: 100%; object-fit: cover;">` :
                          `<div class="bg-light d-flex align-items-center justify-content-center" style="width: 100%; height: 100%;">
                               <i class="fas fa-box text-secondary"></i>
                           </div>`
                        }
                    </div>
                    <div class="ms-3 flex-grow-1">
                        <div class="text-truncate">${product.nombre}</div>
                        <small class="text-muted">$${product.precio}</small>
                    </div>
                </a>
            </li>
        `;
    }

    // Función para obtener y mostrar sugerencias
    function getSuggestions() {
        const query = searchInput.value.trim();
        
        if (query.length < 2) {
            suggestionsContainer.innerHTML = '';
            return;
        }

        fetch(`/api/search/suggestions/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.suggestions.length > 0) {
                    const html = data.suggestions.map(createSuggestionHTML).join('') +
                        `<li><hr class="dropdown-divider mb-0"></li>
                         <li>
                             <a class="dropdown-item text-primary" href="/productos/?search=${encodeURIComponent(query)}">
                                 <i class="fas fa-search me-2"></i>Ver todos los resultados
                             </a>
                         </li>`;
                    suggestionsContainer.innerHTML = html;
                } else {
                    suggestionsContainer.innerHTML = `
                        <li>
                            <span class="dropdown-item text-muted">
                                <i class="fas fa-info-circle me-2"></i>No se encontraron productos
                            </span>
                        </li>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                suggestionsContainer.innerHTML = `
                    <li>
                        <span class="dropdown-item text-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>Error al buscar productos
                        </span>
                    </li>`;
            });
    }

    // Event listeners para el input de búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(getSuggestions, 300);
        });

        // Cerrar sugerencias cuando se hace click fuera
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.innerHTML = '';
            }
        });

        // Evitar que el formulario se envíe al presionar enter si hay una sugerencia seleccionada
        searchInput.closest('form').addEventListener('submit', function(e) {
            const selectedSuggestion = suggestionsContainer.querySelector('.dropdown-item:hover');
            if (selectedSuggestion) {
                e.preventDefault();
                selectedSuggestion.click();
            }
        });
    }
});