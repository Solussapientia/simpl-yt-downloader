#!/bin/bash
echo "🔧 Installing FFmpeg for Railway deployment..."

# Update package list
apt-get update

# Install ffmpeg
apt-get install -y ffmpeg

# Verify installation
ffmpeg -version

echo "✅ FFmpeg installation complete!"

# Install Python dependencies
pip install -r requirements.txt

echo "🎉 Build process complete!" 