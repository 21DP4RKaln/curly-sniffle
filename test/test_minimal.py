#!/usr/bin/env python3
"""
Minimal test for debugging the prediction endpoint
"""

import requests
import json

def minimal_test():
    url = "https://curly-sniffle-q7raztsih-21dp4rkalns-projects.vercel.app/api/predict"
    api_key = "61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f"
    
    # Minimal test data
    data = {
        "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        "symbol": "TEST"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    print("Minimal prediction test...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    minimal_test()
