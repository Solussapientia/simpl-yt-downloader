#!/usr/bin/python3
import sys
import os

# Add your project directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def main():
    # Get PORT from environment with detailed logging
    port_env = os.environ.get("PORT")
    print(f"PORT environment variable: '{port_env}'")
    print(f"PORT type: {type(port_env)}")
    
    # Handle PORT conversion with error handling
    if port_env:
        try:
            port = int(port_env)
            print(f"✅ Successfully converted PORT to integer: {port}")
        except ValueError as e:
            print(f"❌ ERROR: Invalid PORT value '{port_env}': {e}")
            print("Using default port 8000")
            port = 8000
    else:
        port = 8000
        print(f"⚠️  No PORT specified, using default: {port}")
    
    # Start the application
    print(f"🚀 Starting Flask app on 0.0.0.0:{port}")
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 