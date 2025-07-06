#!/usr/bin/env python3
"""
AI Service for SVN Trading Bot
Handles AI predictions and machine learning operations
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIPredictor:
    """AI Prediction service for trading signals"""
    
    def __init__(self):
        self.model_version = "1.0.0"
        self.confidence_threshold = 0.7
        self.feature_weights = {
            'rsi': 0.2,
            'macd': 0.25,
            'bollinger': 0.15,
            'volume': 0.1,
            'support_resistance': 0.15,
            'trend': 0.15
        }
        
    def predict_signal(self, symbol: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal prediction"""
        try:
            # Extract and normalize features
            normalized_features = self._normalize_features(features)
            
            # Calculate prediction
            signal_score = self._calculate_signal_score(normalized_features)
            
            # Determine signal direction
            if signal_score > 0.7:
                signal = 1  # Buy signal
                confidence = min(signal_score, 0.95)
            elif signal_score < -0.7:
                signal = -1  # Sell signal
                confidence = min(abs(signal_score), 0.95)
            else:
                signal = 0  # No clear signal
                confidence = 0.5
            
            # Add market context
            market_context = self._analyze_market_context(symbol, features)
            
            # Adjust confidence based on market conditions
            final_confidence = self._adjust_confidence(confidence, market_context)
            
            return {
                'signal': signal,
                'confidence': final_confidence,
                'signal_strength': abs(signal_score),
                'market_context': market_context,
                'features_used': list(normalized_features.keys()),
                'timestamp': datetime.now().isoformat(),
                'model_version': self.model_version
            }
            
        except Exception as e:
            logger.error(f"Error in predict_signal: {e}")
            return {
                'signal': 0,
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _normalize_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Normalize input features"""
        normalized = {}
        
        try:
            # RSI normalization (0-100 to -1 to 1)
            if 'rsi' in features:
                rsi = float(features['rsi'])
                normalized['rsi'] = (rsi - 50) / 50
            
            # MACD normalization
            if 'macd' in features:
                macd = float(features['macd'])
                normalized['macd'] = max(-1, min(1, macd / 0.001))  # Normalize to [-1, 1]
            
            # MACD Signal
            if 'macd_signal' in features:
                macd_signal = float(features['macd_signal'])
                normalized['macd_signal'] = max(-1, min(1, macd_signal / 0.001))
            
            # Bollinger Bands
            if 'bb_upper' in features and 'bb_lower' in features and 'close' in features:
                bb_upper = float(features['bb_upper'])
                bb_lower = float(features['bb_lower'])
                close = float(features['close'])
                bb_position = (close - bb_lower) / (bb_upper - bb_lower)
                normalized['bollinger'] = (bb_position - 0.5) * 2  # Convert to [-1, 1]
            
            # Volume (relative to average)
            if 'volume' in features and 'volume_avg' in features:
                volume = float(features['volume'])
                volume_avg = float(features['volume_avg'])
                if volume_avg > 0:
                    normalized['volume'] = min(2, volume / volume_avg) - 1  # Convert to [-1, 1]
            
            # Support/Resistance levels
            if 'support' in features and 'resistance' in features and 'close' in features:
                support = float(features['support'])
                resistance = float(features['resistance'])
                close = float(features['close'])
                if resistance > support:
                    sr_position = (close - support) / (resistance - support)
                    normalized['support_resistance'] = (sr_position - 0.5) * 2
            
            # Trend strength
            if 'trend_strength' in features:
                trend = float(features['trend_strength'])
                normalized['trend'] = max(-1, min(1, trend))
            
            # Moving averages
            if 'ma_fast' in features and 'ma_slow' in features:
                ma_fast = float(features['ma_fast'])
                ma_slow = float(features['ma_slow'])
                if ma_slow > 0:
                    normalized['ma_cross'] = (ma_fast - ma_slow) / ma_slow
            
        except Exception as e:
            logger.error(f"Error normalizing features: {e}")
        
        return normalized
    
    def _calculate_signal_score(self, features: Dict[str, float]) -> float:
        """Calculate weighted signal score"""
        score = 0.0
        total_weight = 0.0
        
        for feature, value in features.items():
            if feature in self.feature_weights:
                weight = self.feature_weights[feature]
                score += value * weight
                total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            score = score / total_weight
        
        return score
    
    def _analyze_market_context(self, symbol: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market context for better predictions"""
        context = {
            'volatility': 'medium',
            'trend': 'neutral',
            'market_phase': 'consolidation',
            'risk_level': 'medium'
        }
        
        try:
            # Volatility analysis
            if 'atr' in features:
                atr = float(features['atr'])
                if atr > 0.002:
                    context['volatility'] = 'high'
                elif atr < 0.001:
                    context['volatility'] = 'low'
            
            # Trend analysis
            if 'trend_strength' in features:
                trend = float(features['trend_strength'])
                if trend > 0.5:
                    context['trend'] = 'bullish'
                elif trend < -0.5:
                    context['trend'] = 'bearish'
            
            # Market phase
            if 'rsi' in features:
                rsi = float(features['rsi'])
                if rsi > 70:
                    context['market_phase'] = 'overbought'
                elif rsi < 30:
                    context['market_phase'] = 'oversold'
            
            # Risk assessment
            volatility = context['volatility']
            if volatility == 'high':
                context['risk_level'] = 'high'
            elif volatility == 'low':
                context['risk_level'] = 'low'
            
        except Exception as e:
            logger.error(f"Error analyzing market context: {e}")
        
        return context
    
    def _adjust_confidence(self, base_confidence: float, market_context: Dict[str, Any]) -> float:
        """Adjust confidence based on market conditions"""
        adjusted_confidence = base_confidence
        
        # Reduce confidence in high volatility
        if market_context.get('volatility') == 'high':
            adjusted_confidence *= 0.8
        
        # Increase confidence in clear trends
        if market_context.get('trend') in ['bullish', 'bearish']:
            adjusted_confidence *= 1.1
        
        # Reduce confidence in consolidation
        if market_context.get('market_phase') == 'consolidation':
            adjusted_confidence *= 0.9
        
        return max(0.0, min(1.0, adjusted_confidence))
    
    def update_model(self, feedback_data: List[Dict[str, Any]]) -> bool:
        """Update model based on feedback"""
        try:
            # Simple model update based on feedback
            correct_predictions = 0
            total_predictions = len(feedback_data)
            
            for feedback in feedback_data:
                predicted_signal = feedback.get('predicted_signal', 0)
                actual_result = feedback.get('actual_result', 0)
                
                # Check if prediction was correct
                if (predicted_signal > 0 and actual_result > 0) or \
                   (predicted_signal < 0 and actual_result < 0) or \
                   (predicted_signal == 0 and abs(actual_result) < 0.1):
                    correct_predictions += 1
            
            # Calculate accuracy
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            # Adjust confidence threshold based on accuracy
            if accuracy > 0.8:
                self.confidence_threshold = max(0.6, self.confidence_threshold - 0.05)
            elif accuracy < 0.6:
                self.confidence_threshold = min(0.8, self.confidence_threshold + 0.05)
            
            logger.info(f"Model updated. Accuracy: {accuracy:.2f}, New threshold: {self.confidence_threshold:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            return False
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            'model_version': self.model_version,
            'confidence_threshold': self.confidence_threshold,
            'feature_weights': self.feature_weights,
            'supported_features': list(self.feature_weights.keys()),
            'last_updated': datetime.now().isoformat()
        }

class SmartMoneyAnalyzer:
    """Smart Money Concepts analyzer"""
    
    def __init__(self):
        self.lookback_period = 50
        
    def analyze_order_blocks(self, price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify order blocks in price data"""
        order_blocks = []
        
        try:
            if len(price_data) < self.lookback_period:
                return order_blocks
            
            # Simple order block detection
            for i in range(self.lookback_period, len(price_data)):
                current = price_data[i]
                prev = price_data[i-1]
                
                # Look for strong moves that create order blocks
                if current['close'] > prev['high'] * 1.001:  # Strong bullish move
                    order_blocks.append({
                        'type': 'bullish',
                        'price': prev['high'],
                        'timestamp': current['timestamp'],
                        'strength': 'medium'
                    })
                elif current['close'] < prev['low'] * 0.999:  # Strong bearish move
                    order_blocks.append({
                        'type': 'bearish',
                        'price': prev['low'],
                        'timestamp': current['timestamp'],
                        'strength': 'medium'
                    })
            
        except Exception as e:
            logger.error(f"Error analyzing order blocks: {e}")
        
        return order_blocks
    
    def detect_fair_value_gaps(self, price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect Fair Value Gaps (FVG)"""
        fvgs = []
        
        try:
            if len(price_data) < 3:
                return fvgs
            
            for i in range(2, len(price_data)):
                prev_prev = price_data[i-2]
                prev = price_data[i-1]
                current = price_data[i]
                
                # Bullish FVG
                if prev_prev['high'] < current['low']:
                    fvgs.append({
                        'type': 'bullish',
                        'upper': current['low'],
                        'lower': prev_prev['high'],
                        'timestamp': current['timestamp']
                    })
                
                # Bearish FVG
                if prev_prev['low'] > current['high']:
                    fvgs.append({
                        'type': 'bearish',
                        'upper': prev_prev['low'],
                        'lower': current['high'],
                        'timestamp': current['timestamp']
                    })
            
        except Exception as e:
            logger.error(f"Error detecting FVGs: {e}")
        
        return fvgs
    
    def analyze_liquidity_sweeps(self, price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze liquidity sweeps"""
        sweeps = []
        
        try:
            if len(price_data) < 20:
                return sweeps
            
            # Find recent highs and lows
            recent_highs = []
            recent_lows = []
            
            for i in range(10, len(price_data)-10):
                candle = price_data[i]
                is_high = all(candle['high'] >= price_data[j]['high'] for j in range(i-5, i+6))
                is_low = all(candle['low'] <= price_data[j]['low'] for j in range(i-5, i+6))
                
                if is_high:
                    recent_highs.append({'price': candle['high'], 'index': i})
                if is_low:
                    recent_lows.append({'price': candle['low'], 'index': i})
            
            # Check for liquidity sweeps
            for i in range(len(recent_highs)):
                high_level = recent_highs[i]
                for j in range(high_level['index'] + 1, len(price_data)):
                    if price_data[j]['high'] > high_level['price']:
                        sweeps.append({
                            'type': 'high_sweep',
                            'price': high_level['price'],
                            'swept_at': price_data[j]['timestamp'],
                            'strength': 'medium'
                        })
                        break
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity sweeps: {e}")
        
        return sweeps

# Global AI instances
ai_predictor = AIPredictor()
smart_money_analyzer = SmartMoneyAnalyzer()

def get_ai_prediction(symbol: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI prediction for symbol"""
    return ai_predictor.predict_signal(symbol, features)

def analyze_smart_money(price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze smart money concepts"""
    return {
        'order_blocks': smart_money_analyzer.analyze_order_blocks(price_data),
        'fair_value_gaps': smart_money_analyzer.detect_fair_value_gaps(price_data),
        'liquidity_sweeps': smart_money_analyzer.analyze_liquidity_sweeps(price_data)
    }

def update_ai_model(feedback_data: List[Dict[str, Any]]) -> bool:
    """Update AI model with feedback"""
    return ai_predictor.update_model(feedback_data)

def get_ai_model_info() -> Dict[str, Any]:
    """Get AI model information"""
    return ai_predictor.get_model_stats()
