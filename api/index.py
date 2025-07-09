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
# Force simple auth for now to avoid database connection issues
try:
    from .auth_simple import send_login_code, verify_login_code
    USE_DATABASE_AUTH = False
    print("Using simple authentication (no database)")
    
    # Create placeholder functions for missing auth functions
    def authenticate_api_key(api_key):
        return {'success': False, 'error': 'API key authentication not available in simple mode'}
    
    def verify_token(token):
        return {'success': False, 'error': 'Token verification not available in simple mode'}
    
    class MockDBAuthManager:
        def __init__(self):
            pass
        async def connect(self):
            pass
        async def disconnect(self):
            pass
    
    db_auth_manager = MockDBAuthManager()
    
except ImportError:
    try:
        # For standalone execution
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from auth_simple import send_login_code, verify_login_code
        USE_DATABASE_AUTH = False
        print("Using simple authentication (no database)")
        
        # Create placeholder functions for missing auth functions
        def authenticate_api_key(api_key):
            return {'success': False, 'error': 'API key authentication not available in simple mode'}
        
        def verify_token(token):
            return {'success': False, 'error': 'Token verification not available in simple mode'}
        
        class MockDBAuthManager:
            def __init__(self):
                pass
            async def connect(self):
                pass
            async def disconnect(self):
                pass
        
        db_auth_manager = MockDBAuthManager()
        
    except ImportError:
        print("Could not import authentication modules")

# Import other modules
try:
    from .ai_service import get_ai_prediction, analyze_smart_money, update_ai_model, get_ai_model_info
    from .database import save_trade_data, save_ai_prediction, update_account_data, get_performance_statistics
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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

def authenticate_request():
    """Helper function to authenticate requests"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        
        async def verify_token_async():
            await db_auth_manager.connect()
            try:
                return await verify_token(token)
            finally:
                await db_auth_manager.disconnect()
                
        return asyncio.run(verify_token_async())
    else:
        api_key = request.headers.get('X-API-Key', '')
        
        async def verify_api_key_async():
            await db_auth_manager.connect()
            try:
                return await authenticate_api_key(api_key)
            finally:
                await db_auth_manager.disconnect()
                
        return asyncio.run(verify_api_key_async())

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': API_VERSION,
        'timestamp': datetime.now().isoformat(),
        'database_status': 'connected' if DATABASE_URL else 'not_configured'
    })

@app.route('/api/auth/send-code', methods=['POST'])
def send_auth_code():
    """Send authentication code to email"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email')
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
          # Run async function in event loop
        if USE_DATABASE_AUTH:
            async def run_send_code():
                await db_auth_manager.connect()
                try:
                    result = await send_login_code(email)
                    return result
                finally:
                    await db_auth_manager.disconnect()
            
            result = asyncio.run(run_send_code())
        else:
            # Use simple auth (no database)
            result = send_login_code(email)
        
        return jsonify(result)
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/verify-code', methods=['POST'])
def verify_auth_code():
    """Verify authentication code and login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'success': False, 'error': 'Email and code are required'}), 400
          # Run async function in event loop
        if USE_DATABASE_AUTH:
            async def run_verify_code():
                await db_auth_manager.connect()
                try:
                    result = await verify_login_code(email, code)
                    return result
                finally:
                    await db_auth_manager.disconnect()
            
            result = asyncio.run(run_verify_code())
        else:
            # Use simple auth (no database)
            result = verify_login_code(email, code)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def ai_predict():
    """AI prediction endpoint for trading signals"""
    try:
        # Authenticate request
        auth_result = authenticate_request()
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['symbol', 'timeframe', 'features'
        ]
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
        asyncio.run(save_ai_prediction({
            'prediction_id': prediction_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'features': features,
            'prediction': prediction['signal'],
            'confidence': prediction['confidence']
        }))
        
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
        asyncio.run(save_trade_data(trade_data))
        
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
        asyncio.run(update_account_data(data))
        
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
        auth_result = authenticate_request()
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        user = auth_result['user']
        
        # Get user's performance data
        performance_data = asyncio.run(get_performance_statistics(user['id']))
        
        # Return dashboard data
        return jsonify({
            'user': user,
            'statistics': statistics,
            'market_data': market_data,
            'performance': performance_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    """Get all users (admin only)"""
    try:
        # Authenticate request
        auth_result = authenticate_request()
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        user = auth_result['user']
        
        # Check if user is admin (for now, check if email is admin)
        if user['email'] != 'admin@svn.com':
            return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
        
        # Get all users from database
        async def get_users():
            await db_auth_manager.connect()
            try:
                users = await db_auth_manager.db.user.find_many()
                return [
                    {
                        'id': u.id,
                        'email': u.email,
                        'nickname': u.nickname,
                        'role': u.role.value,
                        'isActive': u.isActive,
                        'createdAt': u.createdAt.isoformat(),
                        'lastLogin': u.lastLogin.isoformat() if u.lastLogin else None,
                        'loginCount': u.loginCount
                    }
                    for u in users
                ]
            finally:
                await db_auth_manager.disconnect()
        
        users = asyncio.run(get_users())
        
        return jsonify({
            'users': users,
            'total': len(users)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    """Update user role (admin only)"""
    try:
        # Authenticate request
        auth_result = authenticate_request()
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        user = auth_result['user']
        
        # Check if user is admin
        if user['email'] != 'admin@svn.com':
            return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
        
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({'error': 'Role is required'}), 400
        
        role = data['role']
        if role not in ['REG_USER', 'LID_USER']:
            return jsonify({'error': 'Invalid role. Must be REG_USER or LID_USER'}), 400
          # Update user role
        async def update_role():
            await db_auth_manager.connect()
            try:
                updated_user = await db_auth_manager.update_user_role(user_id, role)
                return updated_user
            finally:
                await db_auth_manager.disconnect()
        
        result = asyncio.run(update_role())
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'User role updated successfully',
                'user': result['user']
            })
        else:
            return jsonify({'error': result['error']}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    try:
        # Authenticate request
        auth_result = authenticate_request()
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        user = auth_result['user']
        
        # Get user's API keys
        async def get_user_profile():
            await db_auth_manager.connect()
            try:
                api_keys = await db_auth_manager.db.apikey.find_many(
                    where={'userId': user['id'], 'isActive': True}
                )
                
                return {
                    'user': user,
                    'api_keys': [
                        {
                            'id': k.id,
                            'name': k.name,
                            'key': k.key,
                            'createdAt': k.createdAt.isoformat(),
                            'lastUsed': k.lastUsed.isoformat() if k.lastUsed else None
                        }
                        for k in api_keys
                    ]
                }
            finally:
                await db_auth_manager.disconnect()
        
        profile = asyncio.run(get_user_profile())
        
        return jsonify(profile)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=True)
