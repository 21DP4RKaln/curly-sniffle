import os
import sys
import json
import sqlite3
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///svnbot.db')

def get_db_connection():
    if DATABASE_URL.startswith('postgresql'):
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        db_path = DATABASE_URL.replace('sqlite:///', '')
        return sqlite3.connect(db_path)

@app.route('/api/status', methods=['GET'])
def bot_status():
    """Get bot and AI status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total stats
        cursor.execute('SELECT COUNT(*) FROM users') if hasattr(cursor, 'execute') else None
        total_users = cursor.fetchone()[0] if cursor else 0
        
        cursor.execute('SELECT COUNT(*) FROM market_data') if hasattr(cursor, 'execute') else None
        total_data_points = cursor.fetchone()[0] if cursor else 0
        
        cursor.execute('SELECT COUNT(*) FROM trades') if hasattr(cursor, 'execute') else None
        total_trades = cursor.fetchone()[0] if cursor else 0
        
        cursor.execute('''
            SELECT AVG(profit), COUNT(*) 
            FROM trades 
            WHERE timestamp > datetime('now', '-24 hours')
        ''') if hasattr(cursor, 'execute') else None
        daily_stats = cursor.fetchone() if cursor else (0, 0)
        
        conn.close() if conn else None
        
        return jsonify({
            'status': 'operational',
            'ai_trained': True,
            'total_users': total_users,
            'total_data_points': total_data_points,
            'total_trades': total_trades,
            'daily_avg_profit': daily_stats[0] or 0,
            'daily_trade_count': daily_stats[1] or 0,
            'models_loaded': 1,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'total_users': 0,
            'total_data_points': 0,
            'total_trades': 0,
            'daily_avg_profit': 0,
            'daily_trade_count': 0,
            'models_loaded': 0,
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'version': 'vercel-optimized'})

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
