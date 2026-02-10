/* =====================================================
   🌾 Agri-Market Admin Dashboard JavaScript
   ===================================================== */

// Dashboard Configuration
const DashboardConfig = {
    refreshInterval: 30000, // 30 seconds
    mapCenter: [1.3733, 32.2903], // Uganda center
    mapZoom: 7
};

// Region coordinates for Uganda
const UgandaRegions = {
    'Central': { lat: 0.3476, lng: 32.5825, color: '#28a745' },
    'Eastern': { lat: 1.2513, lng: 33.7518, color: '#007bff' },
    'Northern': { lat: 2.7747, lng: 32.2989, color: '#ffc107' },
    'Western': { lat: 0.6180, lng: 30.2565, color: '#6f42c1' },
    'Kampala': { lat: 0.3163, lng: 32.5822, color: '#dc3545' }
};

// Chart instances
let charts = {};
let maps = {};

// Dashboard data (loaded from data attributes)
let dashboardData = {};

// Load dashboard data from HTML data attributes
function loadDashboardData() {
    const dataContainer = document.getElementById('dashboard-data');
    if (!dataContainer) return;
    
    const parseJSON = (attr) => {
        try {
            const value = dataContainer.getAttribute(attr);
            return value ? JSON.parse(value) : [];
        } catch (e) {
            console.warn('Failed to parse', attr, e);
            return [];
        }
    };
    
    dashboardData = {
        salesLabels: parseJSON('data-sales-labels'),
        salesData: parseJSON('data-sales-data'),
        ordersByStatus: parseJSON('data-orders-by-status'),
        categoryLabels: parseJSON('data-category-labels'),
        categoryData: parseJSON('data-category-data'),
        paymentLabels: parseJSON('data-payment-labels'),
        paymentData: parseJSON('data-payment-data'),
        orderLocations: parseJSON('data-order-locations'),
        regionOrderCounts: parseJSON('data-region-order-counts'),
        activeDeliveries: parseJSON('data-active-deliveries'),
        farmerLocations: parseJSON('data-farmer-locations'),
        deliveryZones: parseJSON('data-delivery-zones')
    };
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    initializeCharts();
    initializeMaps();
    setupAutoRefresh();
    setupEventListeners();
});

// Initialize all charts
function initializeCharts() {
    initSalesChart();
    initOrdersChart();
    initCategoryPieChart();
    initPaymentDonutChart();
}

// Sales Line Chart
function initSalesChart() {
    const ctx = document.getElementById('salesChart');
    if (!ctx) return;
    
    charts.sales = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: dashboardData.salesLabels || [],
            datasets: [{
                label: 'Revenue',
                data: dashboardData.salesData || [],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#28a745',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'UGX ' + context.raw.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'UGX ' + (value / 1000) + 'K';
                        }
                    }
                }
            }
        }
    });
}

// Orders Bar Chart
function initOrdersChart() {
    const ctx = document.getElementById('ordersChart');
    if (!ctx) return;
    
    const statusData = dashboardData.ordersByStatus || [];
    const labels = statusData.map(item => item.status.charAt(0).toUpperCase() + item.status.slice(1));
    const data = statusData.map(item => item.count);
    
    charts.orders = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled'],
            datasets: [{
                label: 'Orders',
                data: data.length ? data : [0, 0, 0, 0, 0],
                backgroundColor: [
                    '#ffc107',
                    '#17a2b8',
                    '#007bff',
                    '#28a745',
                    '#dc3545'
                ],
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Category Pie Chart
function initCategoryPieChart() {
    const ctx = document.getElementById('categoryPieChart');
    if (!ctx) return;
    
    charts.category = new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: dashboardData.categoryLabels || [],
            datasets: [{
                data: dashboardData.categoryData || [],
                backgroundColor: [
                    '#28a745', '#1e5631', '#d4a843', '#17a2b8', '#6f42c1',
                    '#fd7e14', '#e83e8c', '#20c997', '#007bff', '#dc3545', '#6c757d'
                ],
                borderWidth: 3,
                borderColor: '#fff',
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 15 }
                }
            }
        }
    });
}

