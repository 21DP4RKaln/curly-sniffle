#!/usr/bin/env python3
"""
SVN Trading Bot - Local Server
Palaist lokāli bez Vercel ierobežojumiem
"""

import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

# Import the Flask app from index.py
from index import app

if __name__ == '__main__':
    print("🚀 SVN Trading Bot sākas...")
    print("📍 Adrese: http://localhost:5000")
    print("📱 Login: sitvain12@gmail.com")
    print("🔑 Demo režīms - kods tiks parādīts konsolē")
    print("="*50)
    
    # Run the Flask app
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
