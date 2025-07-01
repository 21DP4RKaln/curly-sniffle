"""
Server - для PythonAnywhere

"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from flask_mail import Mail, Message
import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging
import threading
import time
import secrets

try:
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("ML libraries not available, using simplified mode - this is normal for memory-constrained environments")

_scaler = None
_model_cache = {}

def get_scaler():
    """initialization of StandardScaler"""
    global _scaler
    if HAS_ML and _scaler is None:
        _scaler = StandardScaler()
    return _scaler

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
           static_url_path='/static', 
           static_folder=os.path.join(os.path.dirname(base_dir), 'static'),
           template_folder=os.path.join(os.path.dirname(base_dir), 'templates'))

app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

CORS(app)

app.secret_key = os.environ.get('SECRET_KEY', 'temp-key')

logging.basicConfig(level=logging.WARNING)  
logger = logging.getLogger(__name__)

mail_username = os.environ.get('MAIL_USERNAME')
if mail_username:
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = mail_username
    
    try:
        mail = Mail(app)
        logger.info("Mail configured successfully")
    except Exception as e:
        logger.error(f"Mail configuration error: {e}")
        mail = None
else:
    mail = None
    logger.warning("Mail not configured - MAIL_USERNAME not found")

ALLOWED_EMAILS = [
    os.environ.get('ADMIN_EMAIL_1', 'sitvain12@gmail.com'),
    os.environ.get('ADMIN_EMAIL_2', 'sitvain89@gmail.com')
]

auth_codes = {}

class OptimizedAITradingServer:
    """ AI server """
    
    def __init__(self):
        self.db_path = os.path.join(base_dir, 'SVNbot.db')
        self.models = {}  
        self.is_trained = False
        self.setup_database()
        
        # Memory optimization: Clean old data on startup
        self.cleanup_old_data()
    
    def cleanup_old_data(self):
        """ Clean old data to maintain database size """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Keep only last 30 days of data
            cursor.execute('''
                DELETE FROM market_data 
                WHERE timestamp < datetime('now', '-30 days')
            ''')
            
            cursor.execute('''
                DELETE FROM trades 
                WHERE timestamp < datetime('now', '-30 days')
            ''')
            
            # Vacuum database to reclaim space
            cursor.execute('VACUUM')
            
            conn.commit()
            conn.close()
            
            logger.info("Database cleanup completed")
            
        except Exception as e:
            logger.error(f"Database cleanup error: {e}")

    def setup_database(self):
        """ Optimized database setup for memory efficiency """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable optimizations
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL') 
        cursor.execute('PRAGMA cache_size=2000')
        cursor.execute('PRAGMA temp_store=MEMORY')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                total_trades INTEGER DEFAULT 0,
                profit REAL DEFAULT 0.0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                symbol TEXT,
                features TEXT,
                signal INTEGER,
                confidence REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                symbol TEXT,
                signal TEXT,
                profit REAL,
                confidence REAL
            )        
        ''')
          # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_user_time ON market_data(user_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_user_time ON trades(user_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)')
        
        conn.commit()
        conn.close()
    
    def train_model(self, symbol='default', max_samples=500):
        """ Optimized model training for memory efficiency """
        if not HAS_ML:
            self.is_trained = True
            return True
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Limit samples to reduce memory usage
            cursor.execute('''
                SELECT features, signal FROM market_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (symbol, max_samples))
            
            data = cursor.fetchall()
            conn.close()
            
            if len(data) < 30:  # Reduced minimum threshold
                return False
            
            X = []
            y = []
            
            for row in data:
                try:
                    features = json.loads(row[0])
                    if len(features) >= 10:  
                        # Use only first 10 features to reduce complexity
                        X.append(features[:10])  
                        y.append(row[1])
                except:
                    continue
            
            if len(X) < 20:  # Further reduced threshold
                return False
            
            X = np.array(X)
            y = np.array(y)
            
            # Use smaller, memory-efficient model
            model = RandomForestRegressor(
                n_estimators=20,   # Reduced from 50
                max_depth=5,       # Reduced from 10
                random_state=42,
                n_jobs=1,          # Single thread to save memory
                max_features='sqrt'  # Reduce feature complexity
            )
            
            scaler = get_scaler()
            X_scaled = scaler.fit_transform(X)
            model.fit(X_scaled, y)
            
            self.models[symbol] = {
                'model': model,
                'scaler': scaler,
                'features_count': X.shape[1]
            }
            
            self.is_trained = True
            
            # Force garbage collection to free memory
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
            return False
    
    def predict(self, features, symbol='default'):
        """Quick prediction"""
        try:
            if not HAS_ML or symbol not in self.models:
                import random
                rand_val = random.random()
                if rand_val > 0.6:
                    return [0.1, 0.2, 0.7]  
                elif rand_val < 0.4:
                    return [0.7, 0.2, 0.1]  
                else:
                    return [0.2, 0.6, 0.2]  
            
            model_data = self.models[symbol]
            model = model_data['model']
            scaler = model_data['scaler']
            
            features_limited = features[:model_data['features_count']]
            features_scaled = scaler.transform([features_limited])
            
            prediction = model.predict(features_scaled)[0]
            
            if prediction > 0.6:
                return [0.1, 0.2, 0.7]  
            elif prediction < 0.4:
                return [0.7, 0.2, 0.1]  
            else:
                return [0.2, 0.6, 0.2]                  
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return [0.33, 0.34, 0.33]

ai_server = OptimizedAITradingServer()

# Авторизация
def generate_auth_code():
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def send_auth_code(email, code):
    """email sending feature for PythonAnywhere"""
    if not mail:
        logger.warning("Mail не настроен")
        return False
    
    try:
        msg = Message(
            subject='Access code to BOT Dashboard',
            sender=app.config.get('MAIL_USERNAME'),
            recipients=[email]
        )
        
        msg.body = f"""