// Payment Methods Donut Chart
function initPaymentDonutChart() {
    const ctx = document.getElementById('paymentDonutChart');
    if (!ctx) return;
    
    const paymentData = dashboardData.paymentMethods || [];
    const labels = paymentData.map(item => {
        const method = item.payment_method || 'Other';
        return method.replace('mobile_money_', '').toUpperCase();
    });
    const data = paymentData.map(item => item.count);
    
    charts.payment = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels.length ? labels : ['MTN', 'Airtel', 'PayPal', 'COD'],
            datasets: [{
                data: data.length ? data : [0, 0, 0, 0],
                backgroundColor: [
                    '#ffc107',  // MTN Yellow
                    '#dc3545',  // Airtel Red
                    '#003087',  // PayPal Blue
                    '#28a745'   // COD Green
                ],
                borderWidth: 0,
                cutout: '70%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20 }
                }
            }
        }
    });
}

// Initialize Maps
function initializeMaps() {
    initOrderDensityMap();
    initDeliveryTrackingMap();
    initFarmerLocationsMap();
}

// Order Density Heatmap
function initOrderDensityMap() {
    const mapContainer = document.getElementById('uganda-map');
    if (!mapContainer) return;
    
    maps.orderDensity = L.map('uganda-map').setView(DashboardConfig.mapCenter, DashboardConfig.mapZoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.orderDensity);
    
    // Add order locations as heat layer
    const orderLocations = dashboardData.orderLocations || [];
    if (orderLocations.length > 0) {
        const heatData = orderLocations.map(loc => [loc.lat, loc.lng, loc.count || 1]);
        L.heatLayer(heatData, {
            radius: 25,
            blur: 15,
            maxZoom: 10,
            gradient: {0.4: '#ffffb2', 0.65: '#fd8d3c', 1: '#bd0026'}
        }).addTo(maps.orderDensity);
    }
    
    // Add region markers
    Object.entries(UgandaRegions).forEach(([region, data]) => {
        const count = dashboardData.regionOrderCounts?.[region] || 0;
        L.circleMarker([data.lat, data.lng], {
            radius: Math.min(30, 10 + count / 5),
            fillColor: data.color,
            color: '#1e5631',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7
        }).addTo(maps.orderDensity).bindPopup(`
            <div class="map-popup">
                <strong>${region}</strong><br>
                <span>${count} orders</span>
            </div>
        `);
    });
}

// Live Delivery Tracking Map
function initDeliveryTrackingMap() {
    const mapContainer = document.getElementById('delivery-tracking-map');
    if (!mapContainer) return;
    
    maps.deliveryTracking = L.map('delivery-tracking-map').setView(DashboardConfig.mapCenter, DashboardConfig.mapZoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.deliveryTracking);
    
    // Add delivery markers
    const activeDeliveries = dashboardData.activeDeliveries || [];
    activeDeliveries.forEach(delivery => {
        if (delivery.lat && delivery.lng) {
            const icon = L.divIcon({
                className: 'delivery-marker-icon',
                html: `<div class="delivery-marker">🏍️</div>`,
                iconSize: [40, 40]
            });
            
            L.marker([delivery.lat, delivery.lng], { icon: icon })
                .addTo(maps.deliveryTracking)
                .bindPopup(`
                    <div class="delivery-popup">
                        <h4>Order #${delivery.order_id}</h4>
                        <p>Rider: ${delivery.rider_name}</p>
                        <p>Status: ${delivery.status}</p>
                        <p>ETA: ${delivery.eta || 'Calculating...'}</p>
                    </div>
                `);
        }
    });
}

