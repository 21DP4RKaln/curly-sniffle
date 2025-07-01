import os
import sys
import json
import logging
from datetime import datetime
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Try to import ML libraries, fallback to mock predictions
try:
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    HAS_ML = True
except ImportError:
    HAS_ML = False

@app.route('/api/predict', methods=['POST'])
def predict_signal():
    """Provide AI prediction for given features"""
    try:
        data = request.get_json()
        if not data or 'features' not in data:
            return jsonify({'error': 'Features required'}), 400
        
        features = data['features']
        symbol = data.get('symbol', 'EURUSD')
        
        if HAS_ML and len(features) >= 10:
            # Use actual ML prediction (simplified)
            # In production, load trained model from database/storage
            prediction_value = sum(features[:5]) / len(features[:5])
            
            if prediction_value > 0.6:
                probabilities = [0.1, 0.2, 0.7]  # BUY
                prediction = 2
            elif prediction_value < 0.4:
                probabilities = [0.7, 0.2, 0.1]  # SELL
                prediction = 0
            else:
                probabilities = [0.2, 0.6, 0.2]  # HOLD
                prediction = 1
        else:
            # Mock prediction for demo
            rand_val = random.random()
            if rand_val > 0.6:
                probabilities = [0.1, 0.2, 0.7]  # BUY
                prediction = 2
            elif rand_val < 0.4:
                probabilities = [0.7, 0.2, 0.1]  # SELL
                prediction = 0
            else:
                probabilities = [0.2, 0.6, 0.2]  # HOLD
                prediction = 1
        
        confidence = max(probabilities)
        
        return jsonify({
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': {
                'sell': probabilities[0],
                'hold': probabilities[1], 
                'buy': probabilities[2]
            },
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/training_data', methods=['POST'])
def receive_training_data():
    """Receive training data from MT5 clients"""
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Invalid training data'}), 400
        
        # In production, save to database
        # For now, just acknowledge receipt
        logging.info(f"Received training data: {len(data['features'])} features")
        
        return jsonify({
            'status': 'success',
            'message': 'Training data received',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Training data error: {e}")
        return jsonify({'error': str(e)}), 500

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
