import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
import secrets
import jwt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Vercel serverless function imports
from flask import Flask, request, jsonify, session
from flask_cors import CORS

# Initialize Flask app for serverless
app = Flask(__name__)
CORS(app)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'temp-key-for-development')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///svnbot.db')

# Allowed emails
ALLOWED_EMAILS = os.environ.get('ALLOWED_EMAILS', '').split(',')
if not ALLOWED_EMAILS[0]:
    ALLOWED_EMAILS = ['sitvain12@gmail.com', 'sitvain89@gmail.com']

# Simple in-memory auth codes for demo (in production use Redis/database)
auth_codes = {}

# Database helper
def get_db_connection():
    if DATABASE_URL.startswith('postgresql'):
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        # SQLite fallback
        db_path = DATABASE_URL.replace('sqlite:///', '')
        return sqlite3.connect(db_path)

# JWT helper functions
def generate_token(email):
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload['email']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Auth decorator
def require_auth(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
            email = verify_token(token)
            if not email:
                return jsonify({'error': 'Invalid token'}), 401
            request.user_email = email
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Invalid authorization'}), 401
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    
    if email and not code:
        # Generate and send code
        if email not in ALLOWED_EMAILS:
            return jsonify({'error': 'Email not authorized'}), 403
        
        auth_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        auth_codes[email] = {
            'code': auth_code,
            'timestamp': datetime.now(),
            'attempts': 0
        }
        
        # In production, send email here
        # For demo, return code (REMOVE IN PRODUCTION!)
        return jsonify({
            'message': 'Code sent to email',
            'demo_code': auth_code  # REMOVE IN PRODUCTION!
        })
    
    elif email and code:
        # Verify code
        if email not in auth_codes:
            return jsonify({'error': 'No code found'}), 400
        
        stored_data = auth_codes[email]
        
        if datetime.now() - stored_data['timestamp'] > timedelta(minutes=10):
            del auth_codes[email]
            return jsonify({'error': 'Code expired'}), 400
        
        if stored_data['attempts'] >= 3:
            del auth_codes[email]
            return jsonify({'error': 'Too many attempts'}), 400
        
        if code == stored_data['code']:
            del auth_codes[email]
            token = generate_token(email)
            return jsonify({
                'token': token,
                'message': 'Login successful'
            })
        else:
            auth_codes[email]['attempts'] += 1
            return jsonify({'error': 'Invalid code'}), 400
    
    return jsonify({'error': 'Email and code required'}), 400

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
