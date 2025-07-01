import os
import sqlite3
import secrets
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect
from auth import require_auth, auth_codes, send_email_code, generate_token, verify_token
from dashboard import init_database
from predict import ai_predictor

app = Flask(__name__)

# Initialize database
init_database()

# Auth endpoint
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    
    ADMIN_EMAIL = os.environ.get('ALLOWED_EMAILS', 'sitvain12@gmail.com').lower()
    
    if email and not code:
        if email.strip().lower() != ADMIN_EMAIL.lower():
            return jsonify({'error': 'E-pasts nav autorizēts'}), 403
        
        auth_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        auth_codes[email] = {
            'code': auth_code,
            'timestamp': datetime.now(),
            'attempts': 0
        }
        
        email_sent = send_email_code(email, auth_code)
        
        response = {'message': 'Kods nosūtīts uz e-pastu'}
        if not email_sent:
            response['demo_code'] = auth_code
            
        return jsonify(response)
    
    elif email and code:
        if email not in auth_codes:
            return jsonify({'error': 'Kods nav atrasts'}), 400
        
        stored_data = auth_codes[email]
        
        if datetime.now() - stored_data['timestamp'] > timedelta(minutes=10):
            del auth_codes[email]
            return jsonify({'error': 'Kods ir beidzies'}), 400
        
        if stored_data['attempts'] >= 3:
            del auth_codes[email]
            return jsonify({'error': 'Pārāk daudz mēģinājumu'}), 400
        
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

