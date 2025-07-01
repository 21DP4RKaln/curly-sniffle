import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
import jwt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///svnbot.db')
SECRET_KEY = os.environ.get('SECRET_KEY', 'temp-key')

def get_db_connection():
    if DATABASE_URL.startswith('postgresql'):
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        db_path = DATABASE_URL.replace('sqlite:///', '')
        return sqlite3.connect(db_path)

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['email']
    except:
        return None

def require_auth(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            email = verify_token(token)
            if not email:
                return jsonify({'error': 'Invalid token'}), 401
            request.user_email = email
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Invalid authorization'}), 401
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/dashboard', methods=['GET'])
@require_auth
def api_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute('SELECT COUNT(*) FROM users') if hasattr(cursor, 'execute') else None
        total_users = cursor.fetchone()[0] if cursor else 0
        
        cursor.execute('SELECT COUNT(*) FROM trades WHERE DATE(timestamp) = DATE("now")') if hasattr(cursor, 'execute') else None
        today_trades = cursor.fetchone()[0] if cursor else 0
        
        cursor.execute('SELECT COALESCE(SUM(profit), 0) FROM trades') if hasattr(cursor, 'execute') else None
        total_profit = cursor.fetchone()[0] if cursor else 0
        
        # Recent trades
        cursor.execute('''
            SELECT timestamp, user_id, symbol, signal, profit, confidence
            FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''') if hasattr(cursor, 'execute') else None
        recent_trades = cursor.fetchall() if cursor else []
        
        conn.close() if conn else None
        
        # Format recent trades
        trades_data = []
        for trade in recent_trades:
            trades_data.append({
                'timestamp': trade[0],
                'user_id': trade[1],
                'symbol': trade[2],
                'type': 'buy' if trade[3] == 'BUY' else 'sell',
                'volume': 0.1,  # Default volume
                'profit': trade[4],
                'ai_signal': trade[3]
            })
        
        return jsonify({
            'statistics': {
                'active_bots': total_users,
                'total_profit': round(total_profit, 2),
                'trades_today': today_trades,
                'ai_accuracy': 85.5  # Mock data
            },
            'charts': {
                'profit': {
                    'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    'data': [120, 190, 300, 500, 200, 300, 450]
                },
                'trades': {
                    'profitable': 65,
                    'losing': 35
                }
            },
            'recent_trades': trades_data,
            'system_logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'message': 'AI system operational - Vercel deployment'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Connected users: {total_users}'
                }
            ]
        })
        
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
