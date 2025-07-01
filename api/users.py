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

@app.route('/api/users', methods=['GET'])
@require_auth
def api_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get users with their stats
        cursor.execute('''
            SELECT u.id, u.registration_date, u.last_activity, u.total_trades, u.profit,
                   COUNT(t.id) as recent_trades,
                   AVG(CASE WHEN t.profit > 0 THEN 1.0 ELSE 0.0 END) * 100 as win_rate
            FROM users u
            LEFT JOIN trades t ON u.id = t.user_id AND t.timestamp > datetime('now', '-7 days')
            GROUP BY u.id
            ORDER BY u.last_activity DESC
        ''') if hasattr(cursor, 'execute') else None
        
        users_data = cursor.fetchall() if cursor else []
        conn.close() if conn else None
        
        # Format users data
        users = []
        for user in users_data:
            users.append({
                'user_id': user[0],
                'registration_date': user[1],
                'last_activity': user[2],
                'total_trades': user[3] or 0,
                'profit': user[4] or 0.0,
                'recent_trades': user[5] or 0,
                'win_rate': user[6] or 0.0,
                'ai_accuracy': min(95, 60 + (user[3] or 0) / 10),  # Mock calculation
                'risk_level': 'Medium',
                'balance': (user[4] or 0) + 1000,  # Mock balance
                'equity': (user[4] or 0) + 1000
            })
        
        return jsonify({
            'users': users,
            'stats': {
                'total': len(users),
                'active': len([u for u in users if u['last_activity']]),
                'total_profit': sum(u['profit'] for u in users)
            }
        })
        
    except Exception as e:
        logging.error(f"Users API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>/details', methods=['GET'])
@require_auth
def user_details(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user details
        cursor.execute('''
            SELECT id, registration_date, last_activity, total_trades, profit
            FROM users WHERE id = ?
        ''', (user_id,)) if hasattr(cursor, 'execute') else None
        
        user = cursor.fetchone() if cursor else None
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get trade history for profit chart
        cursor.execute('''
            SELECT DATE(timestamp) as date, SUM(profit) as daily_profit
            FROM trades 
            WHERE user_id = ? 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''', (user_id,)) if hasattr(cursor, 'execute') else None
        
        profit_history = cursor.fetchall() if cursor else []
        conn.close() if conn else None
        
        return jsonify({
            'user_id': user[0],
            'registration_date': user[1],
            'last_activity': user[2],
            'balance': (user[4] or 0) + 1000,
            'equity': (user[4] or 0) + 1000,
            'total_trades': user[3] or 0,
            'winning_trades': int((user[3] or 0) * 0.65),  # Mock
            'losing_trades': int((user[3] or 0) * 0.35),   # Mock
            'win_rate': 65.0,  # Mock
            'profit_history': {
                'labels': [p[0] for p in profit_history],
                'data': [p[1] for p in profit_history]
            }
        })
        
    except Exception as e:
        logging.error(f"User details error: {e}")
        return jsonify({'error': str(e)}), 500

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
