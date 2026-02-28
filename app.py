from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import firestore, credentials, initialize_app
import os
import json
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# --- Firebase Initialization ---
try:
    FIREBASE_CREDENTIALS_JSON_STRING = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not FIREBASE_CREDENTIALS_JSON_STRING:
        raise ValueError("FIREBASE_CREDENTIALS_JSON environment variable is not set.")
    
    cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON_STRING)
    cred = credentials.Certificate(cred_dict)

    if not firebase_admin._apps:
        initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"❌ Firebase Error: {e}")

def calculate_kpis(bets):
    total = len(bets)
    if total == 0:
        return {"total_bets": 0, "win_rate": 0, "net_profit": 0, "roi": 0}
    
    wins = [b for b in bets if b.get('outcome') == 'win']
    win_count = len(wins)
    loss_count = total - win_count
    
    win_rate = (win_count / total) * 100
    net_profit = win_count - loss_count # Assuming 1 unit stake
    roi = (net_profit / total) * 100
    
    return {
        "total_bets": total,
        "win_rate": round(win_rate, 2),
        "net_profit": net_profit,
        "roi": round(roi, 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard_data')
def get_dashboard_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    league_filter = request.args.get('league')

    # Fetch data sorted chronologically for the Trend Chart
    query = db.collection('resolved_bets').order_by('placed_at', direction=firestore.Query.ASCENDING)
    
    if start_date:
        query = query.where('placed_at', '>=', start_date)
    if end_date:
        query = query.where('placed_at', '<=', end_date)
    
    docs = query.stream()
    all_bets_raw = [doc.to_dict() for doc in docs]

    available_filters = set()
    filtered_bets = []
    
    # Data Structures for Charts
    daily_summary = defaultdict(lambda: {"wins": 0, "losses": 0})
    perf_score = defaultdict(lambda: {"wins": 0, "losses": 0})
    perf_day = defaultdict(lambda: {"wins": 0, "losses": 0})
    perf_country = defaultdict(lambda: {"wins": 0, "losses": 0})
    profit_trend = []
    cumulative_profit = 0

    week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for bet in all_bets_raw:
        country = bet.get('country', 'Unknown')
        league = bet.get('league', 'Unknown')
        display_name = f"{country} - {league}"
        available_filters.add(display_name)

        # Apply Dropdown Filter
        if league_filter and league_filter != "All" and display_name != league_filter:
            continue
            
        filtered_bets.append(bet)
        outcome = bet.get('outcome')
        placed_at = bet.get('placed_at', '')
        
        # Robust Date Parsing
        date_key = "Unknown"
        day_name = "Unknown"
        if placed_at:
            try:
                dt_obj = datetime.strptime(placed_at, '%Y-%m-%d %H:%M:%S')
                date_key = dt_obj.strftime('%Y-%m-%d')
                day_name = dt_obj.strftime('%A')
            except:
                date_key = placed_at.split(' ')[0]

        # Calculate metrics
        is_win = (outcome == 'win')
        profit_change = 1 if is_win else -1
        cumulative_profit += profit_change
        
        # Update Daily Volume
        if is_win:
            daily_summary[date_key]["wins"] += 1
            perf_score[bet.get('36_score', 'N/A')]["wins"] += 1
            perf_country[country]["wins"] += 1
            if day_name in week_order: perf_day[day_name]["wins"] += 1
        else:
            daily_summary[date_key]["losses"] += 1
            perf_score[bet.get('36_score', 'N/A')]["losses"] += 1
            perf_country[country]["losses"] += 1
            if day_name in week_order: perf_day[day_name]["losses"] += 1

        profit_trend.append({"date": date_key, "profit": cumulative_profit})

    def calc_wr(d):
        return {k: round(v['wins']/(v['wins']+v['losses'])*100, 2) 
                for k, v in d.items() if (v['wins']+v['losses']) > 0}

    # Sort Day of Week Performance
    sorted_perf_day = {day: calc_wr(perf_day).get(day, 0) for day in week_order if day in perf_day}
    
    # Sort Daily Summary by date
    sorted_days = sorted(daily_summary.keys())

    return jsonify({
        "kpis": calculate_kpis(filtered_bets),
        "filter_options": sorted(list(available_filters)),
        "daily_summary": {
            "labels": sorted_days,
            "wins": [daily_summary[d]["wins"] for d in sorted_days],
            "losses": [daily_summary[d]["losses"] for d in sorted_days]
        },
        "performance_by_initial_score": calc_wr(perf_score),
        "performance_by_day_of_week": sorted_perf_day,
        "performance_by_country": calc_wr(perf_country),
        "daily_profit_trend": profit_trend,
        "recent_bets": filtered_bets[::-1][:50] # Show newest at top of table
    })

if __name__ == '__main__':
    app.run(debug=True)
