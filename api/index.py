"""
Enhanced SVN Trading Bot API with Strong Authentication
Only authorized emails and IPs can access the system
"""

import os
import json
import secrets
import jwt
import random
import hashlib
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, make_response, redirect, url_for

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip
    pass

app = Flask(__name__)

# Configuration - ALL from environment variables (Vercel)
SECRET_KEY = os.environ.get('SECRET_KEY')
API_KEY = os.environ.get('MT5_API_KEY')
ACCESS_CODE = os.environ.get('ACCESS_CODE')

# Email configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

# Authorized users and IPs from environment variables
AUTHORIZED_EMAILS_ENV = os.environ.get('ALLOWED_EMAILS')
AUTHORIZED_EMAILS = [email.strip().lower() for email in AUTHORIZED_EMAILS_ENV.split(',') if email.strip()] if AUTHORIZED_EMAILS_ENV else []

# IP whitelist from environment variables
AUTHORIZED_IPS_ENV = os.environ.get('ALLOWED_IPS')
AUTHORIZED_IPS = [ip.strip() for ip in AUTHORIZED_IPS_ENV.split(',') if ip.strip()] if AUTHORIZED_IPS_ENV else []

# Session management
active_sessions = {}
failed_attempts = {}
access_codes = {}  # Store temporary access codes
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME = 3600  # 1 hour

# Simple in-memory storage
trades_data = []
market_data = []
predictions_cache = {}

# Security functions
def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.environ.get('REMOTE_ADDR', '0.0.0.0')

def is_ip_authorized(ip):
    """Check if IP is authorized"""
    return ip in AUTHORIZED_IPS or ip.startswith('192.168.') or ip.startswith('10.') or ip == '127.0.0.1'

def is_email_authorized(email):
    """Check if email is authorized"""
    return email.lower() in [e.lower() for e in AUTHORIZED_EMAILS]

def check_rate_limit(ip):
    """Check if IP is rate limited"""
    current_time = time.time()
    
    if ip in failed_attempts:
        attempts, last_attempt = failed_attempts[ip]
        
        # Reset attempts if lockout time has passed
        if current_time - last_attempt > LOCKOUT_TIME:
            del failed_attempts[ip]
            return True
        
        # Check if IP is locked out
        if attempts >= MAX_FAILED_ATTEMPTS:
            return False
    
    return True

def record_failed_attempt(ip):
    """Record failed authentication attempt"""
    current_time = time.time()
    
    if ip in failed_attempts:
        attempts, _ = failed_attempts[ip]
        failed_attempts[ip] = (attempts + 1, current_time)
    else:
        failed_attempts[ip] = (1, current_time)

def generate_access_code(email):
    """Generate temporary access code for email"""
    code = str(random.randint(100000, 999999))
    access_codes[email] = {
        'code': code,
        'expires': time.time() + 300,  # 5 minutes
        'ip': get_client_ip()
    }
    return code

def send_access_code_email(email, code):
    """Send access code via email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        msg['Subject'] = "SVN Trading Bot - Pieejas kods"
        
        body = f"""
Jūsu pieejas kods SVN Trading Bot sistēmai ir: {code}

Šis kods derīgs 5 minūtes.

Ja neesat pieprasījis šo kodu, lūdzu, ignorējiet šo e-pastu.

