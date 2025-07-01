#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

def test_platform():
    """Testa MT5 trading bot platformas funkcionalitāti"""
    base_url = "http://localhost:5000"
    
    print("🚀 TESTĒJAM SVN TRADING BOT PLATFORMU")
    print("=" * 50)
    
    # 1. Testa galveno lapu
    print("\n1️⃣ Testējam galveno lapu...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Galvenā lapa darbojas!")
        else:
            print(f"   ❌ Kļūda: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Kļūda: {e}")
    
    # 2. Testa dashboard API (bez autentifikācijas)
    print("\n2️⃣ Testējam dashboard API...")
    try:
        response = requests.get(f"{base_url}/api/dashboard")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Dashboard API darbojas!")
            print(f"   📊 Dati: {json.dumps(data, indent=2, ensure_ascii=False)}")
        elif response.status_code == 401:
            print("   🔒 Nepieciešama autentifikācija")
        else:
            print(f"   ❌ Kļūda: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Kļūda: {e}")
    
    # 3. Testa login API
    print("\n3️⃣ Testējam login API...")
    try:
        login_data = {"email": "sitvain12@gmail.com"}
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Login API darbojas!")
            if 'demo_code' in result:
                print(f"   🔑 Demo kods: {result['demo_code']}")
                
                # Testējam ar kodu
                print("\n4️⃣ Testējam autentifikāciju ar kodu...")
                auth_data = {
                    "email": "sitvain12@gmail.com",
                    "code": result['demo_code']
                }
                auth_response = requests.post(f"{base_url}/api/auth/login", json=auth_data)
                print(f"   Status: {auth_response.status_code}")
                if auth_response.status_code == 200:
                    auth_result = auth_response.json()
                    print("   ✅ Autentifikācija veiksmīga!")
                    token = auth_result.get('token')
                    if token:
                        print(f"   🎫 Token saņemts!")
                        
                        # Testējam dashboard ar token
                        print("\n5️⃣ Testējam dashboard ar autentifikāciju...")
                        headers = {"Authorization": f"Bearer {token}"}
                        dash_response = requests.get(f"{base_url}/api/dashboard", headers=headers)
                        print(f"   Status: {dash_response.status_code}")
                        if dash_response.status_code == 200:
                            dash_data = dash_response.json()
                            print("   ✅ Dashboard ar autentifikāciju darbojas!")
                            print(f"   📈 Kopējie darījumi: {dash_data.get('total_trades', 0)}")
                            print(f"   💰 Kopējā peļņa: {dash_data.get('total_profit', 0)}€")
                            print(f"   📊 Sekmīgie darījumi: {dash_data.get('success_rate', 0)}%")
                        else:
                            print(f"   ❌ Dashboard kļūda: {dash_response.status_code}")
                else:
                    print(f"   ❌ Auth kļūda: {auth_response.status_code}")
        else:
            print(f"   ❌ Login kļūda: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Kļūda: {e}")
    
    # 6. Testa AI prediction API
    print("\n6️⃣ Testējam AI prediction API...")
    try:
        # Simulē MT5 datus
        prediction_data = {
            "symbol": "EURUSD",
            "features": {
                "price": 1.1234,
                "volume": 1000,
                "rsi": 65.5,
                "macd": 0.001,
                "bollinger_upper": 1.1250,
                "bollinger_lower": 1.1220
            }
        }
        
        pred_response = requests.post(f"{base_url}/api/predict", json=prediction_data)
        print(f"   Status: {pred_response.status_code}")
        if pred_response.status_code == 200:
            pred_result = pred_response.json()
            print("   ✅ AI Prediction API darbojas!")
            print(f"   🤖 Signāls: {pred_result.get('signal', 'N/A')}")
            print(f"   📊 Confidence: {pred_result.get('confidence', 0)}%")
        else:
            print(f"   ❌ Prediction kļūda: {pred_response.status_code}")
    except Exception as e:
        print(f"   ❌ Kļūda: {e}")
    
    print(f"\n✅ Testēšana pabeigta!")
    print("🌐 Atveriet pārlūkprogrammā: http://localhost:5000")

if __name__ == "__main__":
    test_platform()
