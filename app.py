from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import firestore, credentials, initialize_app
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time  # Import the time module

app = Flask(__name__)

# --- Firebase Initialization (Modified for a web app) ---
try:
    FIREBASE_CREDENTIALS_JSON_STRING = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not FIREBASE_CREDENTIALS_JSON_STRING:
        raise ValueError("FIREBASE_CREDENTIALS_JSON is not set.")
    
    cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON_STRING)
    cred = credentials.Certificate(cred_dict)

    if not firebase_admin._apps:
        initialize_app(cred)
    db = firestore.client()
    print("✅ Web app: Firebase initialized successfully.")
except Exception as e:
    print(f"❌ Web app: Failed to initialize Firebase: {e}")
    # In a production app, you might want to handle this gracefully
    # e.g., by returning an error page or a 500 status code.

# --- Data Processing Functions ---
def calculate_kpis(bets):
    """Calculates all key performance metrics from a list of bet documents."""
    total_bets = len(bets)
    if total_bets == 0:
        return {
            "total_bets": 0, "win_rate": 0, "net_profit": 0,
            "roi": 0, "biggest_win_streak": 0, "biggest_loss_streak": 0
        }

    wins = [b for b in bets if b.get('outcome') == 'win']
    win_count = len(wins)
    
    win_rate = (win_count / total_bets) * 100
    
    # Assuming a hypothetical bet size of 1 unit
    net_profit = win_count - (total_bets - win_count)
    roi = (net_profit / total_bets) * 100 if total_bets > 0 else 0
    
    # Calculate streaks (simplified)
    current_win_streak = 0
    biggest_win_streak = 0
    current_loss_streak = 0
    biggest_loss_streak = 0
    
    for bet in bets:
        if bet.get('outcome') == 'win':
            current_win_streak += 1
            biggest_win_streak = max(biggest_win_streak, current_win_streak)
            current_loss_streak = 0
        elif bet.get('outcome') == 'loss':
            current_loss_streak += 1
            biggest_loss_streak = max(biggest_loss_streak, current_loss_streak)
            current_win_streak = 0

    return {
        "total_bets": total_bets,
        "win_rate": round(win_rate, 2),
        "net_profit": net_profit,
        "roi": round(roi, 2),
        "biggest_win_streak": biggest_win_streak,
        "biggest_loss_streak": biggest_loss_streak,
    }

def get_resolved_bets_data(start_date=None, end_date=None, match_name=None, league_name=None):
    """Fetches resolved bets from Firestore, with optional date and name filtering."""
    try:
        print(f"🔄 Starting Firestore data fetch with filters: start_date={start_date}, end_date={end_date}, match_name={match_name}, league_name={league_name}")
        start_time = time.time()
        
        query = db.collection('resolved_bets')
        
        # Use a single query that combines filters
        if start_date:
            query = query.where('placed_at', '>=', start_date)
        if end_date:
            query = query.where('placed_at', '<=', end_date)
        
        # Note: '==' filtering for match/league names can be slow without indexes
        if match_name:
            query = query.where('match_name', '==', match_name)
        if league_name:
            query = query.where('league', '==', league_name)
        
        # Always order by a field used in the query for performance
        docs = query.order_by('placed_at', direction=firestore.Query.DESCENDING).stream()
        
        data = [doc.to_dict() for doc in docs]
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ Firestore data fetch completed. Fetched {len(data)} documents in {duration:.2f} seconds.")
        
        return data
    except Exception as e:
        print(f"❌ Firestore Error during data fetch: {e}")
        return []

# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('index.html')