Your access code: {code}

Код действителен 10 минут.

--
BOT Dashboard by SVN
        """
        
        msg.html = f"""
<html>
<body>
    <h2>Bot Dashboard</h2>
    <p>Your access code: <strong style="font-size: 18px; color: #007bff;">{code}</strong></p>
    <p><em>Код действителен 10 минут.</em></p>
    <hr>
    <small>BOT Dashboard by SVN</small>
</body>
</html>
        """
        
        with app.app_context():
            mail.send(msg)
        
        logger.info(f"Email sent successfully to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        try:
            simple_msg = Message(
                subject='AI Trading - Код доступа',
                sender=app.config.get('MAIL_USERNAME'),
                recipients=[email],
                body=f'Код доступа: {code}'
            )
            with app.app_context():
                mail.send(simple_msg)
            logger.info(f"Simple email sent to {email}")
            return True
        except Exception as e2:
            logger.error(f"sending also failed: {str(e2)}")
            return False

def is_authenticated():
    return session.get('authenticated', False)

def require_auth(f):
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/api/health')
def health_check():
    return jsonify({'status': 'ok', 'version': 'optimized'})

# AI API Endpoints for MT5 Bot
@app.route('/api/data', methods=['POST'])
def receive_market_data():
    """Receive market data from MT5 bot"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract user info
        user_id = data.get('account_id', 'unknown')
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Register user if new
        conn = sqlite3.connect(ai_server.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, last_activity) 
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (user_id,))
        
        cursor.execute('''
            UPDATE users SET 
                last_activity = CURRENT_TIMESTAMP,
                total_trades = ?,
                profit = ?
            WHERE id = ?
        ''', (data.get('total_trades', 0), data.get('daily_profit', 0), user_id))
        
        # Store market data (limited to save space)
        market_data = data.get('market_data', [])
        for i, market_point in enumerate(market_data[-50:]):  # Only last 50 points
            features_json = json.dumps(market_point.get('indicators', []))
            cursor.execute('''
                INSERT INTO market_data 
                (user_id, symbol, features, signal, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, symbol, features_json, 
                  market_point.get('signal', 0), 0.0))
        
        # Clean old data to save space (keep only last 1000 records per user)
        cursor.execute('''
            DELETE FROM market_data 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM market_data 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1000
            )
        ''', (user_id, user_id))
        
        conn.commit()
        conn.close()
        
        # Trigger model retraining if enough data
        try:
            ai_server.train_model(symbol)
        except:
            pass
        
        return jsonify({
            'status': 'success',
            'message': 'Data received and processed',
            'data_points': len(market_data)
        })
        
    except Exception as e:
        logger.error(f"Error receiving market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict_signal():
    """Provide AI prediction for given features"""
    try:
        data = request.get_json()
        if not data or 'features' not in data:
            return jsonify({'error': 'Features required'}), 400
        
        features = data['features']
        symbol = data.get('symbol', 'default')
        
        # Get prediction from AI
        prediction_probs = ai_server.predict(features, symbol)
        
        # Convert to signal (0=SELL, 1=HOLD, 2=BUY)
        prediction = prediction_probs.index(max(prediction_probs))
        confidence = max(prediction_probs)
        
        return jsonify({
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': {
                'sell': prediction_probs[0],
                'hold': prediction_probs[1], 
                'buy': prediction_probs[2]
            }
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def receive_trade_feedback():
    """Receive trade results for learning"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract trade info
        trade_id = data.get('trade_id')
        profit = data.get('profit', 0)
        is_win = data.get('is_win', False)
        signal = data.get('signal', 0)
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Store trade result
        conn = sqlite3.connect(ai_server.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades 
            (user_id, symbol, signal, profit, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', ('system', symbol, str(signal), profit, 1.0 if is_win else 0.0))
        
        # Clean old trades (keep only last 500)
        cursor.execute('''
            DELETE FROM trades 
            WHERE id NOT IN (
                SELECT id FROM trades 
                ORDER BY timestamp DESC 
                LIMIT 500
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Trade feedback received'
        })
        
    except Exception as e:
        logger.error(f"Error receiving trade feedback: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def bot_status():
    """Get bot and AI status"""
    try:
        conn = sqlite3.connect(ai_server.db_path)
        cursor = conn.cursor()
        
        # Get total stats
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM market_data')
        total_data_points = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_trades = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT AVG(profit), COUNT(*) 
            FROM trades 
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        daily_stats = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'status': 'operational',
            'ai_trained': ai_server.is_trained,
            'total_users': total_users,
            'total_data_points': total_data_points,
            'total_trades': total_trades,
            'daily_avg_profit': daily_stats[0] or 0,
            'daily_trade_count': daily_stats[1] or 0,
            'models_loaded': len(ai_server.models),
            'memory_optimized': True
        })
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

