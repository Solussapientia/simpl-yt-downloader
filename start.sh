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

# Start the application
echo "🎬 Starting YouTube downloader..."
gunicorn wsgi:app 