import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_EMAIL = "sitvain12@gmail.com"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_login_flow():
    """Test login flow"""
    print("\n🔐 Testing login flow...")
    try:
        # Step 1: Request code
        response = requests.post(f"{BASE_URL}/api/auth/login", 
                               json={"email": TEST_EMAIL})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Code request successful")
            
            # Check if demo code is provided (development mode)
            if 'demo_code' in data:
                code = data['demo_code']
                print(f"📱 Demo code: {code}")
                
                # Step 2: Verify code
                response = requests.post(f"{BASE_URL}/api/auth/login",
                                       json={"email": TEST_EMAIL, "code": code})
                
                if response.status_code == 200:
                    token_data = response.json()
                    if 'token' in token_data:
                        print("✅ Login successful")
                        return token_data['token']
                    else:
                        print("❌ No token received")
                        return None
                else:
                    print(f"❌ Code verification failed: {response.status_code}")
                    return None
            else:
                print("⚠️  No demo code (production mode)")
                return None
        else:
            print(f"❌ Code request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Login flow error: {e}")
        return None

def test_dashboard_api(token):
    """Test dashboard API"""
    print("\n📊 Testing dashboard API...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Dashboard API working")
            print(f"   Active bots: {data['statistics']['active_bots']}")
            print(f"   Total profit: ${data['statistics']['total_profit']}")
            return True
        else:
            print(f"❌ Dashboard API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard API error: {e}")
        return False

def test_users_api(token):
    """Test users API"""
    print("\n👥 Testing users API...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Users API working")
            print(f"   Total users: {data['stats']['total']}")
            return True
        else:
            print(f"❌ Users API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Users API error: {e}")
        return False

def test_predict_api():
    """Test prediction API"""
    print("\n🤖 Testing AI prediction API...")
    try:
        # Sample features (20 values)
        features = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   0.11, 0.22, 0.33, 0.44, 0.55, 0.66, 0.77, 0.88, 0.99, 0.5]
        
        response = requests.post(f"{BASE_URL}/api/predict", 
                               json={
                                   "features": features,
                                   "symbol": "EURUSD",
                                   "account_id": "test_123"
                               })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Prediction API working")
            print(f"   Signal: {data['signal']}")
            print(f"   Confidence: {data['confidence']:.2f}")
            print(f"   Probabilities: {data['probabilities']}")
            return True
        else:
            print(f"❌ Prediction API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Prediction API error: {e}")
        return False

def test_training_data_api():
    """Test training data API"""
    print("\n📚 Testing training data API...")
    try:
        features = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                   0.11, 0.22, 0.33, 0.44, 0.55, 0.66, 0.77, 0.88, 0.99, 0.5]
        
        response = requests.post(f"{BASE_URL}/api/training_data",
                               json={
                                   "features": features,
                                   "signal": 1,  # BUY
                                   "result": 50.0,  # Profit
                                   "symbol": "EURUSD",
                                   "account_id": "test_123"
                               })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Training data API working")
            print(f"   Status: {data['status']}")
            print(f"   Training samples: {data['training_samples']}")
            return True
        else:
            print(f"❌ Training data API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Training data API error: {e}")
        return False

def test_mt5_data_flow():
    """Test MT5 data reception"""
    print("\n🔄 Testing MT5 data flow...")
    try:
        mt5_data = {
            "account_id": "123456",
            "symbol": "EURUSD",
            "balance": 1000.00,
            "equity": 1050.00,
            "daily_profit": 50.00,
            "total_trades": 10,
            "market_data": [
                {
                    "time": "2025-07-01T12:00:00",
                    "open": 1.0850,
                    "high": 1.0870,
                    "low": 1.0840,
                    "close": 1.0860,
                    "volume": 1000,
                    "indicators": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                                 0.11, 0.22, 0.33, 0.44, 0.55, 0.66, 0.77, 0.88, 0.99, 0.5],
                    "signal": 1
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/data", json=mt5_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ MT5 data reception working")
            print(f"   Status: {data['status']}")
            return True
        else:
            print(f"❌ MT5 data reception failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ MT5 data flow error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 SVN Trading Bot - API Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Basic health check failed. Is the server running?")
        print("   Start server with: scripts\\start_local.bat")
        return
    
    # Test 2: Login flow
    token = test_login_flow()
    
    # Test 3-4: Authenticated endpoints
    if token:
        test_dashboard_api(token)
        test_users_api(token)
    else:
        print("\n⚠️  Skipping authenticated tests (no token)")
    
    # Test 5-6: AI endpoints
    test_predict_api()
    test_training_data_api()
    
    # Test 7: MT5 data flow
    test_mt5_data_flow()
    
    print("\n" + "=" * 50)
    print("🎯 Test suite completed!")
    print("\n📝 Next steps:")
    print("   1. Configure .env.local with your email settings")
    print("   2. Test login with real email")
    print("   3. Configure MT5 bot with server URL")
    print("   4. Deploy to Vercel: scripts\\deploy_vercel.bat")
    print("\n🌐 Access dashboard: http://localhost:5000/dashboard")

if __name__ == "__main__":
    main()
