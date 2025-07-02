#!/usr/bin/env python3
"""
Simple test server for SecureDeal app
"""

from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-for-testing'
app.template_folder = 'app/templates'
app.static_folder = 'app/static'

# Disable CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth/login')
def login():
    return render_template('auth/login.html')

@app.route('/auth/register') 
def register():
    return render_template('auth/register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/contracts')
def contracts():
    return redirect('/dashboard')

@app.route('/invitations')
def invitations():
    return redirect('/dashboard')

@app.route('/docs')
def docs():
    return redirect('/dashboard')

@app.route('/contracts/create')
def create_contract():
    return redirect('/dashboard')

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('app/static', filename)

# Mock API endpoints (just return success)
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    return jsonify({
        'message': 'User registered successfully',
        'user': {'email': 'test@example.com'},
        'token': 'mock-token-123'
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    return jsonify({
        'message': 'Login successful',
        'user': {'email': 'test@example.com'},
        'token': 'mock-token-123'
    }), 200

if __name__ == '__main__':
    print("🚀 Starting SecureDeal Test Server...")
    print("📱 Visit http://localhost:5000 to test the app")
    print("✅ Login/Register flow is now working!")
    print("🔄 Use any email/password to test - it will redirect to dashboard")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
