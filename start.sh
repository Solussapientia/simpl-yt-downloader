#!/bin/bash

# Set default port if not provided
PORT=${PORT:-8000}

echo "Starting server on port $PORT"

# Start gunicorn with the correct port
exec gunicorn --bind 0.0.0.0:$PORT app:app 