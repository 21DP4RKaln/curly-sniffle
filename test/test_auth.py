#!/usr/bin/env python3
import requests
import json

# Test authentication flow
print("🔐 TESTĒJAM AUTENTIFIKĀCIJU")
print("=" * 30)

# Step 1: Request code
login_response = requests.post('http://localhost:5000/api/auth/login', 
                              json={'email': 'sitvain12@gmail.com'})
print(f"1. Koda pieprasīšana - Status: {login_response.status_code}")

if login_response.status_code == 200:
    login_result = login_response.json()
    demo_code = login_result.get('demo_code')
    print(f"   Demo kods: {demo_code}")
    
    # Step 2: Authenticate with code
    auth_response = requests.post('http://localhost:5000/api/auth/login', 
                                 json={'email': 'sitvain12@gmail.com', 'code': demo_code})
    print(f"2. Autentifikācija - Status: {auth_response.status_code}")
    
    if auth_response.status_code == 200:
        auth_result = auth_response.json()
        token = auth_result.get('token')
        print(f"   ✅ Token saņemts: {token[:30]}..." if token else "   ❌ Nav token")
        
        if token:
            # Step 3: Test dashboard with authentication
            headers = {'Authorization': f'Bearer {token}'}
            dash_response = requests.get('http://localhost:5000/api/dashboard', headers=headers)
            print(f"3. Dashboard ar auth - Status: {dash_response.status_code}")
            
            if dash_response.status_code == 200:
                dash_data = dash_response.json()
                print(f"   ✅ Dashboard dati:")
                print(f"   📊 Kopējie darījumi: {dash_data.get('total_trades', 0)}")
                print(f"   💰 Kopējā peļņa: {dash_data.get('total_profit', 0)}€")
                print(f"   📈 Veiksmīgie: {dash_data.get('success_rate', 0)}%")
            else:
                print(f"   ❌ Dashboard kļūda: {dash_response.text}")
    else:
        print(f"   ❌ Auth kļūda: {auth_response.text}")
else:
    print(f"   ❌ Login kļūda: {login_response.text}")

print("\n✅ Autentifikācijas tests pabeigts!")
