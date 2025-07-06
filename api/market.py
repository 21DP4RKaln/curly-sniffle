#!/usr/bin/env python3
"""
Market Data API endpoints for SVN Trading Bot
Handles market data collection, analysis, and distribution
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any, Optional

from .auth import authenticate_api_key, verify_token
from .ai_service import get_ai_prediction, analyze_smart_money
from .database import save_market_tick, get_historical_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
market_bp = Blueprint('market', __name__)

# In-memory market data storage (replace with database)
market_data_cache = {}
symbol_subscriptions = set()

@market_bp.route('/api/market/data', methods=['POST'])
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
        
        # Save to database (async)
        save_market_tick(market_tick)
        
        return jsonify({
            'status': 'success',
            'message': 'Market data received',
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': market_tick['received_at']
        })
        
    except Exception as e:
        logger.error(f"Error receiving market data: {e}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/market/analyze', methods=['POST'])
def analyze_market_data():
    """Analyze market data for trading signals"""
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
        
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', 'M15')
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        # Get market data from cache
        cache_key = f"{symbol}_{timeframe}"
        price_data = market_data_cache.get(cache_key, [])
        
        if len(price_data) < 50:
            return jsonify({'error': 'Insufficient market data for analysis'}), 400
        
        # Perform smart money analysis
        smart_money_analysis = analyze_smart_money(price_data)
        
        # Get latest market data for AI prediction
        latest_data = price_data[-1]
        features = latest_data.get('indicators', {})
        
        # Add price action features
        features.update({
            'close': latest_data['close'],
            'volume': latest_data['volume'],
            'spread': latest_data.get('spread', 0),
        })
        
        # Get AI prediction
        ai_prediction = get_ai_prediction(symbol, features)
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'analysis_timestamp': datetime.now().isoformat(),
            'smart_money': smart_money_analysis,
            'ai_prediction': ai_prediction,
            'market_context': {
                'latest_price': latest_data['close'],
                'volume': latest_data['volume'],
                'spread': latest_data.get('spread', 0),
                'data_points': len(price_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing market data: {e}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/market/subscribe', methods=['POST'])
def subscribe_to_symbol():
    """Subscribe to market data for a symbol"""
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
        
        symbols = data.get('symbols', [])
        if not symbols:
            return jsonify({'error': 'Symbols list is required'}), 400
        
        # Add symbols to subscription list
        for symbol in symbols:
            symbol_subscriptions.add(symbol.upper())
        
        return jsonify({
            'status': 'success',
            'message': f'Subscribed to {len(symbols)} symbols',
            'subscribed_symbols': list(symbol_subscriptions)
        })
        
    except Exception as e:
        logger.error(f"Error subscribing to symbols: {e}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/market/history', methods=['GET'])
def get_market_history():
    """Get historical market data"""
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
        
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe', 'M15')
        limit = int(request.args.get('limit', 100))
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        # Get data from cache
        cache_key = f"{symbol}_{timeframe}"
        price_data = market_data_cache.get(cache_key, [])
        
        # Limit data
        if limit > 0:
            price_data = price_data[-limit:]
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'data_points': len(price_data),
            'data': price_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting market history: {e}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/market/status', methods=['GET'])
def get_market_status():
    """Get market data status and statistics"""
    try:
        # Calculate statistics
        total_symbols = len(set(key.split('_')[0] for key in market_data_cache.keys()))
        total_data_points = sum(len(data) for data in market_data_cache.values())
        
        # Get latest data timestamps for each symbol
        latest_data = {}
        for cache_key, data in market_data_cache.items():
            if data:
                symbol = cache_key.split('_')[0]
                latest_timestamp = data[-1]['timestamp']
                if symbol not in latest_data or latest_timestamp > latest_data[symbol]:
                    latest_data[symbol] = latest_timestamp
        
        return jsonify({
            'status': 'active',
            'statistics': {
                'total_symbols': total_symbols,
                'total_data_points': total_data_points,
                'subscribed_symbols': len(symbol_subscriptions),
                'cache_keys': len(market_data_cache)
            },
            'subscribed_symbols': list(symbol_subscriptions),
            'latest_data': latest_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/market/signals', methods=['GET'])
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
        
        # Generate signals for each subscribed symbol
        for symbol in symbol_subscriptions:
            cache_key = f"{symbol}_M15"  # Use M15 timeframe for signals
            price_data = market_data_cache.get(cache_key, [])
            
            if len(price_data) >= 50:
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
        logger.error(f"Error getting trading signals: {e}")
        return jsonify({'error': str(e)}), 500

# Helper functions
def calculate_technical_indicators(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate technical indicators from price data"""
    if len(price_data) < 20:
        return {}
    
    closes = [float(candle['close']) for candle in price_data]
    highs = [float(candle['high']) for candle in price_data]
    lows = [float(candle['low']) for candle in price_data]
    volumes = [int(candle['volume']) for candle in price_data]
    
    indicators = {}
    
    try:
        # Simple Moving Averages
        if len(closes) >= 20:
            indicators['sma_20'] = sum(closes[-20:]) / 20
        if len(closes) >= 50:
            indicators['sma_50'] = sum(closes[-50:]) / 50
        
        # RSI (simplified)
        if len(closes) >= 14:
            gains = []
            losses = []
            for i in range(1, min(15, len(closes))):
                diff = closes[-i] - closes[-i-1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(diff))
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            
            if avg_loss != 0:
                rs = avg_gain / avg_loss
                indicators['rsi'] = 100 - (100 / (1 + rs))
            else:
                indicators['rsi'] = 100
        
        # Support and Resistance (simplified)
        recent_highs = highs[-20:] if len(highs) >= 20 else highs
        recent_lows = lows[-20:] if len(lows) >= 20 else lows
        
        indicators['resistance'] = max(recent_highs)
        indicators['support'] = min(recent_lows)
        
        # Volume average
        if len(volumes) >= 20:
            indicators['volume_avg'] = sum(volumes[-20:]) / 20
        
        # ATR (simplified)
        if len(price_data) >= 14:
            true_ranges = []
            for i in range(1, min(15, len(price_data))):
                current = price_data[-i]
                previous = price_data[-i-1]
                
                tr1 = current['high'] - current['low']
                tr2 = abs(current['high'] - previous['close'])
                tr3 = abs(current['low'] - previous['close'])
                
                true_ranges.append(max(tr1, tr2, tr3))
            
            indicators['atr'] = sum(true_ranges) / len(true_ranges)
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
    
    return indicators

