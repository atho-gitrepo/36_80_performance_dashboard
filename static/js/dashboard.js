document.addEventListener('DOMContentLoaded', () => {
    // Initial data fetch on page load
    fetchDashboardData();

    // Event listener for the filter button
    document.getElementById('filterButton').addEventListener('click', fetchDashboardData);
});

async function fetchDashboardData() {
    const start_date = document.getElementById('startDate').value;
    const end_date = document.getElementById('endDate').value;
    // Correctly get the values from the input fields by their IDs
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
        createOutcomeByScoreChart(data.outcome_by_initial_score);
        createPerformanceByDayChart(data.performance_by_day_of_week);
        createPerformanceByCountryChart(data.performance_by_country);
        createPerformanceByBetTypeChart(data.performance_by_bet_type);

    } catch (error) {
        console.error("Error fetching dashboard data:", error);
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
        row.innerHTML = `
            <td>${bet.match_name}</td>
            <td>${bet.league}</td>
            <td>${bet.country}</td>
            <td>${bet.bet_type}</td>
            <td class="${outcomeClass}">${bet.outcome}</td>
            <td>${bet.placed_at ? new Date(bet.placed_at).toLocaleString() : 'N/A'}</td>
        `;
        tableBody.appendChild(row);
    });
}

// --- New Chart Functions ---
let scoreChartInstance = null;
let dayChartInstance = null;
let countryChartInstance = null;
let betTypeChartInstance = null;

// Creates a chart showing wins/losses grouped by initial score
function createOutcomeByScoreChart(data) {
    const ctx = document.getElementById('outcomeByScoreChart');
    if (!ctx) return;
    
    if (scoreChartInstance) {
        scoreChartInstance.destroy();
    }

    const labels = Object.keys(data);
    const winData = labels.map(label => data[label].wins);
    const lossData = labels.map(label => data[label].losses);

    scoreChartInstance = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Wins',
                    data: winData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
                {
                    label: 'Losses',
                    data: lossData,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
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
                        text: 'Number of Bets'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Bet Outcomes by Initial Score'
                }
            }
        }
    });
}

// Creates a chart showing performance by day of the week
function createPerformanceByDayChart(data) {
    const ctx = document.getElementById('performanceByDayChart');
    if (!ctx) return;

    if (dayChartInstance) {
        dayChartInstance.destroy();
    }
    
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const labels = daysOrder.filter(day => data[day]);
    const winData = labels.map(day => data[day].wins);
    const lossData = labels.map(day => data[day].losses);

    dayChartInstance = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Wins',
                    data: winData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Losses',
                    data: lossData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
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
                        text: 'Number of Bets'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Performance by Day of the Week'
                }
            }
        }
    });
}

// --- New Chart: Performance by Country ---
function createPerformanceByCountryChart(data) {
    const ctx = document.getElementById('performanceByCountryChart');
    if (!ctx) return;

    if (countryChartInstance) {
        countryChartInstance.destroy();
    }

    const labels = Object.keys(data);
    const winData = labels.map(label => data[label].wins);
    const lossData = labels.map(label => data[label].losses);

    countryChartInstance = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Wins',
                    data: winData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
                {
                    label: 'Losses',
                    data: lossData,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
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
                        text: 'Number of Bets'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Performance by Country'
                }
            }
        }
    });
}

// --- New Chart: Performance by Bet Type ---
function createPerformanceByBetTypeChart(data) {
    const ctx = document.getElementById('performanceByBetTypeChart');
    if (!ctx) return;

    if (betTypeChartInstance) {
        betTypeChartInstance.destroy();
    }

    const labels = Object.keys(data);
    const winData = labels.map(label => data[label].wins);
    const lossData = labels.map(label => data[label].losses);

    betTypeChartInstance = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Wins',
                    data: winData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                },
                {
                    label: 'Losses',
                    data: lossData,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
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
                        text: 'Number of Bets'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Performance by Bet Type'
                }
            }
        }
    });
}
