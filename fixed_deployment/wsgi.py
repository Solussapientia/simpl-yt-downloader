#!/usr/bin/python3
import sys
import os

# Add your project directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run() 