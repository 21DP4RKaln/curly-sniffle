from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    """Main dashboard page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SVN Trading Bot Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .status { padding: 15px; margin: 20px 0; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .nav { text-align: center; margin: 20px 0; }
            .nav a { margin: 0 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .nav a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 SVN Trading Bot Dashboard</h1>
            <div class="status success">
                ✅ Application successfully deployed on Vercel!
            </div>
            <div class="nav">
                <a href="/users">Users</a>
                <a href="/login">Login</a>
                <a href="/ai-analytics">AI Analytics</a>
            </div>
            <p><strong>Status:</strong> Bot is ready for configuration</p>
            <p><strong>Environment:</strong> Vercel Serverless</p>
            <p><strong>Version:</strong> 2.0.0</p>
        </div>
    </body>
    </html>
    '''

@app.route('/users', methods=['GET'])
def users():
    """Users page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Users - SVN Trading Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .nav { text-align: center; margin: 20px 0; }
            .nav a { margin: 0 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👥 Users Management</h1>
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/login">Login</a>
                <a href="/ai-analytics">AI Analytics</a>
            </div>
            <p>User management functionality will be implemented here.</p>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET'])
def login():
    """Login page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - SVN Trading Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; }
            input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Login</h1>
            <form>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" placeholder="Enter your email">
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" placeholder="Enter your password">
                </div>
                <button type="submit">Login</button>
            </form>
            <p style="text-align: center; margin-top: 20px;">
                <a href="/">← Back to Dashboard</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/ai-analytics', methods=['GET'])
def ai_analytics():
    """AI Analytics page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Analytics - SVN Trading Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .nav { text-align: center; margin: 20px 0; }
            .nav a { margin: 0 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .chart-placeholder { height: 200px; background: #f8f9fa; border: 2px dashed #dee2e6; display: flex; align-items: center; justify-content: center; margin: 20px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 AI Analytics</h1>
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/users">Users</a>
                <a href="/login">Login</a>
            </div>
            <div class="chart-placeholder">
                📈 Trading Analytics Charts will be displayed here
            </div>
            <p><strong>Next Steps:</strong> Integrate with your trading data and ML models.</p>
        </div>
    </body>
    </html>
    '''
