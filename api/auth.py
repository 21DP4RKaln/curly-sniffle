import os
import jwt
import smtplib
import secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask import Flask, request, jsonify, render_template_string

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'development-secret-key-please-change-in-production')
ADMIN_EMAIL = os.environ.get('ALLOWED_EMAILS', 'sitvain12@gmail.com').lower()

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
    import sqlite3
    conn = sqlite3.connect('svnbot.db')
    conn.row_factory = sqlite3.Row
    return conn

# JWT helper functions
def generate_token(email):
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['email']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Auth decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            token = token.replace('Bearer ', '')
            email = verify_token(token)
            if email:
                return f(*args, **kwargs)
        return jsonify({'error': 'Nav autorizācijas'}), 401
    return decorated_function
