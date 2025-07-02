#!/usr/bin/env python3

from flask import Flask, render_template, jsonify, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-for-testing'

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
    return render_template('dashboard_simple.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('app/static', filename)

if __name__ == '__main__':
    # Set template folder
    app.template_folder = 'app/templates'
    app.static_folder = 'app/static'
    
    print("Starting simple Flask server...")
    print("Visit http://localhost:5000 to test the app")
    app.run(debug=True, host='0.0.0.0', port=5000)
