#!/usr/bin/env python3
"""
Simple Flask app for shared hosting
"""

import os
import sys
import cgitb

# Enable CGI error reporting
cgitb.enable()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template, request, jsonify
    import subprocess
    import json
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/test')
    def test():
        return "Flask is working!"
    
    if __name__ == '__main__':
        # For CGI
        print("Content-Type: text/html\n")
        app.run()
        
except Exception as e:
    print("Content-Type: text/html\n")
    print(f"<h1>Error: {str(e)}</h1>")
    print(f"<p>Python path: {sys.path}</p>")
    print(f"<p>Current directory: {os.getcwd()}</p>") 