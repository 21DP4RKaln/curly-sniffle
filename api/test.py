import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__)
CORS(app)

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'API is working!',
        'environment': 'Vercel',
        'admin_email': os.environ.get('ALLOWED_EMAILS', 'sitvain12@gmail.com')
    })

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
