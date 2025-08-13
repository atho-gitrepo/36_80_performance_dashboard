// Chart instances for cleanup
let profitTrendsChart = null;
let runningPnlChart = null;
let dailyResultsChart = null;
let leaguePerformanceChart = null;
let typePerformanceChart = null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize date inputs
    const today = new Date().toISOString().split('T')[0];
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    const oneMonthAgoStr = oneMonthAgo.toISOString().split('T')[0];
    
    document.getElementById('start-date').value = oneMonthAgoStr;
    document.getElementById('end-date').value = today;
    
    fetchDashboardData();
});

async function fetchDashboardData() {
    try {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        const response = await fetch(`/api/dashboard_data?start_date=${startDate}&end_date=${endDate}`);
        const data = await response.json();
        
        updateKPIs(data.kpis);
        renderCharts(data);
        renderBetHistory(data.recent_bets);

    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // You might want to show an error message to the user here
    }
}

function resetDates() {
    const today = new Date().toISOString().split('T')[0];
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    const oneMonthAgoStr = oneMonthAgo.toISOString().split('T')[0];
    
    document.getElementById('start-date').value = oneMonthAgoStr;
    document.getElementById('end-date').value = today;
    
    fetchDashboardData();
}

function updateKPIs(kpis) {
    document.getElementById('total-bets').textContent = kpis.total_bets;
    document.getElementById('win-rate').textContent = `${kpis.win_rate}%`;
    
    const netProfitEl = document.getElementById('net-profit');
    netProfitEl.textContent = kpis.net_profit;
    netProfitEl.className = `card-text fs-2 ${kpis.net_profit >= 0 ? 'text-success' : 'text-danger'}`;
    
    const roiEl = document.getElementById('roi');
    roiEl.textContent = `${kpis.roi}%`;
    roiEl.className = `card-text fs-2 ${kpis.roi >= 0 ? 'text-success' : 'text-danger'}`;
}

function renderCharts(data) {
    // Destroy previous charts if they exist
    if (profitTrendsChart) profitTrendsChart.destroy();
    if (runningPnlChart) runningPnlChart.destroy();
    if (dailyResultsChart) dailyResultsChart.destroy();
    if (leaguePerformanceChart) leaguePerformanceChart.destroy();
    if (typePerformanceChart) typePerformanceChart.destroy();

    // Daily Results Chart
    const dailyResultsCtx = document.getElementById('dailyResultsChart').getContext('2d');
    dailyResultsChart = new Chart(dailyResultsCtx, {
        type: 'bar',
        data: {
            labels: data.daily_results.map(item => item.date),
            datasets: [
                {
                    label: 'Wins',
                    data: data.daily_results.map(item => item.wins),
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Losses',
                    data: data.daily_results.map(item => item.losses),
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Number of Bets'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterBody: function(context) {
                            const data = data.daily_results[context[0].dataIndex];
                            return `Net: ${data.net >= 0 ? '+' : ''}${data.net}`;
                        }
                    }
                }
            }
        }
    });

    // Running P&L Chart
    const runningPnlCtx = document.getElementById('runningPnlChart').getContext('2d');
    runningPnlChart = new Chart(runningPnlCtx, {
        type: 'line',
        data: {
            labels: data.running_pnl.map(d => d.date),
            datasets: [{
                label: 'Cumulative P&L',
                data: data.running_pnl.map(d => d.pnl),
                borderColor: 'rgba(0, 123, 255, 1)',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Profit/Loss'
                    }
                }
            }
        }
    });

    // League Performance Chart
    const leagueLabels = Object.keys(data.performance_by_league);
    const leaguePerformanceCtx = document.getElementById('leaguePerformanceChart').getContext('2d');
    leaguePerformanceChart = new Chart(leaguePerformanceCtx, {
        type: 'bar',
        data: {
            labels: leagueLabels,
            datasets: [
                {
                    label: 'Wins',
                    data: leagueLabels.map(league => data.performance_by_league[league].wins),
                    backgroundColor: 'rgba(40, 167, 69, 0.7)'
                },
                {
                    label: 'Losses',
                    data: leagueLabels.map(league => data.performance_by_league[league].losses),
                    backgroundColor: 'rgba(220, 53, 69, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });

    // Type Performance Chart
    const typeLabels = Object.keys(data.performance_by_type);
    const typePerformanceCtx = document.getElementById('typePerformanceChart').getContext('2d');
    typePerformanceChart = new Chart(typePerformanceCtx, {
        type: 'bar',
        data: {
            labels: typeLabels,
            datasets: [
                {
                    label: 'Wins',
                    data: typeLabels.map(type => data.performance_by_type[type].wins),
                    backgroundColor: 'rgba(40, 167, 69, 0.7)'
                },
                {
                    label: 'Losses',
                    data: typeLabels.map(type => data.performance_by_type[type].losses),
                    backgroundColor: 'rgba(220, 53, 69, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

function renderBetHistory(bets) {
    const tableBody = document.getElementById('bet-history-table').querySelector('tbody');
    tableBody.innerHTML = ''; // Clear existing rows
    
    bets.forEach(bet => {
        const row = tableBody.insertRow();
        const dateCell = row.insertCell(0);
        const matchCell = row.insertCell(1);
        const leagueCell = row.insertCell(2);
        const typeCell = row.insertCell(3);
        const outcomeCell = row.insertCell(4);
        
        dateCell.textContent = new Date(bet.placed_at).toLocaleString();
        matchCell.textContent = bet.match || 'N/A';
        leagueCell.textContent = bet.league || 'N/A';
        typeCell.textContent = bet.bet_type || 'N/A';
        
        outcomeCell.textContent = bet.outcome.toUpperCase();
        outcomeCell.className = bet.outcome === 'win' ? 'text-success fw-bold' : 'text-danger fw-bold';
    });
}

// Make functions available globally for HTML onclick handlers
window.fetchDashboardData = fetchDashboardData;
window.resetDates = resetDates;

