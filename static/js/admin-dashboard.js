/**
 * Agri-Market Admin Dashboard - Charts & Map
 */

document.addEventListener('DOMContentLoaded', function() {
    const dataContainer = document.getElementById('dashboard-data');
    if (!dataContainer) return;

    const data = {
        salesLabels: JSON.parse(dataContainer.dataset.salesLabels || '[]'),
        salesData: JSON.parse(dataContainer.dataset.salesData || '[]'),
        categoryLabels: JSON.parse(dataContainer.dataset.categoryLabels || '[]'),
        categoryData: JSON.parse(dataContainer.dataset.categoryData || '[]'),
        pendingOrders: parseInt(dataContainer.dataset.pendingOrders || '0'),
        processingOrders: parseInt(dataContainer.dataset.processingOrders || '0'),
        deliveredOrders: parseInt(dataContainer.dataset.deliveredOrders || '0')
    };

    // Chart.js Defaults
    Chart.defaults.font.family = "'Poppins', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#4a5d4a';

    // Agricultural Color Palette
    const colors = {
        green: '#2E7D32',
        greenLight: '#4CAF50',
        gold: '#FFB300',
        orange: '#FF8F00',
        blue: '#1976D2',
        purple: '#6A1B9A',
        red: '#C62828'
    };

    // Sales Line Chart
    const salesCtx = document.getElementById('salesChart');
    if (salesCtx) {
        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: data.salesLabels,
                datasets: [{
                    label: 'Sales (UGX)',
                    data: data.salesData,
                    borderColor: colors.green,
                    backgroundColor: 'rgba(46, 125, 50, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: colors.green,
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: colors.green,
                        padding: 12,
                        titleFont: { weight: '600' },
                        callbacks: {
                            label: function(ctx) {
                                return 'UGX ' + ctx.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxTicksLimit: 8 }
                    },
                    y: {
                        grid: { color: 'rgba(46, 125, 50, 0.08)' },
                        ticks: {
                            callback: function(value) {
                                if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
                                if (value >= 1000) return (value / 1000).toFixed(0) + 'K';
                                return value;
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    // Category Doughnut Chart
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx) {
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: data.categoryLabels.length ? data.categoryLabels : ['No Data'],
                datasets: [{
                    data: data.categoryData.length ? data.categoryData : [1],
                    backgroundColor: [
                        colors.green,
                        colors.gold,
                        colors.blue,
                        colors.orange,
                        colors.purple,
                        colors.greenLight
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 12,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    }
                }
            }
        });
    }

    // Orders Status Pie Chart (Pizza Style)
    const ordersCtx = document.getElementById('ordersChart');
    if (ordersCtx) {
        const totalOrders = data.pendingOrders + data.processingOrders + data.deliveredOrders;
        new Chart(ordersCtx, {
            type: 'pie',
            data: {
                labels: ['Pending', 'Processing', 'Delivered'],
                datasets: [{
                    data: totalOrders > 0 ? [data.pendingOrders, data.processingOrders, data.deliveredOrders] : [1, 0, 0],
                    backgroundColor: [colors.gold, colors.blue, colors.green],
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    hoverOffset: 15,
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 12,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        titleFont: { weight: '600' }
                    }
                }
            }
        });
    }

    // Revenue Bar Chart
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
        const revenueData = data.salesData.slice(0, 6).map(v => v || Math.random() * 500000);
        
        new Chart(revenueCtx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Revenue',
                    data: revenueData,
                    backgroundColor: [
                        'rgba(46, 125, 50, 0.8)',
                        'rgba(76, 175, 80, 0.8)',
                        'rgba(255, 179, 0, 0.8)',
                        'rgba(25, 118, 210, 0.8)',
                        'rgba(255, 143, 0, 0.8)',
                        'rgba(106, 27, 154, 0.8)'
                    ],
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        grid: { color: 'rgba(46, 125, 50, 0.08)' },
                        ticks: {
                            callback: function(value) {
                                if (value >= 1000) return (value / 1000).toFixed(0) + 'K';
                                return value;
                            }
                        }
                    }
                }
            }
        });
    }

    // Uganda Map
    const mapContainer = document.getElementById('uganda-map');
    if (mapContainer && typeof L !== 'undefined') {
        const map = L.map('uganda-map').setView([1.3733, 32.2903], 7);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        // Uganda regions with markers
        const regions = [
            { name: 'Kampala', coords: [0.3476, 32.5825], orders: 45, color: colors.green },
            { name: 'Entebbe', coords: [0.0512, 32.4637], orders: 23, color: colors.greenLight },
            { name: 'Jinja', coords: [0.4244, 33.2041], orders: 18, color: colors.gold },
            { name: 'Mbarara', coords: [-0.6072, 30.6545], orders: 15, color: colors.orange },
            { name: 'Gulu', coords: [2.7747, 32.2990], orders: 12, color: colors.blue },
            { name: 'Mbale', coords: [1.0750, 34.1755], orders: 10, color: colors.purple },
            { name: 'Fort Portal', coords: [0.6710, 30.2750], orders: 8, color: colors.green },
            { name: 'Lira', coords: [2.2499, 32.8998], orders: 7, color: colors.greenLight }
        ];

        regions.forEach(region => {
            const marker = L.circleMarker(region.coords, {
                radius: Math.max(8, region.orders / 3),
                fillColor: region.color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);

            marker.bindPopup(`
                <div class="map-popup">
                    <h4>📍 ${region.name}</h4>
                    <p><strong>${region.orders}</strong> orders</p>
                    <p>Active customers in this region</p>
                </div>
            `);
        });

        // Add Uganda boundary highlight
        const ugandaBounds = [
            [-1.5, 29.5],
            [4.2, 35.0]
        ];
        
        L.rectangle(ugandaBounds, {
            color: colors.green,
            weight: 2,
            fill: false,
            dashArray: '5, 10'
        }).addTo(map);

        // Invalidate size after render
        setTimeout(() => map.invalidateSize(), 100);
    }
});
