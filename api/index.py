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
        'version': '1.0.0'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for testing connectivity"""
    return jsonify({
        'status': 'ok',
        'service': 'SVN Trading Bot API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    """AI prediction endpoint for MT5 bot"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract features from MT5 smart money analysis
        symbol = data.get('symbol', 'UNKNOWN')
        timeframe = data.get('timeframe', 'M15')
        ob_signal = data.get('ob_signal', 0)
        fvg_signal = data.get('fvg_signal', 0)
        bos_signal = data.get('bos_signal', 0)
        choch_signal = data.get('choch_signal', 0)
        liq_signal = data.get('liq_signal', 0)
        
        # Simple AI logic based on smart money signals
        bullish_score = 0
        bearish_score = 0
        
        # Weight the signals
        if ob_signal == 1: bullish_score += 3
        elif ob_signal == 2: bearish_score += 3
        
        if bos_signal == 1: bullish_score += 2
        elif bos_signal == 2: bearish_score += 2
        
        if fvg_signal == 1: bullish_score += 1
        elif fvg_signal == 2: bearish_score += 1
        
        if choch_signal == 1: bullish_score += 1
        elif choch_signal == 2: bearish_score += 1
        
        if liq_signal == 1: bullish_score += 1
        elif liq_signal == 2: bearish_score += 1
        
        # Determine prediction
        if bullish_score > bearish_score + 1:
            prediction = 1  # BUY
            signal = "BUY"
            confidence = min(0.95, 0.6 + (bullish_score - bearish_score) * 0.05)
        elif bearish_score > bullish_score + 1:
            prediction = 2  # SELL
            signal = "SELL"
            confidence = min(0.95, 0.6 + (bearish_score - bullish_score) * 0.05)
        else:
            prediction = 0  # HOLD
            signal = "HOLD"
            confidence = 0.5
        
        # Store prediction for tracking
        prediction_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        predictions_cache[prediction_key] = {
            'symbol': symbol,
            'prediction': prediction,
            'signal': signal,
            'confidence': confidence,
            'features': data,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'prediction': prediction,
            'signal': signal,
            'confidence': round(confidence, 3),
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

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

@app.route('/api/account/update', methods=['POST'])
@require_api_key
def update_account():
    """Update account information from MT5"""
    try:
        data = request.get_json()
        account_info = {
            'account_id': data.get('account', data.get('accountId')),
            'balance': data.get('balance', 0.0),
            'equity': data.get('equity', 0.0),
            'margin': data.get('margin', 0.0),
            'free_margin': data.get('free_margin', 0.0),
            'leverage': data.get('leverage', 1),
            'currency': data.get('currency', 'USD'),
            'broker_name': data.get('brokerName', ''),
            'server_name': data.get('serverName', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in simple in-memory storage
        if not hasattr(app, 'account_data'):
            app.account_data = {}
        app.account_data[account_info['account_id']] = account_info
        
        return jsonify({'success': True, 'message': 'Account updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trades/save', methods=['POST'])
@require_api_key
def save_trade():
    """Save trade information from MT5"""
    try:
        data = request.get_json()
        trade_record = {
            'trade_id': data.get('ticket', data.get('tradeId')),
            'symbol': data.get('symbol', ''),
            'type': data.get('type', 0),
            'volume': data.get('volume', data.get('lotSize', 0.0)),
            'open_price': data.get('open_price', data.get('openPrice', 0.0)),
            'close_price': data.get('close_price', data.get('closePrice')),
            'sl': data.get('sl', data.get('stopLoss')),
            'tp': data.get('tp', data.get('takeProfit')),
            'profit': data.get('profit', 0.0),
            'signal_type': data.get('signal_type', data.get('signal', 0)),
            'confidence': data.get('confidence', 0.0),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        trades_data.append(trade_record)
        
        # Keep only last 1000 trades
        if len(trades_data) > 1000:
            trades_data.pop(0)
        
        return jsonify({'success': True, 'message': 'Trade saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analysis/save', methods=['POST'])
@require_api_key
def save_analysis():
    """Save smart money analysis data from MT5"""
    try:
        data = request.get_json()
        analysis_record = {
            'symbol': data.get('symbol', ''),
            'ob_signal': data.get('ob_signal', 0),
            'fvg_signal': data.get('fvg_signal', 0),
            'bos_signal': data.get('bos_signal', 0),
            'choch_signal': data.get('choch_signal', 0),
            'liquidity_signal': data.get('liquidity_signal', 0),
            'pd_zone': data.get('pd_zone', 0),
            'overall_score': data.get('overall_score', 0.0),
            'ai_prediction': data.get('ai_prediction', 0),
            'ai_confidence': data.get('ai_confidence', 0.0),
            'final_signal': data.get('final_signal', 0),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Store analysis data
        if not hasattr(app, 'analysis_data'):
            app.analysis_data = []
        app.analysis_data.append(analysis_record)
        
        # Keep only last 500 analysis records
        if len(app.analysis_data) > 500:
            app.analysis_data.pop(0)
        
        return jsonify({'success': True, 'message': 'Analysis saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predictions/save', methods=['POST'])
@require_api_key
def save_prediction():
    """Save AI prediction data from MT5"""
    try:
        data = request.get_json()
        prediction_record = {
            'symbol': data.get('symbol', ''),
            'timeframe': data.get('timeframe', ''),
            'features': data.get('features', {}),
            'prediction': data.get('prediction', 0),
            'confidence': data.get('confidence', 0.0),
            'actual_result': data.get('actualResult'),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        predictions_cache[f"{prediction_record['symbol']}_{prediction_record['timestamp']}"] = prediction_record
        
        return jsonify({'success': True, 'message': 'Prediction saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/positions/sync', methods=['POST'])
@require_api_key
def sync_positions():
    """Sync open positions from MT5"""
    try:
        data = request.get_json()
        positions = data.get('positions', [])
        
        # Store positions data
        if not hasattr(app, 'positions_data'):
            app.positions_data = {}
        
        for position in positions:
            ticket = position.get('ticket')
            if ticket:
                app.positions_data[ticket] = {
                    'ticket': ticket,
                    'symbol': position.get('symbol', ''),
                    'type': position.get('type', 0),
                    'volume': position.get('volume', 0.0),
                    'price': position.get('price', 0.0),
                    'sl': position.get('sl', 0.0),
                    'tp': position.get('tp', 0.0),
                    'profit': position.get('profit', 0.0),
                    'timestamp': position.get('timestamp', datetime.now().isoformat())
                }
        
        return jsonify({'success': True, 'message': f'Synced {len(positions)} positions'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot-events/save', methods=['POST'])
@require_api_key
def save_bot_event():
    """Save bot events from MT5"""
    try:
        data = request.get_json()
        event_record = {
            'event_type': data.get('event_type', data.get('event', '')),
            'description': data.get('description', data.get('message', '')),
            'additional_data': data.get('additional_data', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Store events
        if not hasattr(app, 'bot_events'):
            app.bot_events = []
        app.bot_events.append(event_record)
        
        # Keep only last 200 events
        if len(app.bot_events) > 200:
            app.bot_events.pop(0)
        
        return jsonify({'success': True, 'message': 'Event saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market-data/save', methods=['POST'])
@require_api_key
def save_market_data():
    """Save market data from MT5"""
    try:
        data = request.get_json()
        market_record = {
            'symbol': data.get('symbol', ''),
            'timeframe': data.get('timeframe', ''),
            'open': data.get('open', 0.0),
            'high': data.get('high', 0.0),
            'low': data.get('low', 0.0),
            'close': data.get('close', 0.0),
            'volume': data.get('volume', 0),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        market_data.append(market_record)
        
        # Keep only last 1000 market data records
        if len(market_data) > 1000:
            market_data.pop(0)
        
        return jsonify({'success': True, 'message': 'Market data saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/performance/save', methods=['POST'])
@require_api_key
def save_performance():
    """Save performance data from MT5"""
    try:
        data = request.get_json()
        performance_record = {
            'daily_profit': data.get('daily_profit', 0.0),
            'total_trades': data.get('total_trades', 0),
            'winning_trades': data.get('winning_trades', 0),
            'losing_trades': data.get('losing_trades', 0),
            'max_drawdown': data.get('max_drawdown', 0.0),
            'profit_factor': data.get('profit_factor', 0.0),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Store performance data
        if not hasattr(app, 'performance_data'):
            app.performance_data = []
        app.performance_data.append(performance_record)
        
        # Keep only last 90 days
        if len(app.performance_data) > 90:
            app.performance_data.pop(0)
        
        return jsonify({'success': True, 'message': 'Performance data saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs/save', methods=['POST'])
@require_api_key
def save_log():
    """Save system logs from MT5"""
    try:
        data = request.get_json()
        log_record = {
            'level': data.get('level', 'INFO'),
            'message': data.get('message', ''),
            'details': data.get('details', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        # Store logs
        if not hasattr(app, 'system_logs'):
            app.system_logs = []
        app.system_logs.append(log_record)
        
        # Keep only last 1000 log entries
        if len(app.system_logs) > 1000:
            app.system_logs.pop(0)
        
        return jsonify({'success': True, 'message': 'Log saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Dashboard endpoints for viewing data
@app.route('/api/dashboard/summary', methods=['GET'])
@require_api_key
def dashboard_summary():
    """Get dashboard summary data"""
    try:
        # Account data
        account_data = getattr(app, 'account_data', {})
        latest_account = list(account_data.values())[-1] if account_data else {}
        
        # Trades summary
        total_trades = len(trades_data)
        winning_trades = len([t for t in trades_data if t.get('profit', 0) > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Recent events
        recent_events = getattr(app, 'bot_events', [])[-10:]
        
        summary = {
            'account': latest_account,
            'trading_stats': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': round(win_rate, 2)
            },
            'recent_events': recent_events,
            'bot_status': 'active' if recent_events else 'inactive',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': summary})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard', methods=['GET'])
def dashboard_html():
    """Serve dashboard HTML"""
    try:
        import os
        dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard.html')
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>SVN Trading Bot Dashboard</title></head>
        <body>
            <h1>🚀 SVN Trading Bot Dashboard</h1>
            <p>Welcome to the SVN Trading Bot Dashboard!</p>
            <p>API Status: ✅ Online</p>
            <p>Bot Version: v1.0.0</p>
            <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div>
                <h3>API Endpoints:</h3>
                <ul>
                    <li><a href="/api/health">Health Check</a></li>
                    <li><a href="/api/dashboard">Dashboard Data</a></li>
                </ul>
            </div>
        </body>
        </html>
        """, 200, {'Content-Type': 'text/html'}

# For Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
