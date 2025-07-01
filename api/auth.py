import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
import secrets
import jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# Allowed emails - only one email from environment
ADMIN_EMAIL = os.environ.get('ALLOWED_EMAILS', 'sitvain12@gmail.com').split(',')[0].strip()

# Email configuration
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

# Simple in-memory auth codes for demo (in production use Redis/database)
auth_codes = {}

def send_email_code(email, code):
    """Send authentication code via email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER if SMTP_USER else 'noreply@svnbot.com'
        msg['To'] = email
        msg['Subject'] = "SVN Trading Bot - Kods autentifikācijai"
        
        # Email body in Latvian
        body = f"""
Sveiki!

Jūsu autentifikācijas kods SVN Trading Bot sistēmai:

{code}

Šis kods derīgs 10 minūtes.

Ja jūs nepieprasījāt šo kodu, ignorējiet šo e-pastu.

Ar cieņu,
SVN Trading Bot komanda
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Send email
        if SMTP_USER and SMTP_PASSWORD:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_USER, email, text)
            server.quit()
            return True
        else:
            # For development - log the code
            print(f"Development mode - Auth code for {email}: {code}")
            return False
            
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

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
        # Check if email is authorized
        if email.strip().lower() != ADMIN_EMAIL.lower():
            return jsonify({'error': 'E-pasts nav autorizēts'}), 403
        
        # Generate and send code
        auth_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        auth_codes[email] = {
            'code': auth_code,
            'timestamp': datetime.now(),
            'attempts': 0
        }
        
        # Send email code
        email_sent = send_email_code(email, auth_code)
        
        # Return response
        response = {
            'message': 'Kods nosūtīts uz e-pastu'
        }
        
        # For development, include code if email sending failed
        if not email_sent:
            response['demo_code'] = auth_code
            
        return jsonify(response)
    
    elif email and code:
        # Verify code
        if email not in auth_codes:
            return jsonify({'error': 'Kods nav atrasts'}), 400
        
        stored_data = auth_codes[email]
        
        # Check if code expired
        if datetime.now() - stored_data['timestamp'] > timedelta(minutes=10):
            del auth_codes[email]
            return jsonify({'error': 'Kods ir beidzies'}), 400
        
        # Check attempts limit
        if stored_data['attempts'] >= 3:
            del auth_codes[email]
            return jsonify({'error': 'Pārāk daudz mēģinājumu'}), 400
        
        # Verify code
        if code == stored_data['code']:
            del auth_codes[email]
            token = generate_token(email)
            return jsonify({
                'token': token,
                'message': 'Pieteikšanās veiksmīga'
            })
        else:
            auth_codes[email]['attempts'] += 1
            return jsonify({'error': 'Nepareizs kods'}), 400
    
    return jsonify({'error': 'Nepieciešams e-pasts un kods'}), 400

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