Ar cieņu,
SVN Trading Bot komanda
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_EMAIL, email, text)
        server.quit()
        
        print(f"Access code sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        return False

def verify_access_code(email, code):
    """Verify access code for email"""
    if email not in access_codes:
        return False
    
    stored = access_codes[email]
    if time.time() > stored['expires']:
        del access_codes[email]
        return False
    
    if stored['code'] == code:
        del access_codes[email]
        return True
    
    return False

def generate_session_token(email):
    """Generate JWT session token"""
    from datetime import timezone
    
    payload = {
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(timezone.utc),
        'ip': get_client_ip()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_session_token(token):
    """Verify JWT session token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Decorators
def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        
        # Check rate limiting
        if not check_rate_limit(client_ip):
            return jsonify({
                'error': 'Too many failed attempts. IP locked for 1 hour.',
                'locked_until': time.time() + LOCKOUT_TIME
            }), 429
        
        # Check authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            record_failed_attempt(client_ip)
            return jsonify({'error': 'Missing Authorization header'}), 401
        
        if not auth_header.startswith('Bearer '):
            record_failed_attempt(client_ip)
            return jsonify({'error': 'Invalid Authorization format'}), 401
        
        token = auth_header.split(' ')[1]
        if token != API_KEY:
            record_failed_attempt(client_ip)
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Check if IP is authorized for API access
        if not is_ip_authorized(client_ip):
            record_failed_attempt(client_ip)
            return jsonify({
                'error': 'Unauthorized IP address',
                'ip': client_ip,
                'message': 'Contact administrator to authorize your IP'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def require_web_auth(f):
    """Decorator to require web authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        
        # Check rate limiting
        if not check_rate_limit(client_ip):
            return jsonify({
                'error': 'Too many failed attempts. IP locked for 1 hour.',
                'locked_until': time.time() + LOCKOUT_TIME
            }), 429
        
        # Check session token from cookies or headers
        token = request.cookies.get('session_token') or request.headers.get('X-Session-Token')
        
        if not token:
            return redirect('/login')
        
        payload = verify_session_token(token)
        if not payload:
            return redirect('/login')
        
        # Verify email is still authorized
        if not is_email_authorized(payload.get('email', '')):
            return redirect('/login')
        
        # Add user info to request
        request.user_email = payload.get('email')
        request.user_ip = client_ip
        
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/api/send-code', methods=['POST'])
def send_code():
    """Send access code to authorized email"""
    client_ip = get_client_ip()
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        return jsonify({
            'error': 'Pārāk daudz mēģinājumu. Mēģiniet vēlāk.',
            'locked_until': time.time() + LOCKOUT_TIME
        }), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Check if email is authorized
    if not is_email_authorized(email):
        record_failed_attempt(client_ip)
        return jsonify({'error': 'E-pasta adrese nav autorizēta'}), 403
    
    # Generate and send access code
    code = generate_access_code(email)
    
    # Try to send email
    if SMTP_EMAIL and SMTP_PASSWORD:
        if send_access_code_email(email, code):
            return jsonify({'message': 'Pieejas kods nosūtīts uz jūsu e-pastu'})
        else:
            return jsonify({'error': 'Failed to send email. Please try again.'}), 500
    else:
        # For development - return code directly (remove in production)
        return jsonify({'message': 'Access code sent', 'code': code})

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    """Verify access code and create session"""
    client_ip = get_client_ip()
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        return jsonify({
            'error': 'Pārāk daudz mēģinājumu. Mēģiniet vēlāk.',
            'locked_until': time.time() + LOCKOUT_TIME
        }), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    
    if not email or not code:
        return jsonify({'error': 'Email and code are required'}), 400
    
    # Check if email is authorized
    if not is_email_authorized(email):
        record_failed_attempt(client_ip)
        return jsonify({'error': 'E-pasta adrese nav autorizēta'}), 403
    
    # Verify access code
    if not verify_access_code(email, code):
        record_failed_attempt(client_ip)
        return jsonify({'error': 'Nepareizs vai novecojis pieejas kods'}), 400
    
    # Create session token
    session_token = generate_session_token(email)
    
    # Create response with session cookie
    response = make_response(jsonify({
        'message': 'Pieslēgšanās veiksmīga',
        'token': session_token,
        'user': email
    }))
    
    # Set secure cookie
    response.set_cookie(
        'session_token',
        session_token,
        max_age=24*60*60,  # 24 hours
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite='Strict'
    )
    
    return response

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user by clearing session"""
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.set_cookie('session_token', '', expires=0)
    return response

# Static file routes
@app.route('/')
def index():
    """Main dashboard - requires authentication"""
    # Check if user is authenticated
    token = request.cookies.get('session_token')
    if not token:
        return redirect('/login')
    
    payload = verify_session_token(token)
    if not payload:
        return redirect('/login')
    
    # Serve dashboard
    try:
        with open('static/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return redirect('/dashboard')

@app.route('/login')
def login_page():
    """Login page"""
    try:
        with open('static/login.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Return inline login page
        return """
        <!DOCTYPE html>
        <html lang="lv">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SVN Trading Bot - Login</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                }
                
                .login-container {
                    background: rgba(255, 255, 255, 0.15);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    max-width: 400px;
                    width: 100%;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                
                .login-header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .login-header h1 {
                    font-size: 1.8em;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: 500;
                    color: rgba(255, 255, 255, 0.9);
                }
                
                input {
                    width: 100%;
                    padding: 15px;
                    border: none;
                    border-radius: 10px;
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    font-size: 16px;
                    box-sizing: border-box;
                    transition: all 0.3s ease;
                }
                
                input:focus {
                    outline: none;
                    background: rgba(255, 255, 255, 0.3);
                    transform: scale(1.02);
                }
                
                input::placeholder {
                    color: rgba(255, 255, 255, 0.6);
                }
                
                .login-btn {
                    width: 100%;
                    padding: 15px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-top: 10px;
                }
                
                .login-btn:hover {
                    background: #45a049;
                    transform: translateY(-2px);
                }
                
                .login-btn:disabled {
                    background: #666;
                    cursor: not-allowed;
                    transform: none;
                }
                
                .info {
                    text-align: center;
                    margin-top: 20px;
                    opacity: 0.8;
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                .error {
                    color: #ff6b6b;
                    text-align: center;
                    margin-bottom: 20px;
                    padding: 10px;
                    border-radius: 5px;
                    background: rgba(255, 107, 107, 0.1);
                }
                
                .success {
                    color: #4CAF50;
                    text-align: center;
                    margin-bottom: 20px;
                    padding: 10px;
                    border-radius: 5px;
                    background: rgba(76, 175, 80, 0.1);
                }
                
                .step-indicator {
                    text-align: center;
                    margin-bottom: 20px;
                    font-size: 14px;
                    opacity: 0.8;
                }
                
                .hidden {
                    display: none;
                }
                
                .loading {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #4CAF50;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 10px;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="login-header">
                    <h1>🔐 SVN Trading Bot</h1>
                </div>
                
                <div id="error-message" class="error hidden"></div>
                <div id="success-message" class="success hidden"></div>
                
                <!-- Step 1: Email Input -->
                <div id="step1">
                    <div class="step-indicator">Solis 1: Ievadiet savu e-pasta adresi</div>
                    <form id="email-form">
                        <div class="form-group">
                            <label for="email">Authorized Email:</label>
                            <input type="email" id="email" name="email" required 
                                   placeholder="jūsu@e-pasts.lv">
                        </div>
                        <button type="submit" class="login-btn" id="email-btn">
                            Nosūtīt pieejas kodu
                        </button>
                    </form>
                </div>
                
                <!-- Step 2: Access Code Input -->
                <div id="step2" class="hidden">
                    <div class="step-indicator">Solis 2: Ievadiet pieejas kodu</div>
                    <form id="code-form">
                        <div class="form-group">
                            <label for="access_code">Access Code:</label>
                            <input type="text" id="access_code" name="access_code" required 
                                   placeholder="Ievadiet 6-ciparu kodu" maxlength="6">
                        </div>
                        <button type="submit" class="login-btn" id="code-btn">
                            Pieslēgties
                        </button>
                        <button type="button" class="login-btn" id="back-btn" 
                                style="background: #666; margin-top: 10px;">
                            Atpakaļ
                        </button>
                    </form>
                </div>
                
                <div class="info">
                    <p>Tikai autorizēti lietotāji var piekļūt šai sistēmai.</p>
                    <p>Sazinieties ar administratoru, lai saņemtu pieejas datus.</p>
                </div>
            </div>
            
            <script>
                const step1 = document.getElementById('step1');
                const step2 = document.getElementById('step2');
                const emailForm = document.getElementById('email-form');
                const codeForm = document.getElementById('code-form');
                const emailBtn = document.getElementById('email-btn');
                const codeBtn = document.getElementById('code-btn');
                const backBtn = document.getElementById('back-btn');
                const errorMessage = document.getElementById('error-message');
                const successMessage = document.getElementById('success-message');
                
                let userEmail = '';
                
                function showError(message) {
                    errorMessage.textContent = message;
                    errorMessage.classList.remove('hidden');
                    successMessage.classList.add('hidden');
                }
                
                function showSuccess(message) {
                    successMessage.textContent = message;
                    successMessage.classList.remove('hidden');
                    errorMessage.classList.add('hidden');
                }
                
                function hideMessages() {
                    errorMessage.classList.add('hidden');
                    successMessage.classList.add('hidden');
                }
                
                emailForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    hideMessages();
                    
                    const email = document.getElementById('email').value.trim();
                    if (!email) {
                        showError('Lūdzu ievadiet e-pasta adresi');
                        return;
                    }
                    
                    emailBtn.innerHTML = '<span class="loading"></span>Nosūta...';
                    emailBtn.disabled = true;
                    
                    try {
                        const response = await fetch('/api/send-code', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ email: email })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            userEmail = email;
                            showSuccess('Pieejas kods nosūtīts uz jūsu e-pastu');
                            step1.classList.add('hidden');
                            step2.classList.remove('hidden');
                            document.getElementById('access_code').focus();
                        } else {
                            showError(data.error || 'Kļūda nosūtot pieejas kodu');
                        }
                    } catch (error) {
                        showError('Savienojuma kļūda. Mēģiniet vēlreiz.');
                    } finally {
                        emailBtn.innerHTML = 'Nosūtīt pieejas kodu';
                        emailBtn.disabled = false;
                    }
                });
                
                codeForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    hideMessages();
                    
                    const code = document.getElementById('access_code').value.trim();
                    if (!code) {
                        showError('Lūdzu ievadiet pieejas kodu');
                        return;
                    }
                    
                    codeBtn.innerHTML = '<span class="loading"></span>Pārbauda...';
                    codeBtn.disabled = true;
                    
                    try {
                        const response = await fetch('/api/verify-code', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ 
                                email: userEmail, 
                                code: code 
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            showSuccess('Pieslēgšanās veiksmīga! Pārvirza...');
                            setTimeout(() => {
                                window.location.href = '/dashboard';
                            }, 1500);
                        } else {
                            showError(data.error || 'Nepareizs pieejas kods');
                        }
                    } catch (error) {
                        showError('Savienojuma kļūda. Mēģiniet vēlreiz.');
                    } finally {
                        codeBtn.innerHTML = 'Pieslēgties';
                        codeBtn.disabled = false;
                    }
                });
                
                backBtn.addEventListener('click', () => {
                    hideMessages();
                    step2.classList.add('hidden');
                    step1.classList.remove('hidden');
                    document.getElementById('access_code').value = '';
                    document.getElementById('email').focus();
                });
            </script>
        </body>
        </html>
        """

@app.route('/dashboard')
def dashboard():
    """Secure dashboard for authorized users"""
    # Check if user is authenticated
    token = request.cookies.get('session_token')
    if not token:
        return redirect('/login')
    
    payload = verify_session_token(token)
    if not payload:
        return redirect('/login')
    
    # Check if email is still authorized
    if not is_email_authorized(payload.get('email', '')):
        return redirect('/login')
    
    user_email = payload.get('email')
    
    # Serve dashboard
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SVN Trading Bot - Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .user-bar {{
                background: rgba(255,255,255,0.2);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .card {{
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }}
            .logout-btn {{
                background: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s ease;
            }}
            .logout-btn:hover {{
                background: #da190b;
                transform: translateY(-2px);
            }}
            .status-green {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .api-link {{
                color: #87CEEB;
                text-decoration: none;
                transition: color 0.3s ease;
            }}
            .api-link:hover {{
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 SVN Trading Bot</h1>
            <p>AI-Powered Smart Money Trading System</p>
        </div>
        
        <div class="user-bar">
            <span>✅ Welcome, <strong>{user_email}</strong></span>
            <form method="POST" action="/logout" style="display: inline;">
                <button type="submit" class="logout-btn">Logout</button>
            </form>
        </div>
        
        <div class="card">
            <h3>📊 System Status</h3>
            <p class="status-green">✅ System Active</p>
            <p>⏰ Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>🔗 API Version: 2.0.0</p>
        </div>
        
        <div class="card">
            <h3>🔗 API Endpoints</h3>
            <ul>
                <li><a href="/api/health" class="api-link">Health Check</a></li>
                <li><a href="/api/dashboard-data" class="api-link">Dashboard Data</a></li>
                <li>POST /api/predict - AI Prediction</li>
                <li>POST /api/feedback - Trade Feedback</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>📈 Trading Statistics</h3>
            <p>Total Trades: {len(trades_data)}</p>
            <p>Active Predictions: {len(predictions_cache)}</p>
            <p>Session IP: {request.environ.get('REMOTE_ADDR', 'Unknown')}</p>
        </div>
    </body>
    </html>
    """

