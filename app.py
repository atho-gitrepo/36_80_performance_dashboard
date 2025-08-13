from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import firestore, credentials
import os
import json
from datetime import datetime, timedelta
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Firebase Initialization ---
try:
    FIREBASE_CREDENTIALS_JSON_STRING = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not FIREBASE_CREDENTIALS_JSON_STRING:
        raise ValueError("FIREBASE_CREDENTIALS_JSON is not set.")
    
    cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON_STRING)
    cred = credentials.Certificate(cred_dict)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("✅ Firebase initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Firebase: {e}")
    raise

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
    
    win_rate = (win_count / total_bets) * 100 if total_bets > 0 else 0
    
    # Assuming a hypothetical bet size of 1 unit
    net_profit = win_count - (total_bets - win_count)
    roi = (net_profit / total_bets) * 100 if total_bets > 0 else 0
    
    # Calculate streaks
    current_win_streak = 0
    biggest_win_streak = 0
    current_loss_streak = 0
    biggest_loss_streak = 0
    
    for bet in bets:
        outcome = bet.get('outcome')
        if outcome == 'win':
            current_win_streak += 1
            biggest_win_streak = max(biggest_win_streak, current_win_streak)
            current_loss_streak = 0
        elif outcome == 'loss':
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
    """More robust data fetcher with debug capabilities"""
    try:
        col_ref = db.collection('resolved_bets')
        query = col_ref
        
        # Debug: Print collection stats
        print(f"📊 Collection stats: {col_ref.count().get()[0]} total documents")
        
        # Convert string dates to datetime if needed
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        # Apply date filters if provided
        if start_date:
            query = query.where('resolved_at', '>=', start_date)
        if end_date:
            query = query.where('resolved_at', '<=', end_date)
        
        # Add debug query
        debug_query = query.limit(1)
        print(f"🔍 Sample document: {[doc.to_dict() for doc in debug_query.stream()]}")
        
        # Get full results
        docs = query.order_by('resolved_at', direction=firestore.Query.DESCENDING).stream()
        bets = []
        
        for doc in docs:
            data = doc.to_dict()
            # Ensure required fields exist
            data['id'] = doc.id
            data.setdefault('outcome', 'unknown')
            data.setdefault('resolved_at', datetime.utcnow().isoformat())
            bets.append(data)
        
        print(f"✅ Found {len(bets)} resolved bets")
        return bets
        
    except Exception as e:
        print(f"🔥 Error fetching resolved bets: {e}")
        # Try fallback query without filters
        try:
            docs = db.collection('resolved_bets').limit(10).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as fallback_error:
            print(f"🔥 Fallback query failed: {fallback_error}")
            return []

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard_data')
def get_dashboard_data():
    """API endpoint to fetch processed data for the dashboard."""
    try:
        # Get date range from request or set defaults
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        # Convert date strings to datetime objects
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

        bets = get_resolved_bets_data(start_date, end_date)
        
        # Debug: Print first bet if available
        if bets:
            logger.info(f"Sample bet data: {bets[0]}")
        
        kpis = calculate_kpis(bets)
        
        # Initialize data structures
        performance_by_league = {}
        performance_by_type = {}
        daily_results = {}
        cumulative_pnl = 0
        running_pnl_data = []
        
        for bet in sorted(bets, key=lambda x: x.get('resolved_at', '')):
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
                
            # Daily Results
            placed_at = bet.get('resolved_at')
            if isinstance(placed_at, str):
                placed_at = datetime.fromisoformat(placed_at)
            date_key = placed_at.strftime('%Y-%m-%d') if placed_at else 'unknown-date'
            
            if date_key not in daily_results:
                daily_results[date_key] = {"wins": 0, "losses": 0, "net": 0}
            
            if bet['outcome'] == 'win':
                daily_results[date_key]["wins"] += 1
                daily_results[date_key]["net"] += 1
            else:
                daily_results[date_key]["losses"] += 1
                daily_results[date_key]["net"] -= 1
            
            # Cumulative P&L
            cumulative_pnl += 1 if bet['outcome'] == 'win' else -1
            running_pnl_data.append({"date": date_key, "pnl": cumulative_pnl})
            
        # Convert daily results to sorted list
        daily_results_list = [
            {
                "date": date, 
                "wins": data["wins"], 
                "losses": data["losses"],
                "net": data["net"]
            }
            for date, data in daily_results.items()
            if date != 'unknown-date'
        ]
        daily_results_list.sort(key=lambda x: x["date"])
        
        return jsonify({
            "kpis": kpis,
            "performance_by_league": performance_by_league,
            "performance_by_type": performance_by_type,
            "daily_results": daily_results_list,
            "running_pnl": running_pnl_data,
            "recent_bets": bets[:50]  # Limit to 50 for the log table
        })
        
    except Exception as e:
        logger.error(f"Error in dashboard_data endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# Debug endpoint to check Firestore connection
@app.route('/debug/firestore')
def debug_firestore():
    try:
        docs = db.collection('resolved_bets').limit(5).stream()
        bets = [doc.to_dict() for doc in docs]
        return jsonify({
            "status": "success",
            "count": len(bets),
            "sample_data": bets,
            "collection": "resolved_bets"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)

