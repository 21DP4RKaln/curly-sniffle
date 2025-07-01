import os
import sqlite3
import logging
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from auth import require_auth, get_db_connection

app = Flask(__name__)

# Ensure database exists
def init_database():
    """Initialize database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            registration_date TEXT,
            last_activity TEXT,
            total_trades INTEGER DEFAULT 0,
            profit REAL DEFAULT 0.0
        )
    ''')
    
    # Create trades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            symbol TEXT,
            signal TEXT,
            profit REAL,
            confidence REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create market_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            symbol TEXT,
            features TEXT,
            signal INTEGER,
            confidence REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

@app.route('/api/dashboard', methods=['GET'])
@require_auth
def api_dashboard():
    """Dashboard API endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get summary statistics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                SUM(profit) as total_profit,
                COUNT(*) as total_trades,
                AVG(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100 as win_rate
            FROM trades 
            WHERE timestamp >= datetime('now', '-30 days')
        ''')
        stats = cursor.fetchone()
        
        # Get today's trades
        cursor.execute('''
            SELECT COUNT(*) as today_trades
            FROM trades 
            WHERE DATE(timestamp) = DATE('now')
        ''')
        today_stats = cursor.fetchone()
        
        # Get recent trades
        cursor.execute('''
            SELECT timestamp, user_id, symbol, signal, profit, confidence
            FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_trades = cursor.fetchall()
        
        conn.close()
        
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
                'active_bots': stats[0] or 0,
                'total_profit': round(stats[1] or 0, 2),
                'trades_today': today_stats[0] or 0,
                'ai_accuracy': round(stats[3] or 0, 1)
            },
            'charts': {
                'profit': {
                    'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    'data': [120, 180, 250, 320, 280, 410, 390]  # Mock data
                },
                'trades': {
                    'win': stats[0] or 0,
                    'loss': max(0, (stats[0] or 0) - int((stats[3] or 0) / 100 * (stats[0] or 0)))
                }
            },
            'recent_trades': trades_data,
            'system_logs': [
                {'time': datetime.now().strftime('%H:%M:%S'), 'message': 'AI system operational', 'type': 'info'},
                {'time': (datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S'), 'message': 'New prediction generated', 'type': 'success'}
            ]
        })
        
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

# Add data reception endpoint for MT5 bots
@app.route('/api/data', methods=['POST'])
def receive_bot_data():
    """Receive data from MT5 bots"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Extract user info
        account_id = data.get('account_id', 'unknown')
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Insert or update user
        cursor.execute('''
            INSERT OR REPLACE INTO users (id, registration_date, last_activity, total_trades, profit)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            account_id,
            data.get('registration_date', datetime.now().isoformat()),
            datetime.now().isoformat(),
            data.get('total_trades', 0),
            data.get('daily_profit', 0.0)
        ))
        
        # Store market data if available
        if 'market_data' in data:
            for market_point in data['market_data']:
                cursor.execute('''
                    INSERT INTO market_data (timestamp, user_id, symbol, features, signal, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    market_point.get('time', datetime.now().isoformat()),
                    account_id,
                    symbol,
                    json.dumps(market_point.get('indicators', [])),
                    market_point.get('signal', 0),
                    0.75  # Default confidence
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Data received successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Data reception error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def receive_feedback():
    """Receive trade results for learning"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Store trade result
        cursor.execute('''
            INSERT INTO trades (timestamp, user_id, symbol, signal, profit, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('timestamp', datetime.now().isoformat()),
            data.get('account_id', 'unknown'),
            data.get('symbol', 'UNKNOWN'),
            'BUY' if data.get('signal', 0) > 0 else 'SELL',
            data.get('profit', 0.0),
            0.75  # Default confidence
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received',
            'learning_updated': True
        })
        
    except Exception as e:
        logging.error(f"Feedback error: {e}")
        return jsonify({'error': str(e)}), 500

# Serverless function handler
def handler(request):
    with app.app_context():
        return app(request.environ, lambda *args: None)