# API routes
@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    """AI prediction endpoint for MT5 bot"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract features from MT5 smart money analysis
        symbol = data.get('symbol', 'UNKNOWN')
        timeframe = data.get('timeframe', 'M15')
        ob_signal = data.get('ob_signal', 0)
        fvg_signal = data.get('fvg_signal', 0)
        bos_signal = data.get('bos_signal', 0)
        choch_signal = data.get('choch_signal', 0)
        liq_signal = data.get('liq_signal', 0)
        
        # Simple AI logic based on smart money signals
        bullish_score = 0
        bearish_score = 0
        
        # Weight the signals
        if ob_signal == 1: bullish_score += 3
        elif ob_signal == 2: bearish_score += 3
        
        if bos_signal == 1: bullish_score += 2
        elif bos_signal == 2: bearish_score += 2
        
        if fvg_signal == 1: bullish_score += 1
        elif fvg_signal == 2: bearish_score += 1
        
        if choch_signal == 1: bullish_score += 1
        elif choch_signal == 2: bearish_score += 1
        
        if liq_signal == 1: bullish_score += 1
        elif liq_signal == 2: bearish_score += 1
        
        # Determine prediction
        if bullish_score > bearish_score + 1:
            prediction = 1  # BUY
            signal = "BUY"
            confidence = min(0.95, 0.6 + (bullish_score - bearish_score) * 0.05)
        elif bearish_score > bullish_score + 1:
            prediction = 2  # SELL
            signal = "SELL"
            confidence = min(0.95, 0.6 + (bearish_score - bullish_score) * 0.05)
        else:
            prediction = 0  # HOLD
            signal = "HOLD"
            confidence = 0.5
        
        # Store prediction for tracking
        prediction_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        predictions_cache[prediction_key] = {
            'symbol': symbol,
            'prediction': prediction,
            'signal': signal,
            'confidence': confidence,
            'features': data,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'prediction': prediction,
            'signal': signal,
            'confidence': round(confidence, 3),
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/api/feedback', methods=['POST'])
@require_api_key
def feedback():
    """Trade feedback endpoint for MT5 bot"""
    try:
        data = request.get_json()
        trade_id = data.get('trade_id')
        profit = data.get('profit', 0.0)
        is_win = data.get('is_win', False)
        signal = data.get('signal', 0)
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Store trade result
        trade_record = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'profit': profit,
            'is_win': is_win,
            'signal': signal
        }
        trades_data.append(trade_record)
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Feedback failed: {str(e)}'}), 500

@app.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    """Dashboard data endpoint for authenticated web users"""
    # Check if user is authenticated
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    payload = verify_session_token(token)
    if not payload:
        return jsonify({'error': 'Invalid session'}), 401
    
    return jsonify({
        'status': 'active',
        'user': payload.get('email'),
        'trades_count': len(trades_data),
        'predictions_count': len(predictions_cache),
        'recent_trades': trades_data[-10:],
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
