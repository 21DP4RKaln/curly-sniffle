import os
import sqlite3
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from auth import require_auth, get_db_connection

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
@require_auth
def api_users():
    """Get all users/bots with their statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get users with their statistics
        cursor.execute('''
            SELECT 
                u.id, u.registration_date, u.last_activity, u.total_trades, u.profit,
                (SELECT COUNT(*) FROM trades t WHERE t.user_id = u.id AND DATE(t.timestamp) = DATE('now')) as recent_trades,
                (SELECT AVG(CASE WHEN profit > 0 THEN 100 ELSE 0 END) FROM trades t WHERE t.user_id = u.id) as win_rate
            FROM users u
            ORDER BY u.last_activity DESC
        ''')
        users_data = cursor.fetchall()
        
        users = []
        for user in users_data:
            users.append({
                'id': user[0],
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
    """Get detailed information about a specific user/bot"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user details
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent trades
        cursor.execute('''
            SELECT timestamp, symbol, signal, profit, confidence
            FROM trades 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''', (user_id,))
        recent_trades = cursor.fetchall()
        
        # Get profit history (last 30 days)
        cursor.execute('''
            SELECT DATE(timestamp) as date, SUM(profit) as daily_profit
            FROM trades 
            WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (user_id,))
        profit_history = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'id': user[0],
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

@app.route('/api/users/<user_id>/trades', methods=['GET'])
@require_auth
def user_trades(user_id):
    """Get trade history for a specific user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, symbol, signal, profit, confidence
            FROM trades 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        trades = cursor.fetchall()
        conn.close()
        
        trades_data = []
        for trade in trades:
            trades_data.append({
                'timestamp': trade[0],
                'symbol': trade[1],
                'signal': trade[2],
                'profit': trade[3],
                'confidence': trade[4]
            })
        
        return jsonify({'trades': trades_data})
        
    except Exception as e:
        logging.error(f"User trades error: {e}")
        return jsonify({'error': str(e)}), 500

# Serverless function handler
def handler(request):
    with app.app_context():
        return app(request.environ, lambda *args: None)
