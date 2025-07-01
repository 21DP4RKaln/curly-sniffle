#!/usr/bin/env python3
"""
Quick test for the prediction endpoint specifically
"""

import requests
import json

def test_prediction():
    SERVER_URL = "https://curly-sniffle-mx7e9n808-21dp4rkalns-projects.vercel.app/api"
    API_KEY = "61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f"
    
    # Test data
    features = [
        1.1025,    # Close price
        1.1020,    # Open price
        1.1030,    # High price
        1.1015,    # Low price
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
    ]
    
    prediction_data = {
        "features": features,
        "symbol": "EURUSD"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    print("Testing prediction endpoint...")
    print(f"Features count: {len(features)}")
    print(f"URL: {SERVER_URL}/predict")
    
    try:
        response = requests.post(f"{SERVER_URL}/predict", 
                               json=prediction_data, 
                               headers=headers, 
                               timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_prediction()
