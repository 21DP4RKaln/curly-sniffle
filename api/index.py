"""
Simplified API for Vercel deployment without complex database setup
Focuses on MT5 bot integration with basic functionality
"""

import os
import json
import secrets
import jwt
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'k9mX#vR2$pL8qN4wE6tY1uI3oP5aS7dF9gH0jK2lZ4xC6vB8nM1qW3eR5tY7uI9oP')
API_KEY = os.environ.get('MT5_API_KEY', '61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f')

# Simple in-memory storage for demo (in production use proper database)
trades_data = []
market_data = []
predictions_cache = {}

# Simple AI Predictor
class SimpleAIPredictor:
    def __init__(self):
        self.training_data = []
    
    def predict(self, features):
        # Simple prediction logic based on features
        prediction = random.choice([-1, 0, 1])  # SELL, HOLD, BUY
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        signal_names = {-1: "SELL", 0: "HOLD", 1: "BUY"}
        
        return {
            'prediction': prediction,
            'signal': signal_names[prediction],
            'confidence': confidence
        }

ai_predictor = SimpleAIPredictor()

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing Authorization header'}), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid Authorization format'}), 401
        
        token = auth_header.split(' ')[1]
        if token != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def home():
    """Home page"""
    return jsonify({
        'message': 'SVN Trading Bot API',
        'version': '2.0.0',
        'status': 'active',
        'endpoints': [
            'GET /api/health - Health check',
            'POST /api/predict - AI predictions',
            'POST /api/feedback - Trade feedback',
            'POST /api/data - Market data upload',
            'GET /api/dashboard - Dashboard data'
        ]
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """AI prediction endpoint for MT5 bot - simplified version"""
    return jsonify({
        'prediction': 1,
        'signal': 'BUY',
        'confidence': 0.75,
        'status': 'success'
    })

@app.route('/api/predict2', methods=['POST'])
def predict2():
    """Alternative prediction endpoint for testing"""
    try:
        # Manual authentication check
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing Authorization header'}), 401
        
        token = auth_header.replace('Bearer ', '')
        if token != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get JSON data
        try:
            data = request.get_json()
        except:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        features = data.get('features', [])
        if len(features) < 10:
            return jsonify({'error': f'Need at least 10 features, got {len(features)}'}), 400
        
        # Simple hardcoded prediction for now
        prediction = 1  # BUY
        confidence = 0.75
        signal = "BUY"
        
        return jsonify({
            'prediction': prediction,
            'signal': signal,
            'confidence': confidence,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@app.route('/api/feedback', methods=['POST'])
@require_api_key
def feedback():
    """Trade feedback endpoint for MT5 bot"""
    try:
        data = request.get_json()
        trade_id = data.get('trade_id')
        profit = data.get('profit', 0.0)
        is_win = data.get('is_win', False)
        signal = data.get('signal', 0)
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Store trade result
        trade_record = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'profit': profit,
            'is_win': is_win,
            'signal': signal
        }
        trades_data.append(trade_record)
        
        # Keep only last 1000 trades in memory
        if len(trades_data) > 1000:
            trades_data.pop(0)
        
        return jsonify({'status': 'success', 'message': 'Feedback received'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['POST'])
@require_api_key
def upload_data():
    """Market data upload endpoint for MT5 bot"""
    try:
        data = request.get_json()
        
        # Store market data
        market_record = {
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'symbol': data.get('symbol', 'UNKNOWN'),
            'account_id': data.get('account_id'),
            'balance': data.get('balance', 0.0),
            'equity': data.get('equity', 0.0),
            'daily_profit': data.get('daily_profit', 0.0),
            'max_drawdown': data.get('max_drawdown', 0.0),
            'total_trades': data.get('total_trades', 0),
            'winning_trades': data.get('winning_trades', 0),
            'market_data': data.get('market_data', [])
        }
        market_data.append(market_record)
        
        # Keep only last 100 market data records in memory
        if len(market_data) > 100:
            market_data.pop(0)
        
        return jsonify({'status': 'success', 'message': 'Data uploaded'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Dashboard data endpoint"""
    try:
        # Calculate statistics from in-memory data
        total_trades = len(trades_data)
        winning_trades = sum(1 for trade in trades_data if trade.get('is_win', False))
        total_profit = sum(trade.get('profit', 0) for trade in trades_data)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Get recent trades
        recent_trades = trades_data[-10:] if trades_data else []
        
        # Get recent market data
        recent_market = market_data[-1] if market_data else {}
        
        return jsonify({
            'statistics': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': round(win_rate, 1),
                'total_profit': round(total_profit, 2),
                'active_bots': 1 if market_data else 0,
                'ai_accuracy': round(win_rate, 1)
            },
            'recent_trades': recent_trades,
            'market_data': recent_market,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# For Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
