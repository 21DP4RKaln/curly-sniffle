#!/usr/bin/env python3
"""
SVN Trading Bot - Test Script
Demonstrē platformas funkcionalitāti
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_platform():
    print("🧪 SVN Trading Bot - Platformas Tests")
    print("="*50)
    
    # Test 1: Health Check
    print("\n1️⃣ Veselības pārbaude...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Serveris darbojas!")
            print(f"📊 Atbilde: {response.json()}")
        else:
            print(f"❌ Serveris neatbild: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Kļūda: {e}")
        return
    
    # Test 2: API Test
    print("\n2️⃣ API tests...")
    try:
        response = requests.get(f"{BASE_URL}/api/test")
        if response.status_code == 200:
            print("✅ API darbojas!")
            data = response.json()
            print(f"📱 Versija: {data.get('version')}")
            print(f"💬 Ziņojums: {data.get('message')}")
        else:
            print(f"❌ API kļūda: {response.status_code}")
    except Exception as e:
        print(f"❌ API kļūda: {e}")
    
    # Test 3: Authentication Flow
    print("\n3️⃣ Autentifikācijas tests...")
    try:
        # Step 1: Request code
        auth_data = {"email": "sitvain12@gmail.com"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=auth_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Koda pieprasīšana veiksmīga!")
            
            if 'demo_code' in result:
                demo_code = result['demo_code']
                print(f"🔑 Demo kods: {demo_code}")
                
                # Step 2: Verify code
                verify_data = {"email": "sitvain12@gmail.com", "code": demo_code}
                auth_response = requests.post(f"{BASE_URL}/api/auth/login", json=verify_data)
                
                if auth_response.status_code == 200:
                    auth_result = auth_response.json()
                    token = auth_result.get('token')
                    print("✅ Autentifikācija veiksmīga!")
                    print(f"🎫 Token saņemts: {token[:30]}...")
                    
                    # Test 4: Protected endpoint
                    print("\n4️⃣ Aizsargātā endpointa tests...")
                    headers = {"Authorization": f"Bearer {token}"}
                    dash_response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
                    
                    if dash_response.status_code == 200:
                        dash_data = dash_response.json()
                        stats = dash_data.get('statistics', {})
                        print("✅ Dashboard pieejams!")
                        print(f"🤖 Aktīvi boti: {stats.get('active_bots', 0)}")
                        print(f"💰 Kopējā peļņa: ${stats.get('total_profit', 0)}")
                        print(f"📈 Darījumi šodien: {stats.get('trades_today', 0)}")
                        print(f"🧠 AI precizitāte: {stats.get('ai_accuracy', 0)}%")
                    else:
                        print(f"❌ Dashboard kļūda: {dash_response.status_code}")
                else:
                    print(f"❌ Koda verifikācija neizdevās: {auth_response.status_code}")
            else:
                print("⚠️ Nav demo koda (ražošanas režīms)")
        else:
            print(f"❌ Koda pieprasīšana neizdevās: {response.status_code}")
    except Exception as e:
        print(f"❌ Autentifikācijas kļūda: {e}")
    
    # Test 5: AI Prediction
    print("\n5️⃣ AI prognožu tests...")
    try:
        prediction_data = {
            "features": [1.2, 0.8, -0.3, 1.1, 0.5],
            "symbol": "EURUSD",
            "account_id": "test_account"
        }
        response = requests.post(f"{BASE_URL}/api/predict", json=prediction_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI prognoze saņemta!")
            print(f"📊 Signāls: {result.get('signal')}")
            print(f"🎯 Uzticamība: {result.get('confidence'):.2%}")
            print(f"📈 Prognoze: {result.get('prediction')}")
        else:
            print(f"❌ AI prognozes kļūda: {response.status_code}")
    except Exception as e:
        print(f"❌ AI kļūda: {e}")
    
    print("\n" + "="*50)
    print("🎉 Tests pabeigts!")
    print("🌐 Atveriet pārlūkprogrammu: http://localhost:5000")
    print("📱 E-pasts: sitvain12@gmail.com")
    print("🔑 Kods tiks parādīts serveris konsolē")

if __name__ == "__main__":
    test_platform()
