#!/usr/bin/env python3
"""
SVN Trading Bot API
Main API handler for Vercel serverless deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import jwt
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import our modules (handle both relative and absolute imports)
try:
    from .auth import authenticate_api_key, verify_token, authenticate_user, register_user
    from .ai_service import get_ai_prediction, analyze_smart_money, update_ai_model, get_ai_model_info
    from .database import save_trade_data, save_ai_prediction, update_account_data, get_performance_statistics
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from auth import authenticate_api_key, verify_token, authenticate_user, register_user
    from ai_service import get_ai_prediction, analyze_smart_money, update_ai_model, get_ai_model_info
    from database import save_trade_data, save_ai_prediction, update_account_data, get_performance_statistics

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'svn-trading-bot-secret-key-2025')
DATABASE_URL = os.environ.get('DATABASE_URL', '')
API_VERSION = '1.0.0'

# In-memory storage for demo (replace with real database)
users_db = {}
trades_db = {}
predictions_cache = {}
statistics = {
    'total_trades': 0,
    'win_rate': 0.0,
    'total_profit': 0.0,
    'active_positions': 0
}

# Sample market data storage
market_data = {
    'balance': 10000.0,
    'equity': 10000.0,
    'free_margin': 10000.0,
    'margin_level': 100.0
}

# Market data cache
market_data_cache = {}
symbol_subscriptions = set()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': API_VERSION,
        'timestamp': datetime.now().isoformat(),
        'database_status': 'connected' if DATABASE_URL else 'not_configured'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User authentication endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No credentials provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Use auth module
        result = authenticate_user(email, password)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', 'User')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Use auth module
        result = register_user(email, password, name)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 409
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def ai_predict():
    """AI prediction endpoint for trading signals"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = verify_token(token)
        else:
            api_key = request.headers.get('X-API-Key', '')
            auth_result = authenticate_api_key(api_key)
        
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['symbol', 'timeframe', 'features']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Extract features
        symbol = data['symbol']
        timeframe = data['timeframe']
        features = data['features']
        
        # Get AI prediction
        prediction = get_ai_prediction(symbol, features)
        
        # Store prediction in cache
        prediction_id = f"{symbol}_{timeframe}_{datetime.now().timestamp()}"
        predictions_cache[prediction_id] = {
            'symbol': symbol,
            'timeframe': timeframe,
            'prediction': prediction['signal'],
            'confidence': prediction['confidence'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to database
        save_ai_prediction({
            'prediction_id': prediction_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'features': features,
            'prediction': prediction['signal'],
            'confidence': prediction['confidence']
        })
        
        return jsonify({
            'prediction_id': prediction_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': prediction['signal'],
            'confidence': prediction['confidence'],
            'signal_strength': prediction.get('signal_strength', 0),
            'market_context': prediction.get('market_context', {}),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def trade_feedback():
    """Trade feedback endpoint for AI improvement"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = verify_token(token)
        else:
            api_key = request.headers.get('X-API-Key', '')
            auth_result = authenticate_api_key(api_key)
        
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['prediction_id', 'actual_result', 'profit']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        prediction_id = data['prediction_id']
        actual_result = data['actual_result']
        profit = data['profit']
        
        # Update prediction with actual result
        if prediction_id in predictions_cache:
            predictions_cache[prediction_id]['actual_result'] = actual_result
            predictions_cache[prediction_id]['profit'] = profit
            predictions_cache[prediction_id]['feedback_timestamp'] = datetime.now().isoformat()
        
        # Update statistics
        statistics['total_trades'] += 1
        statistics['total_profit'] += profit
        
        if profit > 0:
            win_trades = statistics.get('win_trades', 0) + 1
            statistics['win_trades'] = win_trades
            statistics['win_rate'] = (win_trades / statistics['total_trades']) * 100
        
        # Update AI model with feedback
        feedback_data = [{
            'predicted_signal': predictions_cache.get(prediction_id, {}).get('prediction', 0),
            'actual_result': actual_result,
            'profit': profit
        }]
        update_ai_model(feedback_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received and processed',
            'prediction_id': prediction_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/save', methods=['POST'])
def save_trade():
    """Save trade data endpoint"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = verify_token(token)
        else:
            api_key = request.headers.get('X-API-Key', '')
            auth_result = authenticate_api_key(api_key)
        
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['trade_id', 'symbol', 'type', 'lot_size', 'open_price']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        trade_id = data['trade_id']
        
        # Save trade to database
        trade_data = {
            'trade_id': trade_id,
            'symbol': data['symbol'],
            'type': data['type'],
            'lot_size': data['lot_size'],
            'open_price': data['open_price'],
            'close_price': data.get('close_price'),
            'stop_loss': data.get('stop_loss'),
            'take_profit': data.get('take_profit'),
            'open_time': data.get('open_time', datetime.now().isoformat()),
            'close_time': data.get('close_time'),
            'profit': data.get('profit'),
            'commission': data.get('commission'),
            'swap': data.get('swap'),
            'signal': data.get('signal'),
            'confidence': data.get('confidence'),
            'is_active': data.get('is_active', True),
            'timestamp': datetime.now().isoformat()
        }
        
        trades_db[trade_id] = trade_data
        save_trade_data(trade_data)
        
        # Update active positions count
        active_count = sum(1 for trade in trades_db.values() if trade.get('is_active', True))
        statistics['active_positions'] = active_count
        
        return jsonify({
            'status': 'success',
            'message': 'Trade saved successfully',
            'trade_id': trade_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/update', methods=['POST'])
def update_account():
    """Update account information endpoint"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = verify_token(token)
        else:
            api_key = request.headers.get('X-API-Key', '')
            auth_result = authenticate_api_key(api_key)
        
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update market data
        if 'balance' in data:
            market_data['balance'] = float(data['balance'])
        if 'equity' in data:
            market_data['equity'] = float(data['equity'])
        if 'free_margin' in data:
            market_data['free_margin'] = float(data['free_margin'])
        if 'margin_level' in data:
            market_data['margin_level'] = float(data['margin_level'])
        
        market_data['last_updated'] = datetime.now().isoformat()
        
        # Save to database
        update_account_data(data)
        
        return jsonify({
            'status': 'success',
            'message': 'Account information updated',
            'market_data': market_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get dashboard data endpoint"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = verify_token(token)
        else:
            api_key = request.headers.get('X-API-Key', '')
            auth_result = authenticate_api_key(api_key)
        
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'statistics': statistics,
            'market_data': market_data,
            'predictions_cache': predictions_cache,
            'recent_trades': list(trades_db.values())[-10:],  # Last 10 trades
            'version': API_VERSION,
            'ai_model_info': get_ai_model_info()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/data', methods=['POST'])
def receive_market_data():
    """Receive market data from MT5"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
        else:
            api_key = request.headers.get('X-API-Key', '')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        auth_result = authenticate_api_key(api_key)
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Process market data
        symbol = data['symbol']
        timeframe = data['timeframe']
        
        # Store in cache
        cache_key = f"{symbol}_{timeframe}"
        if cache_key not in market_data_cache:
            market_data_cache[cache_key] = []
        
        market_tick = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': data['timestamp'],
            'open': float(data['open']),
            'high': float(data['high']),
            'low': float(data['low']),
            'close': float(data['close']),
            'volume': int(data['volume']),
            'spread': data.get('spread', 0.0),
            'indicators': data.get('indicators', {}),
            'received_at': datetime.now().isoformat()
        }
        
        market_data_cache[cache_key].append(market_tick)
        
        # Keep only last 1000 candles per symbol/timeframe
        if len(market_data_cache[cache_key]) > 1000:
            market_data_cache[cache_key] = market_data_cache[cache_key][-1000:]
        
        return jsonify({
            'status': 'success',
            'message': 'Market data received',
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': market_tick['received_at']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/signals', methods=['GET'])
def get_trading_signals():
    """Get current trading signals for all subscribed symbols"""
    try:
        # Authenticate request
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_result = verify_token(token)
        else:
            api_key = request.headers.get('X-API-Key', '')
            auth_result = authenticate_api_key(api_key)
        
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        signals = []
        
        # Generate signals for each symbol with data
        for cache_key, price_data in market_data_cache.items():
            if len(price_data) >= 50:
                symbol = cache_key.split('_')[0]
                
                # Get latest data
                latest_data = price_data[-1]
                features = latest_data.get('indicators', {})
                
                # Add price features
                features.update({
                    'close': latest_data['close'],
                    'volume': latest_data['volume'],
                    'spread': latest_data.get('spread', 0)
                })
                
                # Get AI prediction
                prediction = get_ai_prediction(symbol, features)
                
                if prediction['confidence'] > 0.7:  # Only include high-confidence signals
                    signals.append({
                        'symbol': symbol,
                        'signal': prediction['signal'],
                        'confidence': prediction['confidence'],
                        'signal_strength': prediction.get('signal_strength', 0),
                        'market_context': prediction.get('market_context', {}),
                        'timestamp': prediction['timestamp'],
                        'current_price': latest_data['close']
                    })
        
        return jsonify({
            'signals': signals,
            'total_signals': len(signals),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=True)