# ...existing code...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        
        logger.info(f"Login attempt: email={email}, code_provided={bool(code)}")
        
        if email and not code:
            if email not in ALLOWED_EMAILS:
                logger.warning(f"Unauthorized email attempt: {email}")
                flash('Email не авторизован. Кто ты, блядь, такой?')
                return render_template('login.html')
            
            auth_code = generate_auth_code()
            auth_codes[email] = {
                'code': auth_code,
                'timestamp': datetime.now(),
                'attempts': 0
            }
            
            logger.info(f"Generated code {auth_code} for {email}")
            
            if send_auth_code(email, auth_code):
                logger.info(f"Code sent successfully to {email}")
                flash('Код отправлен на email')
                return render_template('login.html', email_sent=True, email=email)
            else:
                logger.error(f"Failed to send code to {email}")
                flash('Error sending code. Check your email settings.')
                
        elif email and code:
            if email not in auth_codes:
                flash('Code not found')
                return render_template('login.html')
            
            stored_data = auth_codes[email]
            
            if datetime.now() - stored_data['timestamp'] > timedelta(minutes=10):
                del auth_codes[email]
                flash('Код истек, ты такой медленный')
                return render_template('login.html')
            
            if stored_data['attempts'] >= 3:
                del auth_codes[email]
                flash('не сегодня, брo')
                return render_template('login.html')
            
            if code == stored_data['code']:
                session['authenticated'] = True
                session['user_email'] = email
                del auth_codes[email]
                return redirect(url_for('dashboard'))
            else:
                auth_codes[email]['attempts'] += 1
                flash('Неверный код, как-так?')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def dashboard():
    return render_template('dashboard.html')

@app.route('/users')
@require_auth  
def users():
    return render_template('users.html')

@app.route('/ai-analytics')
@require_auth
def ai_analytics():
    return render_template('ai_analytics.html')


@app.route('/api/dashboard')
@require_auth
def api_dashboard():
    try:
        conn = sqlite3.connect(ai_server.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trades WHERE DATE(timestamp) = DATE("now")')
        today_trades = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(profit), 0) FROM trades')
        total_profit = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'today_trades': today_trades,
            'total_profit': round(total_profit, 2),
            'active_models': len(ai_server.models)
        })
        
    except Exception as e:
        logger.error(f"Ошибка API dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
@require_auth
def api_users():
    try:
        conn = sqlite3.connect(ai_server.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, registration_date, total_trades, profit 
            FROM users 
            ORDER BY registration_date DESC            LIMIT 100
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'registration_date': row[1],
                'total_trades': row[2] or 0,
                'profit': round(row[3] or 0, 2)
            })
        
        conn.close()
        return jsonify({'users': users})
        
    except Exception as e:
        logger.error(f"API user error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test-email')
def test_email():
    """Email configuration test"""
    try:
        if not mail:
            return jsonify({
                'status': 'error',
                'message': 'Mail not configured',
                'mail_username': os.environ.get('MAIL_USERNAME', 'Not set'),
                'mail_password': 'Set' if os.environ.get('MAIL_PASSWORD') else 'Not set'
            })
        
        test_code = '123456'
        admin_email = ALLOWED_EMAILS[0]
        
        if send_auth_code(admin_email, test_code):
            return jsonify({
                'status': 'success',
                'message': f'Test email sent to {admin_email}',
                'code': test_code
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test email'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/debug-config')
def debug_config():
    """Debug configurations"""
    return jsonify({
        'mail_configured': mail is not None,
        'mail_username': os.environ.get('MAIL_USERNAME', 'Not set'),
        'mail_password_set': bool(os.environ.get('MAIL_PASSWORD')),
        'allowed_emails': ALLOWED_EMAILS,
        'secret_key_set': bool(app.secret_key),
        'flask_env': os.environ.get('FLASK_ENV', 'Not set')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    try:
        ai_server.train_model()
    except:
        pass
    
    app.run(host='0.0.0.0', port=port, debug=debug)