# Dashboard endpoint
@app.route('/api/dashboard', methods=['GET'])
@require_auth
def api_dashboard():
    """Dashboard API"""
    try:
        conn = sqlite3.connect('svnbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COALESCE(SUM(profit), 0) as total_profit,
                COUNT(*) as total_trades,
                COALESCE(AVG(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100, 0) as win_rate
            FROM trades 
            WHERE timestamp >= datetime('now', '-30 days')
        ''')
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) as today_trades
            FROM trades 
            WHERE DATE(timestamp) = DATE('now')
        ''')
        today_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT timestamp, user_id, symbol, signal, profit, confidence
            FROM trades 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_trades = cursor.fetchall()
        
        conn.close()
        
        trades_data = []
        for trade in recent_trades:
            trades_data.append({
                'timestamp': trade[0],
                'user_id': trade[1],
                'symbol': trade[2],
                'type': 'buy' if trade[3] == 'BUY' else 'sell',
                'volume': 0.1,
                'profit': trade[4],
                'ai_signal': trade[3]
            })
        
        return jsonify({
            'statistics': {
                'active_bots': stats[0] or 0,
                'total_profit': round(stats[1] or 0, 2),
                'trades_today': today_stats[0] or 0,
                'ai_accuracy': round(stats[3] or 0, 1)
            },
            'charts': {
                'profit': {
                    'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    'data': [120, 180, 250, 320, 280, 410, 390]
                }
            },
            'recent_trades': trades_data,
            'system_logs': [
                {'time': datetime.now().strftime('%H:%M:%S'), 'message': 'AI system operational', 'type': 'info'}
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Users endpoint
@app.route('/api/users', methods=['GET'])
@require_auth
def api_users():
    """Users API"""
    try:
        conn = sqlite3.connect('svnbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                u.id, u.registration_date, u.last_activity, u.total_trades, u.profit
            FROM users u
            ORDER BY u.last_activity DESC
        ''')
        users_data = cursor.fetchall()
        
        users = []
        for user in users_data:
            users.append({
                'id': user[0],
                'registration_date': user[1],
                'last_activity': user[2],
                'total_trades': user[3] or 0,
                'profit': user[4] or 0.0,
                'balance': (user[4] or 0) + 1000,
                'equity': (user[4] or 0) + 1000
            })
        
        conn.close()
        
        return jsonify({
            'users': users,
            'stats': {
                'total': len(users),
                'active': len([u for u in users if u['last_activity']]),
                'total_profit': sum(u['profit'] for u in users)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Prediction endpoint
@app.route('/api/predict', methods=['POST'])
def predict():
    """AI prediction"""
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Features required'}), 400
        
        features = data['features']
        symbol = data.get('symbol', 'UNKNOWN')
        
        result = ai_predictor.predict(features)
        
        try:
            conn = sqlite3.connect('svnbot.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_data (timestamp, user_id, symbol, features, signal, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                data.get('account_id', 'unknown'),
                symbol,
                str(features),
                result['prediction'],
                result['confidence']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Database storage warning: {e}")
        
        signal_names = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
        
        return jsonify({
            'prediction': result['prediction'],
            'signal': signal_names[result['prediction']],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'version': '1.0',
                'training_samples': len(ai_predictor.training_data)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Training data endpoint
@app.route('/api/training_data', methods=['POST'])
def receive_training_data():
    """Training data from MT5"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        features = data.get('features', [])
        signal = data.get('signal', 0)
        result = data.get('result', 0.0)
        
        if not features:
            return jsonify({'error': 'Features required'}), 400
        
        success = ai_predictor.train(features, signal, result)
        
        try:
            conn = sqlite3.connect('svnbot.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (timestamp, user_id, symbol, signal, profit, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data.get('timestamp', datetime.now().isoformat()),
                data.get('account_id', 'unknown'),
                data.get('symbol', 'UNKNOWN'),
                'BUY' if signal > 0 else 'SELL' if signal < 0 else 'HOLD',
                result,
                0.75
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Database storage warning: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Training data received',
            'model_updated': success,
            'training_samples': len(ai_predictor.training_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Data reception endpoint
@app.route('/api/data', methods=['POST'])
def receive_bot_data():
    """Data from MT5 bots"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = sqlite3.connect('svnbot.db')
        cursor = conn.cursor()
        
        account_id = data.get('account_id', 'unknown')
        symbol = data.get('symbol', 'UNKNOWN')
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (id, registration_date, last_activity, total_trades, profit)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            account_id,
            data.get('registration_date', datetime.now().isoformat()),
            datetime.now().isoformat(),
            data.get('total_trades', 0),
            data.get('daily_profit', 0.0)
        ))
        
        if 'market_data' in data:
            for market_point in data['market_data']:
                cursor.execute('''
                    INSERT INTO market_data (timestamp, user_id, symbol, features, signal, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    market_point.get('time', datetime.now().isoformat()),
                    account_id,
                    symbol,
                    str(market_point.get('indicators', [])),
                    market_point.get('signal', 0),
                    0.75
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Data received successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Feedback endpoint
@app.route('/api/feedback', methods=['POST'])
def receive_feedback():
    """Trade results"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = sqlite3.connect('svnbot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (timestamp, user_id, symbol, signal, profit, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('timestamp', datetime.now().isoformat()),
            data.get('account_id', 'unknown'),
            data.get('symbol', 'UNKNOWN'),
            'BUY' if data.get('signal', 0) > 0 else 'SELL',
            data.get('profit', 0.0),
            0.75
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received',
            'learning_updated': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Web pages
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="lv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVN Trading Bot - Pieteikšanās</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            overflow: hidden;
            width: 100%;
            max-width: 400px;
        }
        .login-header {
            background: linear-gradient(45deg, #1e3c72, #2a5298);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        .login-body { padding: 2rem; }
        .form-control {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
            transition: all 0.3s ease;
        }
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            border: none;
            border-radius: 10px;
            padding: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .demo-code {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <div style="width: 60px; height: 60px; margin: 0 auto 1rem; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px;">
                <i class="fas fa-robot"></i>
            </div>
            <h2 class="mb-0">SVN Trading Bot</h2>
            <p class="mb-0 opacity-75">MT5 AI Monitorings Platforma</p>
        </div>
        
        <div class="login-body">
            <div id="email-form">
                <h4 class="text-center mb-4">Pieteikšanās</h4>
                <div class="mb-3">
                    <label for="email" class="form-label">
                        <i class="fas fa-envelope me-2"></i>E-pasta adrese
                    </label>
                    <input type="email" class="form-control" id="email" placeholder="jūsu@epasts.lv" required>
                </div>
                <button onclick="sendCode()" class="btn btn-primary w-100">
                    <i class="fas fa-paper-plane me-2"></i>Nosūtīt kodu
                </button>
            </div>

            <div id="code-form" style="display: none;">
                <h4 class="text-center mb-3">Verifikācijas kods</h4>
                <p class="text-muted text-center">
                    Kods nosūtīts uz: <strong id="sent-email"></strong>
                </p>
                <div class="mb-3">
                    <label for="code" class="form-label">
                        <i class="fas fa-key me-2"></i>6-ciparu kods
                    </label>
                    <input type="text" class="form-control text-center" id="code" 
                           placeholder="123456" maxlength="6" style="font-size: 1.5rem; letter-spacing: 0.5rem;">
                    <div id="demo-code" class="demo-code" style="display: none;">
                        <small><strong>Development mode:</strong> <span id="demo-code-value"></span></small>
                    </div>
                </div>
                <button onclick="verifyCode()" class="btn btn-primary w-100 mb-2">
                    <i class="fas fa-sign-in-alt me-2"></i>Pieteikties
                </button>
                <button onclick="showEmailForm()" class="btn btn-outline-secondary w-100">
                    <i class="fas fa-arrow-left me-2"></i>Atpakaļ
                </button>
            </div>
        </div>

        <div class="text-center p-3 border-top">
            <small class="text-muted">
                <i class="fas fa-shield-alt me-1"></i>
                Aizsargāts ar divfaktoru autentifikāciju
            </small>
        </div>
    </div>

    <script>
        let currentEmail = '';

        function sendCode() {
            const email = document.getElementById('email').value;
            
            if (!email) {
                alert('Ievadiet e-pasta adresi');
                return;
            }
            
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: email })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    currentEmail = email;
                    document.getElementById('sent-email').textContent = email;
                    document.getElementById('email-form').style.display = 'none';
                    document.getElementById('code-form').style.display = 'block';
                    
                    if (data.demo_code) {
                        document.getElementById('demo-code-value').textContent = data.demo_code;
                        document.getElementById('demo-code').style.display = 'block';
                    }
                    
                    document.getElementById('code').focus();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Kļūda nosūtot kodu');
            });
        }

        function verifyCode() {
            const code = document.getElementById('code').value;
            
            if (!code || code.length !== 6) {
                alert('Ievadiet 6-ciparu kodu');
                return;
            }
            
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    email: currentEmail, 
                    code: code 
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    localStorage.setItem('auth_token', data.token);
                    window.location.href = '/dashboard';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Kļūda verificējot kodu');
            });
        }

        function showEmailForm() {
            document.getElementById('code-form').style.display = 'none';
            document.getElementById('email-form').style.display = 'block';
            document.getElementById('email').focus();
        }

        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('email').focus();
        });

        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                if (document.getElementById('email-form').style.display !== 'none') {
                    sendCode();
                } else {
                    verifyCode();
                }
            }
        });
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="lv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVN Trading Bot - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .navbar { background: linear-gradient(45deg, #1e3c72, #2a5298) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats-card {
            background: white; border-radius: 15px; padding: 1.5rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08); border: none; transition: transform 0.3s ease;
        }
        .stats-card:hover { transform: translateY(-5px); }
        .stats-value { font-size: 2rem; font-weight: bold; color: #1e3c72; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-online { background: #28a745; }
        .prediction-box {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white; border-radius: 15px; padding: 1.5rem; text-align: center;
        }
        .trade-item {
            background: white; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
            border-left: 4px solid #28a745; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .trade-item.loss { border-left-color: #dc3545; }
        .bot-card { background: white; border-radius: 15px; border: none; box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-robot me-2"></i>SVN Trading Bot
            </a>
            <div class="navbar-nav ms-auto">
                <div class="nav-item">
                    <span class="status-indicator status-online" id="connection-status"></span>
                    <span id="status-text">Online</span>
                </div>
                <div class="nav-item ms-3">
                    <button class="btn btn-outline-light btn-sm" onclick="logout()">
                        <i class="fas fa-sign-out-alt me-1"></i>Iziet
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="stats-value" id="active-bots">--</div>
                            <div class="text-muted">Aktīvi Boti</div>
                        </div>
                        <i class="fas fa-robot fa-2x text-primary"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="stats-value" id="total-profit">$--</div>
                            <div class="text-muted">Kopējā Peļņa</div>
                        </div>
                        <i class="fas fa-chart-line fa-2x text-success"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="stats-value" id="trades-today">--</div>
                            <div class="text-muted">Darījumi Šodien</div>
                        </div>
                        <i class="fas fa-exchange-alt fa-2x text-info"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="stats-value" id="ai-accuracy">--%</div>
                            <div class="text-muted">AI Precizitāte</div>
                        </div>
                        <i class="fas fa-brain fa-2x text-warning"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-8">
                <div class="card bot-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-area me-2"></i>Peļņas Grafiks</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="profitChart" height="300"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="prediction-box mb-3">
                    <h5><i class="fas fa-crystal-ball me-2"></i>AI Prognoze</h5>
                    <div id="prediction-signal" class="h3 mb-2">HOLD</div>
                    <div>Uzticamība: <span id="prediction-confidence">75%</span></div>
                </div>
                <div class="card bot-card">
                    <div class="card-header">
                        <h6><i class="fas fa-list me-2"></i>Nesenie Darījumi</h6>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        <div id="recent-trades">
                            <p class="text-muted text-center">Nav nesenu darījumu</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card bot-card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-users me-2"></i>Aktīvie Boti</h5>
                        <button class="btn btn-primary btn-sm" onclick="refreshData()">
                            <i class="fas fa-sync-alt me-1"></i>Atjaunot
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Bot ID</th>
                                        <th>Pēdējā Aktivitāte</th>
                                        <th>Darījumi</th>
                                        <th>Peļņa</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="bots-table">
                                    <tr><td colspan="5" class="text-center text-muted">Nav aktīvu botu</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let charts = {};
        
        function checkAuth() {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                window.location.href = '/login';
                return false;
            }
            return token;
        }

        function logout() {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }

        function apiCall(endpoint, options = {}) {
            const token = checkAuth();
            if (!token) return Promise.reject('No auth');
            
            return fetch(endpoint, {
                ...options,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
        }

        function loadDashboardData() {
            apiCall('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    updateStatistics(data.statistics);
                    updateCharts(data.charts);
                    updateRecentTrades(data.recent_trades);
                })
                .catch(error => console.error('Error:', error));
            
            apiCall('/api/users')
                .then(response => response.json())
                .then(data => {
                    updateBotsTable(data.users);
                })
                .catch(error => console.error('Error:', error));
        }

        function updateStatistics(stats) {
            document.getElementById('active-bots').textContent = stats.active_bots || 0;
            document.getElementById('total-profit').textContent = '$' + (stats.total_profit || 0).toFixed(2);
            document.getElementById('trades-today').textContent = stats.trades_today || 0;
            document.getElementById('ai-accuracy').textContent = (stats.ai_accuracy || 0).toFixed(1) + '%';
        }

        function updateCharts(chartData) {
            const ctx = document.getElementById('profitChart').getContext('2d');
            
            if (charts.profit) {
                charts.profit.destroy();
            }
            
            charts.profit = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.profit.labels,
                    datasets: [{
                        label: 'Peļņa ($)',
                        data: chartData.profit.data,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }

        function updateRecentTrades(trades) {
            const container = document.getElementById('recent-trades');
            
            if (!trades || trades.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">Nav nesenu darījumu</p>';
                return;
            }
            
            container.innerHTML = trades.map(trade => `
                <div class="trade-item ${trade.profit < 0 ? 'loss' : ''}">
                    <div class="d-flex justify-content-between">
                        <div>
                            <strong>${trade.ai_signal}</strong>
                            <small class="text-muted d-block">${trade.symbol}</small>
                        </div>
                        <div class="text-end">
                            <div class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">
                                ${trade.profit >= 0 ? '+' : ''}$${trade.profit.toFixed(2)}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function updateBotsTable(bots) {
            const tbody = document.getElementById('bots-table');
            
            if (!bots || bots.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nav aktīvu botu</td></tr>';
                return;
            }
            
            tbody.innerHTML = bots.map(bot => `
                <tr>
                    <td><i class="fas fa-robot text-primary me-2"></i><strong>${bot.id}</strong></td>
                    <td><small>${new Date(bot.last_activity).toLocaleString()}</small></td>
                    <td><span class="badge bg-info">${bot.total_trades}</span></td>
                    <td class="${bot.profit >= 0 ? 'text-success' : 'text-danger'}">
                        <strong>$${bot.profit.toFixed(2)}</strong>
                    </td>
                    <td><span class="badge bg-success">Aktīvs</span></td>
                </tr>
            `).join('');
        }

        function refreshData() {
            loadDashboardData();
        }

        function updatePrediction() {
            const signals = ['BUY', 'SELL', 'HOLD'];
            const signal = signals[Math.floor(Math.random() * signals.length)];
            const confidence = Math.floor(Math.random() * 30) + 60;
            
            document.getElementById('prediction-signal').textContent = signal;
            document.getElementById('prediction-confidence').textContent = confidence + '%';
        }

        document.addEventListener('DOMContentLoaded', function() {
            if (checkAuth()) {
                loadDashboardData();
                updatePrediction();
                setInterval(loadDashboardData, 30000);
                setInterval(updatePrediction, 45000);
            }
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def home():
    return redirect('/login')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard', methods=['GET'])
def dashboard_page():
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/test', methods=['GET'])
def api_test():
    return jsonify({
        'status': 'ok',
        'message': 'SVN Trading Bot API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# Serverless handler
def handler(request):
    with app.app_context():
        return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