// Farmer/Seller Locations Map
function initFarmerLocationsMap() {
    const mapContainer = document.getElementById('farmer-locations-map');
    if (!mapContainer) return;
    
    maps.farmerLocations = L.map('farmer-locations-map').setView(DashboardConfig.mapCenter, DashboardConfig.mapZoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.farmerLocations);
    
    // Add farmer markers
    const farmers = dashboardData.farmerLocations || [];
    farmers.forEach(farmer => {
        if (farmer.lat && farmer.lng) {
            const icon = L.divIcon({
                className: 'farmer-marker-icon',
                html: `<div class="farmer-marker">👨‍🌾</div>`,
                iconSize: [40, 40]
            });
            
            L.marker([farmer.lat, farmer.lng], { icon: icon })
                .addTo(maps.farmerLocations)
                .bindPopup(`
                    <div class="farmer-popup">
                        <h4>${farmer.business_name}</h4>
                        <p>${farmer.location}</p>
                        <p class="${farmer.is_verified ? 'verified' : ''}">
                            ${farmer.is_verified ? '✓ Verified Farmer' : 'Pending Verification'}
                        </p>
                        <p>Products: ${farmer.product_count}</p>
                        <p>Rating: ${'⭐'.repeat(farmer.rating || 0)}</p>
                    </div>
                `);
        }
    });
}

// Map Switcher
function switchMap(mapType) {
    const mapButtons = document.querySelectorAll('.map-control-btn');
    mapButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    const mapContainers = document.querySelectorAll('.map-container');
    mapContainers.forEach(container => {
        container.style.display = container.dataset.map === mapType ? 'block' : 'none';
    });
    
    // Invalidate size after showing
    setTimeout(() => {
        if (maps[mapType]) {
            maps[mapType].invalidateSize();
        }
    }, 100);
}

// Auto-refresh setup
function setupAutoRefresh() {
    setInterval(refreshDashboard, DashboardConfig.refreshInterval);
}

// Refresh dashboard data
function refreshDashboard() {
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.classList.add('loading');
    }
    
    fetch('/admin/api/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            updateStats(data);
            updateCharts(data);
            updateDeliveryTracking(data);
        })
        .catch(error => {
            console.log('Dashboard refresh error:', error);
        })
        .finally(() => {
            if (refreshBtn) {
                refreshBtn.classList.remove('loading');
            }
        });
}

// Update stats cards
function updateStats(data) {
    if (data.total_revenue) {
        const revenueEl = document.querySelector('[data-stat="revenue"]');
        if (revenueEl) {
            animateValue(revenueEl, parseInt(revenueEl.textContent.replace(/[^0-9]/g, '')), data.total_revenue);
        }
    }
    
    if (data.total_orders) {
        const ordersEl = document.querySelector('[data-stat="orders"]');
        if (ordersEl) {
            animateValue(ordersEl, parseInt(ordersEl.textContent), data.total_orders);
        }
    }
}

// Animate value changes
function animateValue(element, start, end, duration = 1000) {
    const range = end - start;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + range * progress);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Update charts with new data
function updateCharts(data) {
    if (charts.sales && data.sales_data) {
        charts.sales.data.labels = data.sales_labels;
        charts.sales.data.datasets[0].data = data.sales_data;
        charts.sales.update();
    }
    
    if (charts.orders && data.orders_by_status) {
        const statusData = data.orders_by_status;
        charts.orders.data.datasets[0].data = statusData.map(item => item.count);
        charts.orders.update();
    }
}

// Update delivery tracking
function updateDeliveryTracking(data) {
    if (data.active_deliveries && maps.deliveryTracking) {
        // Clear existing markers and add new ones
        maps.deliveryTracking.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                maps.deliveryTracking.removeLayer(layer);
            }
        });
        
        data.active_deliveries.forEach(delivery => {
            if (delivery.lat && delivery.lng) {
                const icon = L.divIcon({
                    className: 'delivery-marker-icon',
                    html: `<div class="delivery-marker">🏍️</div>`,
                    iconSize: [40, 40]
                });
                
                L.marker([delivery.lat, delivery.lng], { icon: icon })
                    .addTo(maps.deliveryTracking)
                    .bindPopup(`
                        <div class="delivery-popup">
                            <h4>Order #${delivery.order_id}</h4>
                            <p>Rider: ${delivery.rider_name}</p>
                            <p>Status: ${delivery.status}</p>
                        </div>
                    `);
            }
        });
    }
}

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }
    
    // Map control buttons
    document.querySelectorAll('.map-control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchMap(this.dataset.map);
        });
    });
}

// Export for global access
window.Dashboard = {
    refresh: refreshDashboard,
    switchMap: switchMap,
    charts: charts,
    maps: maps
};
