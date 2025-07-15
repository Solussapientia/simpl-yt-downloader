#!/bin/bash

# Railway Build Script for YouTube Downloader
echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Verify installations
echo "✅ Verifying installations..."
python -c "import flask; print('Flask installed successfully')"
python -c "import yt_dlp; print('yt-dlp installed successfully')"
python -c "import gunicorn; print('Gunicorn installed successfully')"

echo "🎉 Build completed successfully!" 