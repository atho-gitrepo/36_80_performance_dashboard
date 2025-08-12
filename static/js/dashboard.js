document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
});

async function fetchDashboardData() {
    try {
        // You can add date filters here later
        const response = await fetch('/api/dashboard_data');
        const data = await response.json();
        
        updateKPIs(data.kpis);
        renderCharts(data);
        renderBetHistory(data.recent_bets);

    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

function updateKPIs(kpis) {
    document.getElementById('total-bets').textContent = kpis.total_bets;
    document.getElementById('win-rate').textContent = `${kpis.win_rate}%`;
    document.getElementById('net-profit').textContent = kpis.net_profit;
    document.getElementById('roi').textContent = `${kpis.roi}%`;
}

function renderCharts(data) {
    // Profit Trends Chart
    const profitTrendsCtx = document.getElementById('profitTrendsChart').getContext('2d');
    new Chart(profitTrendsCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.profit_trends),
            datasets: [{
                label: 'Daily Profit/Loss',
                data: Object.values(data.profit_trends),
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        }
    });

    // Running P&L Chart
    const runningPnlCtx = document.getElementById('runningPnlChart').getContext('2d');
    new Chart(runningPnlCtx, {
        type: 'line',
        data: {
            labels: data.running_pnl.map(d => d.date),
            datasets: [{
                label: 'Cumulative P&L',
                data: data.running_pnl.map(d => d.pnl),
                fill: false,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        }
    });
}

function renderBetHistory(bets) {
    const tableBody = document.getElementById('bet-history-table').querySelector('tbody');
    tableBody.innerHTML = ''; // Clear existing rows
    
    bets.forEach(bet => {
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = new Date(bet.placed_at).toLocaleDateString();
        row.insertCell(1).textContent = bet.match_name;
        row.insertCell(2).textContent = bet.league;
        row.insertCell(3).textContent = bet.bet_type;
        row.insertCell(4).textContent = bet.outcome;
    });
}

