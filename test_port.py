#!/usr/bin/env python3
import os

# Test PORT environment variable handling
port = os.environ.get("PORT")
print(f"PORT environment variable: {port}")

if port:
    try:
        port_int = int(port)
        print(f"PORT as integer: {port_int}")
        print("✅ PORT handling works correctly")
    except ValueError:
        print(f"❌ PORT is not a valid integer: {port}")
else:
    print("⚠️  PORT environment variable not set")
    default_port = 8000
    print(f"Using default port: {default_port}") 