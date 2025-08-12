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

def get_resolved_bets_data(start_date=None, end_date=None):
    """Fetches resolved bets from Firestore, with optional date filtering."""
    try:
        query = db.collection('resolved_bets')
        if start_date:
            query = query.where('placed_at', '>=', start_date)
        if end_date:
            query = query.where('placed_at', '<=', end_date)
            
        docs = query.order_by('placed_at', direction=firestore.Query.DESCENDING).stream()
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
    
    # Get date range from request or set defaults
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Convert date strings to datetime objects for filtering
    start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
    end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

    bets = get_resolved_bets_data(start_date, end_date)
    
    kpis = calculate_kpis(bets)
    
    # More complex calculations
    performance_by_league = {}
    performance_by_type = {}
    profit_trends = {}
    cumulative_pnl = 0
    running_pnl_data = []
    
    for bet in sorted(bets, key=lambda x: x.get('placed_at')):
        # Performance by League
        league = bet.get('league', 'Unknown')
        if league not in performance_by_league:
            performance_by_league[league] = {"wins": 0, "losses": 0}
        if bet['outcome'] == 'win':
            performance_by_league[league]['wins'] += 1
        else:
            performance_by_league[league]['losses'] += 1
            
        # Performance by Bet Type
        bet_type = bet.get('bet_type', 'Unknown')
        if bet_type not in performance_by_type:
            performance_by_type[bet_type] = {"wins": 0, "losses": 0}
        if bet['outcome'] == 'win':
            performance_by_type[bet_type]['wins'] += 1
        else:
            performance_by_type[bet_type]['losses'] += 1
            
        # Profit Trends
        date_key = datetime.fromisoformat(bet['placed_at']).strftime('%Y-%m-%d')
        if date_key not in profit_trends:
            profit_trends[date_key] = 0
        
        # Cumulative P&L
        cumulative_pnl += 1 if bet['outcome'] == 'win' else -1
        running_pnl_data.append({"date": date_key, "pnl": cumulative_pnl})
        
    return jsonify({
        "kpis": kpis,
        "performance_by_league": performance_by_league,
        "performance_by_type": performance_by_type,
        "profit_trends": profit_trends,
        "running_pnl": running_pnl_data,
        "recent_bets": bets[:50] # Limit to 50 for the log table
    })

if __name__ == '__main__':
    # Running locally for development
    app.run(debug=True, port=8000)

