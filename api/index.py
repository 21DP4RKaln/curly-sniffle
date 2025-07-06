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

# Configuration - ALL SENSITIVE DATA FROM ENVIRONMENT VARIABLES
SECRET_KEY = os.environ.get('SECRET_KEY')
API_KEY = os.environ.get('MT5_API_KEY') 
ACCESS_CODE = os.environ.get('ACCESS_CODE')

# Security check - ensure required environment variables are set
if not SECRET_KEY:
    print("ERROR: SECRET_KEY environment variable is required!")
    import sys
    sys.exit(1)
if not API_KEY:
    print("ERROR: MT5_API_KEY environment variable is required!")
    import sys
    sys.exit(1)
if not ACCESS_CODE:
    print("ERROR: ACCESS_CODE environment variable is required!")
    import sys
    sys.exit(1)

# Authorized users and IPs from environment variables
AUTHORIZED_EMAILS_ENV = os.environ.get('ALLOWED_EMAILS', '')
if not AUTHORIZED_EMAILS_ENV:
    raise ValueError("ALLOWED_EMAILS environment variable is required!")

AUTHORIZED_EMAILS = [email.strip().lower() for email in AUTHORIZED_EMAILS_ENV.split(',') if email.strip()]

# IP whitelist from environment variables
AUTHORIZED_IPS_ENV = os.environ.get('ALLOWED_IPS', '127.0.0.1,::1')
AUTHORIZED_IPS = [ip.strip() for ip in AUTHORIZED_IPS_ENV.split(',') if ip.strip()]

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
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
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
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'GET':
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SVN Trading Bot - Login</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                }
                .login-container {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    max-width: 400px;
                    width: 100%;
                }
                h1 { text-align: center; margin-bottom: 30px; }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
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
                }
                input::placeholder {
                    color: rgba(255, 255, 255, 0.7);
                }
                button {
                    width: 100%;
                    padding: 15px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 18px;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                button:hover {
                    background: #45a049;
                }
                .error {
                    color: #ff6b6b;
                    text-align: center;
                    margin-bottom: 20px;
                }
                .info {
                    text-align: center;
                    margin-top: 20px;
                    opacity: 0.8;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>🔐 SVN Trading Bot</h1>
                <form method="POST">
                    <div class="form-group">
                        <label for="email">Authorized Email:</label>
                        <input type="email" id="email" name="email" required 
                               placeholder="Enter your authorized email">
                    </div>                    <div class="form-group">
                        <label for="access_code">Access Code:</label>
                        <input type="password" id="access_code" name="access_code" required 
                               placeholder="Enter access code">
                    </div>
                    <button type="submit">Login</button>
                </form>
                <div class="info">
                    <p>Only authorized users can access this system.</p>
                    <p>Contact administrator for access credentials.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    # POST request - handle login
    client_ip = get_client_ip()
    
    if not check_rate_limit(client_ip):
        return jsonify({
            'error': 'Too many failed attempts. Try again later.'
        }), 429
    
    email = request.form.get('email', '').strip().lower()
    access_code = request.form.get('access_code', '').strip()
      # Check if email is authorized
    if not is_email_authorized(email):
        record_failed_attempt(client_ip)
        return jsonify({'error': 'Email not authorized'}), 403
    
    # Verify access code from environment variable
    if access_code != ACCESS_CODE:
        record_failed_attempt(client_ip)
        return jsonify({'error': 'Invalid access code'}), 401
    
    # Generate session token
    token = generate_session_token(email)
    
    # Store session
    active_sessions[email] = {
        'token': token,
        'ip': client_ip,
        'login_time': time.time()
    }
    
    # Create response with session cookie
    response = make_response(redirect('/dashboard'))
    response.set_cookie('session_token', token, httponly=True, secure=True, max_age=86400)
    
    return response

@app.route('/logout', methods=['POST'])
def logout():
    """Logout and clear session"""
    token = request.cookies.get('session_token')
    if token:
        payload = verify_session_token(token)
        if payload:
            email = payload.get('email')
            if email in active_sessions:
                del active_sessions[email]
    
    response = make_response(redirect('/login'))
    response.set_cookie('session_token', '', expires=0)
    return response

# Main routes
@app.route('/')
def home():
    """Home page - redirect to login or dashboard"""
    token = request.cookies.get('session_token')
    if token and verify_session_token(token):
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/dashboard')
@require_web_auth
def dashboard():
    """Secure dashboard for authorized users"""
    user_email = request.user_email
    
    # Try to serve static dashboard file
    try:
        import os
        static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'index.html')
        if os.path.exists(static_path):
            with open(static_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Inject user info
                content = content.replace(
                    '<p>AI-Powered Smart Money Trading System</p>',
                    f'<p>AI-Powered Smart Money Trading System</p><p style="opacity: 0.8;">Welcome, {user_email}</p>'
                )
                return content
    except:
        pass
    
    # Fallback dashboard
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
                padding: 10px;
                border-radius: 5px;
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
            button {{
                background: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 SVN Trading Bot</h1>
            <p>AI-Powered Smart Money Trading System</p>
        </div>
        
        <div class="user-bar">
            <span>Welcome, {user_email}</span>
            <form method="POST" action="/logout" style="display: inline;">
                <button type="submit">Logout</button>
            </form>
        </div>
        
        <div class="card">
            <h3>System Status</h3>
            <p>✅ System Active</p>
            <p>⏰ Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="card">
            <h3>API Endpoints</h3>
            <ul>
                <li><a href="/api/health" style="color: white;">Health Check</a></li>
                <li><a href="/api/dashboard" style="color: white;">Dashboard Data</a></li>
            </ul>
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

@app.route('/api/dashboard')
@require_web_auth
def dashboard_data():
    """Dashboard data endpoint"""
    return jsonify({
        'status': 'active',
        'trades_count': len(trades_data),
        'predictions_count': len(predictions_cache),
        'last_update': datetime.now().isoformat(),
        'user': request.user_email
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