@app.route('/api/dashboard_data')
def get_dashboard_data():
    """API endpoint to fetch processed data for the dashboard."""
    
    print("➡️ API call received for /api/dashboard_data.")
    request_start_time = time.time()
    
    # Get date range and filters from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    match_name = request.args.get('match_name')
    league_name = request.args.get('league')

    start_date = start_date_str if start_date_str else None
    end_date = end_date_str if end_date_str else None

    bets = get_resolved_bets_data(start_date, end_date, match_name, league_name)
    
    kpis = calculate_kpis(bets)
    
    # New data structures to build charts
    performance_by_initial_score = defaultdict(lambda: {"wins": 0, "losses": 0})
    performance_by_day_of_week = defaultdict(lambda: {"wins": 0, "losses": 0})
    performance_by_country = defaultdict(lambda: {"wins": 0, "losses": 0})
    performance_by_bet_type = defaultdict(lambda: {"wins": 0, "losses": 0})
    daily_profit_trend = defaultdict(int)
    
    data_processing_start = time.time()
    for bet in bets:
        try:
            outcome = bet.get('outcome')
            bet_type = bet.get('bet_type', 'Unknown')
            
            # Profit Calculation
            profit_unit = 1 if outcome == 'win' else -1
            
            # Performance by Initial Score
            initial_score_key = '36_score' if bet_type == 'regular' else '80_score'
            initial_score = bet.get(initial_score_key, 'N/A')
            if outcome == 'win':
                performance_by_initial_score[initial_score]['wins'] += 1
            elif outcome == 'loss':
                performance_by_initial_score[initial_score]['losses'] += 1
            
            # Performance by Day of the Week
            placed_at_str = bet.get('placed_at')
            if placed_at_str:
                placed_at_date = datetime.strptime(placed_at_str, '%Y-%m-%dT%H:%M:%S.%f').date()
                day_of_week = placed_at_date.strftime('%A')
                if outcome == 'win':
                    performance_by_day_of_week[day_of_week]['wins'] += 1
                elif outcome == 'loss':
                    performance_by_day_of_week[day_of_week]['losses'] += 1
                    
                # Daily Profit Trend
                daily_profit_trend[placed_at_date] += profit_unit
                
            # Performance by Country
            country = bet.get('country', 'Unknown')
            if outcome == 'win':
                performance_by_country[country]['wins'] += 1
            elif outcome == 'loss':
                performance_by_country[country]['losses'] += 1

            # Performance by Bet Type
            if outcome == 'win':
                performance_by_bet_type[bet_type]['wins'] += 1
            elif outcome == 'loss':
                performance_by_bet_type[bet_type]['losses'] += 1

        except (KeyError, ValueError) as e:
            print(f"⚠️ Skipping malformed bet document: {e} in {bet}")
            continue

    data_processing_duration = time.time() - data_processing_start
    print(f"⏱️ Data processing completed in {data_processing_duration:.2f} seconds.")

    # Prepare data for plotting
    sorted_daily_profit = sorted(daily_profit_trend.items())
    profit_trend_data = []
    cumulative_profit = 0
    for date, profit in sorted_daily_profit:
        cumulative_profit += profit
        profit_trend_data.append({"date": date.isoformat(), "profit": cumulative_profit})
        
    def calculate_win_rate(data_dict):
        return {
            key: round(val['wins'] / (val['wins'] + val['losses']) * 100, 2)
            if (val['wins'] + val['losses']) > 0 else 0
            for key, val in data_dict.items()
        }

    response_end_time = time.time()
    response_duration = response_end_time - request_start_time
    print(f"✅ Request to /api/dashboard_data completed successfully in {response_duration:.2f} seconds.")

    return jsonify({
        "kpis": kpis,
        "performance_by_initial_score": calculate_win_rate(performance_by_initial_score),
        "performance_by_day_of_week": calculate_win_rate(performance_by_day_of_week),
        "performance_by_country": calculate_win_rate(performance_by_country),
        "performance_by_bet_type": calculate_win_rate(performance_by_bet_type),
        "daily_profit_trend": profit_trend_data,
        "recent_bets": bets[:50]
    })

if __name__ == '__main__':
    # Running locally for development
    app.run(debug=True, port=8081)
