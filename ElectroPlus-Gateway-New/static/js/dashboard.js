// Función para inicializar todos los gráficos
function initDashboardCharts(data) {
    // Gráfico de ventas por período
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: data.salesLabels,
            datasets: [{
                label: 'Ventas',
                data: data.salesData,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Gráfico de productos más vendidos
    const productsCtx = document.getElementById('topProductsChart').getContext('2d');
    new Chart(productsCtx, {
        type: 'bar',
        data: {
            labels: data.topProductsLabels,
            datasets: [{
                label: 'Unidades vendidas',
                data: data.topProductsData,
                backgroundColor: 'rgba(54, 162, 235, 0.5)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Gráfico de estado de reclamos
    const claimsCtx = document.getElementById('claimsChart').getContext('2d');
    new Chart(claimsCtx, {
        type: 'doughnut',
        data: {
            labels: data.claimsLabels,
            datasets: [{
                data: data.claimsData,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)'
                ]
            }]
        },
        options: {
            responsive: true
        }
    });

    // Gráfico de inventario bajo
    const inventoryCtx = document.getElementById('lowStockChart').getContext('2d');
    new Chart(inventoryCtx, {
        type: 'bar',
        data: {
            labels: data.lowStockLabels,
            datasets: [{
                label: 'Stock actual',
                data: data.lowStockData,
                backgroundColor: data.lowStockColors
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}