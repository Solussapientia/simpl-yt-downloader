#!/bin/bash
echo "🚀 Starting Simpl YT Downloader..."

# Check if ffmpeg is available
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is available!"
    ffmpeg -version | head -n 1
else
    echo "⚠️ FFmpeg not found, installing..."
    apt-get update && apt-get install -y ffmpeg
fi

# Get PORT from environment, default to 8000 if not set
PORT=${PORT:-8000}
echo "🔧 Using PORT: $PORT"

# Start the application with proper port binding
echo "🎬 Starting YouTube downloader..."
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300 