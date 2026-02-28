from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import firestore, credentials, initialize_app
import os
import json
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Firebase Initialization
try:
    FIREBASE_CREDENTIALS_JSON_STRING = os.getenv("FIREBASE_CREDENTIALS_JSON")
    cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON_STRING)
    cred = credentials.Certificate(cred_dict)
    if not firebase_admin._apps:
        initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"❌ Firebase Init Error: {e}")

def calculate_kpis(bets):
    total = len(bets)
    if total == 0: return {"total_bets": 0, "win_rate": 0, "net_profit": 0, "roi": 0}
    wins = [b for b in bets if b.get('outcome') == 'win']
    win_rate = (len(wins) / total) * 100
    # Assuming 1 unit stake per bet
    net_profit = len(wins) - (total - len(wins))
    return {
        "total_bets": total,
        "win_rate": round(win_rate, 2),
        "net_profit": net_profit,
        "roi": round((net_profit / total) * 100, 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard_data')
def get_dashboard_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    league_filter = request.args.get('league')

    # Base Query
    query = db.collection('resolved_bets')
    if start_date: query = query.where('placed_at', '>=', start_date)
    if end_date: query = query.where('placed_at', '<=', end_date)
    
    docs = query.order_by('placed_at', direction=firestore.Query.DESCENDING).stream()
    all_bets_raw = [doc.to_dict() for doc in docs]

    # Data Containers
    available_filters = set()
    filtered_bets = []
    daily_summary = defaultdict(lambda: {"wins": 0, "losses": 0})
    perf_score = defaultdict(lambda: {"wins": 0, "losses": 0})
    perf_day = defaultdict(lambda: {"wins": 0, "losses": 0})
    perf_country = defaultdict(lambda: {"wins": 0, "losses": 0})
    profit_trend = []
    cumulative_profit = 0

    for bet in all_bets_raw:
        country = bet.get('country', 'Unknown')
        league = bet.get('league', 'Unknown')
        display_name = f"{country} - {league}"
        available_filters.add(display_name)

        # Filter Logic
        if league_filter and league_filter != "All" and display_name != league_filter:
            continue
            
        filtered_bets.append(bet)
        outcome = bet.get('outcome')
        placed_at = bet.get('placed_at', '')
        day_str = placed_at.split(' ')[0] if placed_at else "N/A"
        
        # 1. KPI & Summary Logic
        if outcome == 'win':
            cumulative_profit += 1
            daily_summary[day_str]["wins"] += 1
            perf_score[bet.get('36_score', 'N/A')]["wins"] += 1
            perf_country[country]["wins"] += 1
            if placed_at:
                day_name = datetime.strptime(placed_at, '%Y-%m-%d %H:%M:%S').strftime('%A')
                perf_day[day_name]["wins"] += 1
        else:
            cumulative_profit -= 1
            daily_summary[day_str]["losses"] += 1
            perf_score[bet.get('36_score', 'N/A')]["losses"] += 1
            perf_country[country]["losses"] += 1
            if placed_at:
                day_name = datetime.strptime(placed_at, '%Y-%m-%d %H:%M:%S').strftime('%A')
                perf_day[day_name]["losses"] += 1

        profit_trend.append({"date": day_str, "profit": cumulative_profit})

    def calc_wr(d):
        return {k: round(v['wins']/(v['wins']+v['losses'])*100, 2) for k, v in d.items() if (v['wins']+v['losses']) > 0}

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
        "performance_by_day_of_week": calc_wr(perf_day),
        "performance_by_country": calc_wr(perf_country),
        "daily_profit_trend": profit_trend[::-1],
        "recent_bets": filtered_bets[:50]
    })

if __name__ == '__main__':
    app.run(debug=True)
