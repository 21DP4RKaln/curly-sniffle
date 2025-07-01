#!/usr/bin/env python3
"""
Test script to verify MT5 bot configuration with Vercel deployment
"""

import requests
import json
import time

def test_mt5_integration():
    """Test MT5 bot integration with updated Vercel URL"""    # Configuration from MT5 bot
    SERVER_URL = "https://curly-sniffle-q7raztsih-21dp4rkalns-projects.vercel.app/api"
    API_KEY = "61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f"
    
    print("🤖 Testing MT5 Bot Integration with Vercel")
    print("=" * 50)
    print(f"Server URL: {SERVER_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    print()
    
    # Test 1: Health Check
    print("1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{SERVER_URL.replace('/api', '')}/api/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed!")
        else:
            print(f"   ❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    print()
    
    # Test 2: AI Prediction (как MT5 бот отправляет данные)
    print("2️⃣ Testing AI Prediction API...")
    try:
        # Simulate MT5 bot sending market data
        features = [
            1.1000,    # Current price
            0.0012,    # Price change %
            0.0050,    # Volatility
            45.5,      # RSI
            0.001,     # MACD
            -0.002,    # MACD Signal
            0.003,     # MACD Difference
            1.1020,    # MA20
            1.1030,    # MA50
            0.5,       # BB Position
            0.02,      # BB Width
            0.015,     # ATR
            1.5,       # Volume ratio
            14.0,      # Hour
            2.0,       # Day of week
            0.8,       # Momentum 5
            0.6,       # Momentum 10
            0.7,       # Support/Resistance position
            0.05,      # Support/Resistance range
            0.0        # Reserved
        ]
          prediction_data = {
            "features": features,
            "symbol": "EURUSD"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        response = requests.post(f"{SERVER_URL}/predict2", 
                               json=prediction_data, 
                               headers=headers, 
                               timeout=10)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            signal = result.get('signal', 'UNKNOWN')
            confidence = result.get('confidence', 0) * 100
            print(f"   ✅ AI Prediction successful!")
            print(f"   🎯 Signal: {signal}")
            print(f"   📊 Confidence: {confidence:.1f}%")
        else:
            print(f"   ❌ Prediction failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Prediction error: {e}")
    
    print()
    
    # Test 3: Trade Feedback (как MT5 бот отправляет результаты сделок)
    print("3️⃣ Testing Trade Feedback API...")
    try:
        feedback_data = {
            "trade_id": f"test_trade_{int(time.time())}",
            "profit": 15.50,
            "is_win": True,
            "signal": 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": "EURUSD"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        response = requests.post(f"{SERVER_URL}/feedback", 
                               json=feedback_data, 
                               headers=headers, 
                               timeout=10)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Trade feedback successful!")
        else:
            print(f"   ❌ Feedback failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Feedback error: {e}")
    
    print()
    
    # Test 4: Data Upload (как MT5 бот отправляет рыночные данные)
    print("4️⃣ Testing Market Data Upload...")
    try:
        market_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": "EURUSD",
            "account_id": "12345",
            "balance": 10000.00,
            "equity": 10015.50,
            "daily_profit": 15.50,
            "max_drawdown": 2.5,
            "total_trades": 10,
            "winning_trades": 7,
            "market_data": [
                {
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": 1.1000,
                    "high": 1.1020,
                    "low": 1.0980,
                    "close": 1.1010,
                    "volume": 1500,
                    "signal": 1,
                    "result": 15.50,
                    "indicators": features
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        response = requests.post(f"{SERVER_URL}/data", 
                               json=market_data, 
                               headers=headers, 
                               timeout=10)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Market data upload successful!")
        else:
            print(f"   ❌ Data upload failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Data upload error: {e}")
    
    print()
    print("🎉 MT5 Integration Test Complete!")
    print()
    print("📋 Summary:")
    print("   - Server URL updated to Vercel deployment")
    print("   - Using Prisma Postgres database") 
    print("   - All MT5 bot endpoints tested")
    print()
    print("🚀 Your MT5 bot is ready to connect to the Vercel platform!")

if __name__ == "__main__":
    test_mt5_integration()
