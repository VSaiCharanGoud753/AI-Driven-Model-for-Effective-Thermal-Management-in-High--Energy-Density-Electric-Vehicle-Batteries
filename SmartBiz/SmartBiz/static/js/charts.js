/* ==========================================================================
   SmartBiz AI - Chart.js 11-Chart Visualizations & Theme Manager
   ========================================================================== */

let activeCharts = {};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('monthlyRevenueChart')) {
        fetchChartData('all');
        initDateFilterListener();
    }
});

function initDateFilterListener() {
    const filterSelect = document.getElementById('dashboardDateFilter');
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            fetchChartData(e.target.value);
            showToast(`Filtering charts by: ${e.target.options[e.target.selectedIndex].text}`, 'info');
        });
    }
}

function fetchChartData(filterRange = 'all') {
    fetch(`/api/charts/data?filter=${filterRange}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                renderAllCharts(data);
            }
        })
        .catch(err => console.error("Error fetching chart data:", err));
}

function renderAllCharts(data) {
    const isDark = document.body.classList.contains('dark-mode');
    const textColor = isDark ? '#cbd5e1' : '#475569';
    const gridColor = isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.8)';

    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = textColor;
    Chart.defaults.scale.grid.color = gridColor;

    // Destroy previous chart instances to prevent canvas reuse leaks
    Object.keys(activeCharts).forEach(key => {
        if (activeCharts[key]) activeCharts[key].destroy();
    });

    // 1. Monthly Revenue & Profit Trend (Line Chart with Gradient Fill)
    const ctxRev = document.getElementById('monthlyRevenueChart')?.getContext('2d');
    if (ctxRev) {
        const gradRev = ctxRev.createLinearGradient(0, 0, 0, 300);
        gradRev.addColorStop(0, 'rgba(79, 70, 229, 0.4)');
        gradRev.addColorStop(1, 'rgba(79, 70, 229, 0.0)');
        
        const gradProf = ctxRev.createLinearGradient(0, 0, 0, 300);
        gradProf.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
        gradProf.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        activeCharts['monthlyRevenue'] = new Chart(ctxRev, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [
                    {
                        label: 'Total Revenue ($)',
                        data: data.monthly_revenue,
                        borderColor: '#4f46e5',
                        backgroundColor: gradRev,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 7
                    },
                    {
                        label: 'Net Profit ($)',
                        data: data.profit_trend,
                        borderColor: '#10b981',
                        backgroundColor: gradProf,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 7
                    }
                ]
            },
            options: getStandardOptions('Revenue & Profit Trends ($)')
        });
    }

    // 2. Category Sales Distribution (Doughnut Chart)
    const ctxCat = document.getElementById('categorySalesChart')?.getContext('2d');
    if (ctxCat) {
        activeCharts['categorySales'] = new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: data.category_sales.labels,
                datasets: [{
                    data: data.category_sales.data,
                    backgroundColor: ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'],
                    borderWidth: 2,
                    borderColor: isDark ? '#131b2e' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 15, usePointStyle: true } }
                },
                cutout: '68%'
            }
        });
    }

    // 3. Top Products Leaderboard (Horizontal Bar Chart)
    const ctxTop = document.getElementById('topProductsChart')?.getContext('2d');
    if (ctxTop) {
        activeCharts['topProducts'] = new Chart(ctxTop, {
            type: 'bar',
            data: {
                labels: data.top_products.labels,
                datasets: [{
                    label: 'Revenue Generated ($)',
                    data: data.top_products.data,
                    backgroundColor: '#7c3aed',
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { grid: { color: gridColor } }, y: { grid: { display: false } } }
            }
        });
    }

    // 4. Inventory Status Breakdown (Pie Chart)
    const ctxInv = document.getElementById('inventoryStatusChart')?.getContext('2d');
    if (ctxInv) {
        activeCharts['inventoryStatus'] = new Chart(ctxInv, {
            type: 'pie',
            data: {
                labels: data.inventory_status.labels,
                datasets: [{
                    data: data.inventory_status.data,
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 2,
                    borderColor: isDark ? '#131b2e' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { usePointStyle: true } } }
            }
        });
    }

    // 5. Region-wise Sales (Polar Area Chart)
    const ctxReg = document.getElementById('regionSalesChart')?.getContext('2d');
    if (ctxReg) {
        activeCharts['regionSales'] = new Chart(ctxReg, {
            type: 'polarArea',
            data: {
                labels: data.region_sales.labels,
                datasets: [{
                    data: data.region_sales.data,
                    backgroundColor: ['rgba(79, 70, 229, 0.7)', 'rgba(6, 182, 212, 0.7)', 'rgba(16, 185, 129, 0.7)', 'rgba(245, 158, 11, 0.7)', 'rgba(236, 72, 153, 0.7)', 'rgba(139, 92, 246, 0.7)']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right', labels: { usePointStyle: true } } }
            }
        });
    }

    // 6. Expense Analysis by Category (Doughnut Chart)
    const ctxExp = document.getElementById('expenseAnalysisChart')?.getContext('2d');
    if (ctxExp) {
        activeCharts['expenseAnalysis'] = new Chart(ctxExp, {
            type: 'doughnut',
            data: {
                labels: data.expense_analysis.labels,
                datasets: [{
                    data: data.expense_analysis.data,
                    backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#10b981', '#64748b'],
                    borderWidth: 2,
                    borderColor: isDark ? '#131b2e' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { usePointStyle: true } } },
                cutout: '60%'
            }
        });
    }

    // 7. Revenue vs Expenses Comparison (Grouped Bar Chart)
    const ctxRevExp = document.getElementById('revenueVsExpensesChart')?.getContext('2d');
    if (ctxRevExp) {
        activeCharts['revVsExp'] = new Chart(ctxRevExp, {
            type: 'bar',
            data: {
                labels: data.months,
                datasets: [
                    {
                        label: 'Monthly Revenue ($)',
                        data: data.revenue_vs_expenses.revenue,
                        backgroundColor: '#4f46e5',
                        borderRadius: 6
                    },
                    {
                        label: 'Operating Expenses ($)',
                        data: data.revenue_vs_expenses.expenses,
                        backgroundColor: '#ef4444',
                        borderRadius: 6
                    }
                ]
            },
            options: getStandardOptions('Revenue vs Expenses ($)')
        });
    }

    // 8. Profit Margin Analytics (% Line Chart)
    const ctxMargin = document.getElementById('profitMarginChart')?.getContext('2d');
    if (ctxMargin) {
        activeCharts['profitMargin'] = new Chart(ctxMargin, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Net Profit Margin (%)',
                    data: data.profit_margin,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.15)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        ticks: { callback: val => val + '%' },
                        grid: { color: gridColor }
                    },
                    x: { grid: { color: gridColor } }
                }
            }
        });
    }

    // 9. Customer Growth Trend (Bar Chart)
    const ctxCust = document.getElementById('customerGrowthChart')?.getContext('2d');
    if (ctxCust) {
        activeCharts['customerGrowth'] = new Chart(ctxCust, {
            type: 'bar',
            data: {
                labels: data.customer_growth.labels,
                datasets: [{
                    label: 'Customers by Segment',
                    data: data.customer_growth.data,
                    backgroundColor: ['#4f46e5', '#3b82f6', '#10b981', '#f59e0b'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { grid: { display: false } }, y: { grid: { color: gridColor } } }
            }
        });
    }
}

function getStandardOptions(yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'top', labels: { usePointStyle: true, padding: 20 } },
            tooltip: {
                padding: 12,
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleFont: { size: 13, weight: 'bold' },
                bodyFont: { size: 13 },
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: $${context.raw.toLocaleString()}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return '$' + value.toLocaleString();
                    }
                }
            }
        }
    };
}

function updateChartsTheme(isDark) {
    const textColor = isDark ? '#cbd5e1' : '#475569';
    const gridColor = isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.8)';
    
    Chart.defaults.color = textColor;
    Chart.defaults.scale.grid.color = gridColor;
    
    Object.values(activeCharts).forEach(chart => {
        if (chart && chart.options && chart.options.scales) {
            if (chart.options.scales.x) chart.options.scales.x.grid.color = gridColor;
            if (chart.options.scales.y) chart.options.scales.y.grid.color = gridColor;
            chart.update();
        }
    });
}
