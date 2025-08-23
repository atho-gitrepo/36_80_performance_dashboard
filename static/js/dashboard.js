document.addEventListener('DOMContentLoaded', () => {
    // Initial data fetch on page load
    fetchDashboardData();

    // Event listener for the filter button
    document.getElementById('filterButton').addEventListener('click', () => {
        showLoadingSpinner();
        fetchDashboardData();
    });
});

function showLoadingSpinner() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';
}

function hideLoadingSpinner() {
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'block';
}

async function fetchDashboardData() {
    const start_date = document.getElementById('startDate').value;
    const end_date = document.getElementById('endDate').value;
    const matchName = document.getElementById('matchName') ? document.getElementById('matchName').value : '';
    const league = document.getElementById('leagueName') ? document.getElementById('leagueName').value : '';

    const queryParams = new URLSearchParams();
    if (start_date) queryParams.append('start_date', start_date);
    if (end_date) queryParams.append('end_date', end_date);
    if (matchName) queryParams.append('match_name', matchName);
    if (league) queryParams.append('league', league);

    try {
        const response = await fetch(`/api/dashboard_data?${queryParams.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        console.log("Fetched data:", data); // For debugging
        
        updateKPIs(data.kpis);
        updateRecentBetsTable(data.recent_bets);
        
        // Update charts with new data structures
        createOutcomeByScoreChart(data.performance_by_initial_score);
        createPerformanceByDayChart(data.performance_by_day_of_week);
        createPerformanceByCountryChart(data.performance_by_country);
        createPerformanceByBetTypeChart(data.performance_by_bet_type);
        createDailyProfitTrendChart(data.daily_profit_trend); // New chart
        
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
    } finally {
        hideLoadingSpinner();
    }
}

function updateKPIs(kpis) {
    document.getElementById('total-bets').textContent = kpis.total_bets;
    document.getElementById('win-rate').textContent = `${kpis.win_rate}%`;
    document.getElementById('net-profit').textContent = kpis.net_profit;
    const roiElement = document.getElementById('roi');
    if (roiElement) {
      roiElement.textContent = `${kpis.roi}%`;
    }
}

function updateRecentBetsTable(bets) {
    const tableBody = document.getElementById('recentBetsTableBody');
    if (!tableBody) {
        console.error("Error: recentBetsTableBody element not found.");
        return;
    }
    
    tableBody.innerHTML = ''; // Clear existing rows

    bets.forEach(bet => {
        const row = document.createElement('tr');
        const outcomeClass = bet.outcome === 'win' ? 'win-text' : 'loss-text';
        
        // Use a more robust date parsing and formatting
        const placedAtDate = bet.placed_at ? new Date(bet.placed_at) : null;
        const placedAtDisplay = placedAtDate ? placedAtDate.toLocaleDateString() : 'N/A';
        
        row.innerHTML = `
            <td>${bet.match_name}</td>
            <td>${bet.league}</td>
            <td>${bet.country}</td>
            <td>${bet.bet_type}</td>
            <td class="${outcomeClass}">${bet.outcome}</td>
            <td>${placedAtDisplay}</td>
        `;
        tableBody.appendChild(row);
    });
}

// --- Chart Functions with Enhancements ---
let chartInstances = {};

function destroyChart(chartName) {
    if (chartInstances[chartName]) {
        chartInstances[chartName].destroy();
        chartInstances[chartName] = null;
    }
}

function createOutcomeByScoreChart(data) {
    const ctx = document.getElementById('outcomeByScoreChart');
    if (!ctx) return;
    
    destroyChart('outcomeByScoreChart');

    const labels = Object.keys(data);
    const chartData = labels.map(label => data[label]);

    chartInstances['outcomeByScoreChart'] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Win Rate (%)',
                    data: chartData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Win Rate (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Win Rate by Initial Score'
                }
            }
        }
    });
}

function createPerformanceByDayChart(data) {
    const ctx = document.getElementById('performanceByDayChart');
    if (!ctx) return;

    destroyChart('performanceByDayChart');
    
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const labels = daysOrder.filter(day => data[day] !== undefined);
    const chartData = labels.map(day => data[day]);

    chartInstances['performanceByDayChart'] = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Win Rate (%)',
                    data: chartData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4,
                    fill: true
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Win Rate (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Win Rate by Day of the Week'
                }
            }
        }
    });
}

function createPerformanceByCountryChart(data) {
    const ctx = document.getElementById('performanceByCountryChart');
    if (!ctx) return;

    destroyChart('performanceByCountryChart');

    const labels = Object.keys(data);
    const chartData = labels.map(label => data[label]);

    chartInstances['performanceByCountryChart'] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Win Rate (%)',
                    data: chartData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Win Rate (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Win Rate by Country'
                }
            }
        }
    });
}

function createPerformanceByBetTypeChart(data) {
    const ctx = document.getElementById('performanceByBetTypeChart');
    if (!ctx) return;

    destroyChart('performanceByBetTypeChart');

    const labels = Object.keys(data);
    const chartData = labels.map(label => data[label]);

    chartInstances['performanceByBetTypeChart'] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Win Rate (%)',
                    data: chartData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Win Rate (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Win Rate by Bet Type'
                }
            }
        }
    });
}

// --- New Chart: Cumulative Profit Trend ---
function createDailyProfitTrendChart(data) {
    const ctx = document.getElementById('dailyProfitTrendChart');
    if (!ctx) return;
    
    destroyChart('dailyProfitTrendChart');

    const labels = data.map(item => item.date);
    const profitData = data.map(item => item.profit);

    chartInstances['dailyProfitTrendChart'] = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Cumulative Net Profit',
                    data: profitData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Net Profit (Units)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Cumulative Profit Trend Over Time'
                }
            }
        }
    });
}