def detect_price_patterns(price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect common price patterns"""
    patterns = []
    
    try:
        if len(price_data) < 10:
            return patterns
        
        # Look for double tops/bottoms (simplified)
        highs = [candle['high'] for candle in price_data[-20:]]
        lows = [candle['low'] for candle in price_data[-20:]]
        
        # Find recent peaks and troughs
        peaks = []
        troughs = []
        
        for i in range(2, len(highs)-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > highs[i-2] and highs[i] > highs[i+2]:
                peaks.append({'index': i, 'price': highs[i]})
            
            if lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < lows[i-2] and lows[i] < lows[i+2]:
                troughs.append({'index': i, 'price': lows[i]})
        
        # Check for double tops
        if len(peaks) >= 2:
            last_peak = peaks[-1]
            second_last_peak = peaks[-2]
            
            if abs(last_peak['price'] - second_last_peak['price']) / second_last_peak['price'] < 0.002:  # Within 0.2%
                patterns.append({
                    'type': 'double_top',
                    'confidence': 0.7,
                    'price_level': (last_peak['price'] + second_last_peak['price']) / 2
                })
        
        # Check for double bottoms
        if len(troughs) >= 2:
            last_trough = troughs[-1]
            second_last_trough = troughs[-2]
            
            if abs(last_trough['price'] - second_last_trough['price']) / second_last_trough['price'] < 0.002:  # Within 0.2%
                patterns.append({
                    'type': 'double_bottom',
                    'confidence': 0.7,
                    'price_level': (last_trough['price'] + second_last_trough['price']) / 2
                })
        
    except Exception as e:
        logger.error(f"Error detecting patterns: {e}")
    
    return patterns
