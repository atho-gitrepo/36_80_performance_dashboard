from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import firestore, credentials, initialize_app
import os
import json
from datetime import datetime, timedelta

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
    # Consider what to do here. Maybe render an error page.

# --- Data Processing Functions ---
def calculate_kpis(bets):
    """Calculates all key performance metrics from a list of bet documents."""
    total_bets = len(bets)
    if total_bets == 0:
        return {
            "total_bets": 0, "win_rate": 0, "net_profit": 0,
            "roi": 0, "biggest_win_streak": 0, "biggest_loss_streak": 0
        }

    wins = [b for b in bets if b['outcome'] == 'win']
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
        if bet['outcome'] == 'win':
            current_win_streak += 1
            biggest_win_streak = max(biggest_win_streak, current_win_streak)
            current_loss_streak = 0
        elif bet['outcome'] == 'loss':
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
        query = db.collection('resolved_bets')
        if start_date:
            query = query.where('placed_at', '>=', start_date)
        if end_date:
            query = query.where('placed_at', '<=', end_date)
        if match_name:
            query = query.where('match_name', '==', match_name)
        if league_name:
            query = query.where('league', '==', league_name)

        docs = query.order_by('resolved_at', direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in docs]
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
    
    # Get date range and filters from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    match_name = request.args.get('match_name')
    league_name = request.args.get('league')

    start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
    end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

    bets = get_resolved_bets_data(start_date, end_date, match_name, league_name)
    
    kpis = calculate_kpis(bets)
    
    # New data structures to replace profit trends
    outcome_by_initial_score = {}
    performance_by_day_of_week = {}
    
    # New data structures for the new charts
    performance_by_country = {}
    performance_by_bet_type = {}
    
    for bet in bets:
        # Determine the initial score key
        bet_type = bet.get('bet_type', 'Unknown')
        initial_score_key = '36_score' if bet_type == 'regular' else '80_score'
        initial_score = bet.get(initial_score_key, 'N/A')
        
        # Performance by Initial Score
        if initial_score not in outcome_by_initial_score:
            outcome_by_initial_score[initial_score] = {"wins": 0, "losses": 0}
        
        if bet['outcome'] == 'win':
            outcome_by_initial_score[initial_score]['wins'] += 1
        else:
            outcome_by_initial_score[initial_score]['losses'] += 1
            
        # Performance by Day of the Week
        placed_at = bet.get('placed_at')
        if placed_at:
            day_of_week = datetime.fromisoformat(placed_at).strftime('%A')
            if day_of_week not in performance_by_day_of_week:
                performance_by_day_of_week[day_of_week] = {"wins": 0, "losses": 0}
            if bet['outcome'] == 'win':
                performance_by_day_of_week[day_of_week]['wins'] += 1
            else:
                performance_by_day_of_week[day_of_week]['losses'] += 1
                
        # --- New: Performance by Country ---
        country = bet.get('country', 'Unknown')
        if country not in performance_by_country:
            performance_by_country[country] = {"wins": 0, "losses": 0}
        if bet['outcome'] == 'win':
            performance_by_country[country]['wins'] += 1
        else:
            performance_by_country[country]['losses'] += 1

        # --- New: Performance by Bet Type ---
        bet_type_name = bet.get('bet_type', 'Unknown')
        if bet_type_name not in performance_by_bet_type:
            performance_by_bet_type[bet_type_name] = {"wins": 0, "losses": 0}
        if bet['outcome'] == 'win':
            performance_by_bet_type[bet_type_name]['wins'] += 1
        else:
            performance_by_bet_type[bet_type_name]['losses'] += 1

    return jsonify({
        "kpis": kpis,
        "outcome_by_initial_score": outcome_by_initial_score,
        "performance_by_day_of_week": performance_by_day_of_week,
        "performance_by_country": performance_by_country,
        "performance_by_bet_type": performance_by_bet_type,
        "recent_bets": bets[:50]
    })

if __name__ == '__main__':
    # Running locally for development
    app.run(debug=True, port=8000)
