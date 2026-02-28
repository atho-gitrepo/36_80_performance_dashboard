document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
    document.getElementById('filterButton').addEventListener('click', () => {
        showLoadingSpinner();
        fetchDashboardData();
    });
});

let chartInstances = {};
function destroyChart(name) { if (chartInstances[name]) chartInstances[name].destroy(); }

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
    const league = document.getElementById('leagueDropdown').value;

    const queryParams = new URLSearchParams({ start_date, end_date, league });

    try {
        const response = await fetch(`/api/dashboard_data?${queryParams.toString()}`);
        const data = await response.json();
        
        updateKPIs(data.kpis);
        updateDropdown(data.filter_options, league);
        updateRecentBetsTable(data.recent_bets);
        
        // Render Charts
        createDailyProfitTrendChart(data.daily_profit_trend);
        createOutcomeByScoreChart(data.performance_by_initial_score);
        createPerformanceByDayChart(data.performance_by_day_of_week);
        createPerformanceByCountryChart(data.performance_by_country);
        createDailySummaryChart(data.daily_summary); // Replaced Bet Type
        
    } catch (error) { console.error("Error:", error); } 
    finally { hideLoadingSpinner(); }
}

function updateKPIs(kpis) {
    document.getElementById('total-bets').textContent = kpis.total_bets;
    document.getElementById('win-rate').textContent = `${kpis.win_rate}%`;
    document.getElementById('net-profit').textContent = kpis.net_profit;
    if (document.getElementById('roi')) document.getElementById('roi').textContent = `${kpis.roi}%`;
}

function updateDropdown(options, current) {
    const select = document.getElementById('leagueDropdown');
    select.innerHTML = '<option value="All">All Leagues</option>';
    options.forEach(opt => {
        const el = document.createElement('option');
        el.value = opt;
        el.textContent = opt;
        if (opt === current) el.selected = true;
        select.appendChild(el);
    });
}

function updateRecentBetsTable(bets) {
    const tableBody = document.getElementById('recentBetsTableBody');
    tableBody.innerHTML = '';
    bets.forEach(bet => {
        const row = document.createElement('tr');
        const outcomeClass = bet.outcome === 'win' ? 'text-green-600 font-bold' : 'text-red-600 font-bold';
        row.innerHTML = `
            <td class="px-6 py-4">${bet.match_name}</td>
            <td class="px-6 py-4">${bet.league}</td>
            <td class="px-6 py-4">${bet.country}</td>
            <td class="px-6 py-4 ${outcomeClass}">${bet.outcome.toUpperCase()}</td>
            <td class="px-6 py-4">${bet.placed_at}</td>
        `;
        tableBody.appendChild(row);
    });
}

// --- Chart Functions ---

function createDailySummaryChart(data) {
    const ctx = document.getElementById('dailySummaryChart');
    if (!ctx) return;
    destroyChart('dailySummaryChart');
    chartInstances['dailySummaryChart'] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                { label: 'Wins', data: data.wins, backgroundColor: '#10B981' },
                { label: 'Losses', data: data.losses, backgroundColor: '#EF4444' }
            ]
        },
        options: { 
            responsive: true, maintainAspectRatio: false, 
            scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } }
        }
    });
}

function createDailyProfitTrendChart(data) {
    const ctx = document.getElementById('dailyProfitTrendChart');
    if (!ctx) return;
    destroyChart('dailyProfitTrendChart');
    chartInstances['dailyProfitTrendChart'] = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{ label: 'Net Profit', data: data.map(d => d.profit), borderColor: '#3B82F6', tension: 0.4, fill: true, backgroundColor: 'rgba(59, 130, 246, 0.1)' }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function createOutcomeByScoreChart(data) {
    const ctx = document.getElementById('outcomeByScoreChart');
    if (!ctx) return;
    destroyChart('outcomeByScoreChart');
    chartInstances['outcomeByScoreChart'] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{ label: 'Win Rate %', data: Object.values(data), backgroundColor: 'rgba(75, 192, 192, 0.6)' }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function createPerformanceByDayChart(data) {
    const ctx = document.getElementById('performanceByDayChart');
    if (!ctx) return;
    destroyChart('performanceByDayChart');
    chartInstances['performanceByDayChart'] = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: Object.keys(data),
            datasets: [{ label: 'Win Rate %', data: Object.values(data), borderColor: '#10B981', tension: 0.4 }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function createPerformanceByCountryChart(data) {
    const ctx = document.getElementById('performanceByCountryChart');
    if (!ctx) return;
    destroyChart('performanceByCountryChart');
    chartInstances['performanceByCountryChart'] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{ label: 'Win Rate %', data: Object.values(data), backgroundColor: '#6366F1' }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}
