import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request
from flask_cors import CORS

app = Flask(__name__, 
           static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
           template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
CORS(app)

@app.route('/', methods=['GET'])
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/users', methods=['GET'])
def users():
    """Users page"""
    return render_template('users.html')

@app.route('/login', methods=['GET'])
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/ai-analytics', methods=['GET'])
def ai_analytics():
    """AI Analytics page"""
    # For now, redirect to dashboard
    return render_template('dashboard.html')

# Serverless function handler
def handler(request):
    return app(request.environ, lambda *args: None)
