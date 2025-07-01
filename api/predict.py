import os
import json
import numpy as np
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from auth import require_auth, get_db_connection

app = Flask(__name__)

# Simple AI predictor class
class SimpleAIPredictor:
    def __init__(self):
        self.model_weights = np.random.rand(20, 3)  # 20 features, 3 outputs
        self.learning_rate = 0.01
        self.training_data = []
        
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def predict(self, features):
        """Make prediction based on features"""
        try:
            features = np.array(features)
            if len(features) != 20:
                if len(features) < 20:
                    features = np.pad(features, (0, 20 - len(features)), 'constant')
                else:
                    features = features[:20]
            
            # Neural network forward pass
            output = np.dot(features, self.model_weights)
            probabilities = self.sigmoid(output)
            probabilities = probabilities / np.sum(probabilities)
            
            prediction = np.argmax(probabilities) - 1  # Convert to -1, 0, 1
            confidence = np.max(probabilities)
            
            return {
                'prediction': int(prediction),
                'confidence': float(confidence),
                'probabilities': {
                    'sell': float(probabilities[0]),
                    'hold': float(probabilities[1]),
                    'buy': float(probabilities[2])
                }
            }
            
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return {
                'prediction': 0,
                'confidence': 0.5,
                'probabilities': {'sell': 0.33, 'hold': 0.34, 'buy': 0.33}
            }
    
    def train(self, features, target, result):
        """Train model with result"""
        try:
            features = np.array(features)
            if len(features) != 20:
                if len(features) < 20:
                    features = np.pad(features, (0, 20 - len(features)), 'constant')
                else:
                    features = features[:20]
            
            self.training_data.append({
                'features': features.tolist(),
                'target': target,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            if len(self.training_data) > 10:
                target_vector = np.zeros(3)
                if result > 0:
                    target_vector[target + 1] = 1.0
                else:
                    target_vector[1] = 1.0
                
                prediction = np.dot(features, self.model_weights)
                error = target_vector - self.sigmoid(prediction)
                self.model_weights += self.learning_rate * np.outer(features, error)
                
            return True
            
        except Exception as e:
            logging.error(f"Training error: {e}")
            return False

# Global AI predictor
ai_predictor = SimpleAIPredictor()

@app.route('/api/predict', methods=['POST'])
def predict():
    """AI prediction endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Features required'}), 400
        
        features = data['features']
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Make prediction
        result = ai_predictor.predict(features)
        
        # Store in database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_data (timestamp, user_id, symbol, features, signal, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                data.get('account_id', 'unknown'),
                symbol,
                json.dumps(features),
                result['prediction'],
                result['confidence']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.warning(f"Database storage failed: {e}")
        
        # Response
        signal_names = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
        
        return jsonify({
            'prediction': result['prediction'],
            'signal': signal_names[result['prediction']],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'version': '1.0',
                'training_samples': len(ai_predictor.training_data)
            }
        })
        
    except Exception as e:
        logging.error(f"Prediction endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/training_data', methods=['POST'])
def receive_training_data():
    """Receive training data from MT5"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        features = data.get('features', [])
        signal = data.get('signal', 0)
        result = data.get('result', 0.0)
        
        if not features:
            return jsonify({'error': 'Features required'}), 400
        
        # Train model
        success = ai_predictor.train(features, signal, result)
        
        # Store in database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (timestamp, user_id, symbol, signal, profit, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data.get('timestamp', datetime.now().isoformat()),
                data.get('account_id', 'unknown'),
                data.get('symbol', 'UNKNOWN'),
                'BUY' if signal > 0 else 'SELL' if signal < 0 else 'HOLD',
                result,
                0.75
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.warning(f"Database storage failed: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Training data received',
            'model_updated': success,
            'training_samples': len(ai_predictor.training_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Training data error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model_status', methods=['GET'])
def model_status():
    """AI model status"""
    return jsonify({
        'status': 'operational',
        'model_version': '1.0',
        'training_samples': len(ai_predictor.training_data),
        'last_updated': datetime.now().isoformat(),
        'capabilities': {
            'prediction': True,
            'training': True,
            'feature_count': 20,
            'output_classes': 3
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'SVN Trading Bot AI',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

# Serverless handler
def handler(request):
    with app.app_context():
        return app(request.environ, lambda *args: None)
