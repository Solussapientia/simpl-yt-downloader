#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import random
import requests
import threading
import uuid
import re
import subprocess
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, parse_qs

# Import yt-dlp with fallback
try:
    import yt_dlp
except ImportError:
    print("yt-dlp not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

app = Flask(__name__)

# Global variables
download_progress = {}
active_downloads = {}

# Multiple proxy configurations for rotation
PROXY_LIST = [
    # You can add residential proxies here if available
    # Format: "http://username:password@proxy-host:port"
]

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
]

class ProgressHook:
    def __init__(self, download_id):
        self.download_id = download_id
        self.last_update = time.time()

    def __call__(self, d):
        current_time = time.time()
        # Update progress at most once per second
        if current_time - self.last_update < 1.0:
            return
        self.last_update = current_time
        
        status = d.get('status', 'unknown')
        
        if status == 'downloading':
            percent = d.get('_percent_str', '0%').replace('%', '')
            try:
                percent = float(percent)
            except:
                percent = 0
            
            speed = d.get('_speed_str', '0 B/s') or '0 B/s'
            eta = d.get('_eta_str', 'Unknown') or 'Unknown'
            
            # Handle file size
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total_bytes:
                file_size = f"{total_bytes / (1024*1024):.1f} MB"
            else:
                file_size = "-- MB"
            
            download_progress[self.download_id] = {
                'status': 'downloading',
                'percent': percent,
                'speed_text': speed,
                'eta_text': eta,
                'file_size': file_size,
                'downloaded': d.get('downloaded_bytes', 0),
                'total': total_bytes,
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0)
            }
        elif status == 'finished':
            download_progress[self.download_id] = {
                'status': 'processing',
                'percent': 100,
                'speed_text': 'Processing...',
                'eta_text': 'Almost done',
                'file_size': 'Processing'
            }

def get_video_info_alternative(url):
    """Alternative method using different approaches to get video info"""
    
    # Method 1: Try multiple yt-dlp configurations
    configs = [
        # Configuration 1: Use different extractors
        {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': random.choice(USER_AGENTS),
            'headers': {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'],
                    'player_skip': ['dash', 'hls'],
                    'include_live_dash': False,
                }
            }
        },
        # Configuration 2: Try web client
        {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                }
            }
        },
        # Configuration 3: Try with different approach
        {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android'],
                }
            }
        }
    ]
    
    for i, config in enumerate(configs):
        try:
            print(f"Trying configuration {i+1}/3...")
            
            # Add random delay to avoid rate limiting
            if i > 0:
                time.sleep(random.uniform(2, 5))
            
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info and 'formats' in info:
                    print(f"Success with configuration {i+1}")
                    return process_video_info(info)
                    
        except Exception as e:
            print(f"Configuration {i+1} failed: {e}")
            continue
    
    # Method 2: Try alternative approach using requests
    try:
        return get_video_info_from_page_source(url)
    except Exception as e:
        print(f"Page source method failed: {e}")
    
    # Method 3: Try with proxy if available
    if PROXY_LIST:
        try:
            return get_video_info_with_proxy(url)
        except Exception as e:
            print(f"Proxy method failed: {e}")
    
    raise Exception("All video info extraction methods failed")

def get_video_info_from_page_source(url):
    """Extract video info from page source - alternative method"""
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Extract video ID from URL
        video_id = None
        if 'youtube.com/watch' in url:
            parsed_url = urlparse(url)
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0]
        
        if not video_id:
            raise Exception("Could not extract video ID")
        
        # Try to extract basic info from page source
        html_content = response.text
        
        # Look for video title
        title_match = re.search(r'"title":"([^"]+)"', html_content)
        title = title_match.group(1) if title_match else "Unknown Video"
        
        # Create basic format list
        formats = [
            {
                'format_id': 'best',
                'ext': 'mp4',
                'format_note': 'Best Quality Available',
                'resolution': 'Best',
                'filesize': None,
                'tbr': None,
                'vcodec': 'unknown',
                'acodec': 'unknown'
            },
            {
                'format_id': 'worst',
                'ext': 'mp4',
                'format_note': 'Lowest Quality',
                'resolution': 'Lowest',
                'filesize': None,
                'tbr': None,
                'vcodec': 'unknown',
                'acodec': 'unknown'
            }
        ]
        
        return {
            'video_formats': formats,
            'audio_formats': [
                {
                    'format_id': 'bestaudio',
                    'ext': 'mp3',
                    'format_note': 'Best Audio Quality',
                    'abr': 'Best',
                    'filesize': None,
                    'acodec': 'mp3'
                }
            ],
            'title': title,
            'duration': None,
            'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        }
        
    except Exception as e:
        raise Exception(f"Page source extraction failed: {e}")

def get_video_info_with_proxy(url):
    """Try to get video info using proxy"""
    proxy = random.choice(PROXY_LIST)
    
    config = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'proxy': proxy,
        'user_agent': random.choice(USER_AGENTS),
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
            }
        }
    }
    
    with yt_dlp.YoutubeDL(config) as ydl:
        info = ydl.extract_info(url, download=False)
        return process_video_info(info)

def process_video_info(info):
    """Process video info and return formatted data"""
    video_formats = []
    audio_formats = []
    
    formats = info.get('formats', [])
    
    for fmt in formats:
        format_info = {
            'format_id': fmt.get('format_id', 'unknown'),
            'ext': fmt.get('ext', 'unknown'),
            'format_note': fmt.get('format_note', ''),
            'filesize': fmt.get('filesize'),
            'tbr': fmt.get('tbr'),
            'vcodec': fmt.get('vcodec', 'none'),
            'acodec': fmt.get('acodec', 'none'),
            'resolution': fmt.get('resolution', 'unknown'),
            'fps': fmt.get('fps'),
            'abr': fmt.get('abr'),
            'height': fmt.get('height'),
            'width': fmt.get('width')
        }
        
        # Categorize formats
        if fmt.get('vcodec') != 'none' and fmt.get('vcodec') != None:
            video_formats.append(format_info)
        elif fmt.get('acodec') != 'none' and fmt.get('acodec') != None:
            audio_formats.append(format_info)
    
    # Sort formats by quality
    video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
    audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
    
    return {
        'video_formats': video_formats,
        'audio_formats': audio_formats,
        'title': info.get('title', 'Unknown'),
        'duration': info.get('duration'),
        'thumbnail': info.get('thumbnail', '')
    }

def download_with_multiple_strategies(url, format_id, download_id):
    """Try multiple download strategies"""
    
    downloads_dir = 'downloads'
    os.makedirs(downloads_dir, exist_ok=True)
    
    # Strategy 1: Try with different yt-dlp configurations
    strategies = [
        # Strategy 1: Android client
        {
            'format': format_id,
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'no_warnings': True,
            'overwrites': True,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'http_headers': {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
        },
        # Strategy 2: iOS client
        {
            'format': format_id,
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'no_warnings': True,
            'overwrites': True,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                }
            },
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
        },
        # Strategy 3: Web client with different settings
        {
            'format': format_id,
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'no_warnings': True,
            'overwrites': True,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                }
            },
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
        }
    ]
    
    # Try each strategy
    for i, strategy in enumerate(strategies):
        try:
            print(f"Trying download strategy {i+1}/{len(strategies)}")
            
            # Add progress hook
            progress_hook = ProgressHook(download_id)
            strategy['progress_hooks'] = [progress_hook]
            
            # Add random delay between attempts
            if i > 0:
                time.sleep(random.uniform(3, 7))
            
            # Update progress
            download_progress[download_id] = {
                'status': 'downloading',
                'percent': 0,
                'speed_text': f'Trying method {i+1}...',
                'eta_text': 'Calculating...',
                'file_size': '-- MB'
            }
            
            with yt_dlp.YoutubeDL(strategy) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Find the downloaded file
                title = info.get('title', 'Unknown')
                expected_filename = f"{title}.{info.get('ext', 'mp4')}"
                
                # Look for files that match the title
                for filename in os.listdir(downloads_dir):
                    if title.replace('/', '_').replace('\\', '_') in filename:
                        file_path = os.path.join(downloads_dir, filename)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            file_size = os.path.getsize(file_path)
                            print(f"Download completed: {filename} ({file_size} bytes)")
                            
                            # Mark as completed
                            download_progress[download_id] = {
                                'status': 'completed',
                                'percent': 100,
                                'filename': filename,
                                'total': file_size,
                                'speed': 0,
                                'eta': 0,
                                'speed_text': 'Completed',
                                'eta_text': 'Done',
                                'file_size': f"{file_size / (1024*1024):.1f} MB"
                            }
                            return True
                
        except Exception as e:
            print(f"Strategy {i+1} failed: {e}")
            continue
    
    # Try with proxy if available
    if PROXY_LIST:
        try:
            return download_with_proxy(url, format_id, download_id)
        except Exception as e:
            print(f"Proxy download failed: {e}")
    
    # If all strategies fail, try alternative download method
    try:
        return download_with_alternative_method(url, format_id, download_id)
    except Exception as e:
        print(f"Alternative download method failed: {e}")
    
    return False

def download_with_proxy(url, format_id, download_id):
    """Download using proxy"""
    proxy = random.choice(PROXY_LIST)
    
    config = {
        'format': format_id,
        'outtmpl': os.path.join('downloads', '%(title)s.%(ext)s'),
        'no_warnings': True,
        'overwrites': True,
        'proxy': proxy,
        'user_agent': random.choice(USER_AGENTS),
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
            }
        },
        'progress_hooks': [ProgressHook(download_id)],
        'retries': 5,
        'fragment_retries': 5,
        'skip_unavailable_fragments': True,
    }
    
    with yt_dlp.YoutubeDL(config) as ydl:
        info = ydl.extract_info(url, download=True)
        return True

def download_with_alternative_method(url, format_id, download_id):
    """Alternative download method using different approach"""
    try:
        # Update progress
        download_progress[download_id] = {
            'status': 'downloading',
            'percent': 0,
            'speed_text': 'Using alternative method...',
            'eta_text': 'Calculating...',
            'file_size': '-- MB'
        }
        
        # Try using youtube-dl as fallback
        cmd = [
            'youtube-dl',
            '--format', format_id,
            '--output', os.path.join('downloads', '%(title)s.%(ext)s'),
            '--user-agent', random.choice(USER_AGENTS),
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Find the downloaded file
            for filename in os.listdir('downloads'):
                file_path = os.path.join('downloads', filename)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    file_size = os.path.getsize(file_path)
                    
                    download_progress[download_id] = {
                        'status': 'completed',
                        'percent': 100,
                        'filename': filename,
                        'total': file_size,
                        'speed': 0,
                        'eta': 0,
                        'speed_text': 'Completed',
                        'eta_text': 'Done',
                        'file_size': f"{file_size / (1024*1024):.1f} MB"
                    }
                    return True
        
        return False
        
    except Exception as e:
        print(f"Alternative method failed: {e}")
        return False

def download_thread_func(url, format_id, download_id):
    """Main download thread function"""
    try:
        # Initialize progress
        download_progress[download_id] = {
            'status': 'starting',
            'percent': 0,
            'speed_text': "Starting...",
            'eta_text': "Calculating...",
            'file_size': "-- MB"
        }
        
        # Try multiple download strategies
        success = download_with_multiple_strategies(url, format_id, download_id)
        
        if not success:
            raise Exception("All download methods failed")
            
    except Exception as e:
        print(f"Download failed: {e}")
        
        # Create user-friendly error message
        error_str = str(e).lower()
        if "403" in error_str or "forbidden" in error_str:
            user_error = "YouTube is blocking downloads from this server. This is a common issue with hosting providers. Try: 1) Wait 15-30 minutes, 2) Try a different video, 3) The server IP may be blacklisted by YouTube."
        elif "failed to extract any player response" in error_str:
            user_error = "YouTube is completely blocking video information extraction from this server. This is a severe anti-bot measure. Try: 1) Wait 15-30 minutes, 2) Try a different video, 3) This server IP may be blacklisted by YouTube."
        elif "sign in" in error_str or "confirm you're not a bot" in error_str:
            user_error = "YouTube is asking for sign-in verification. This happens when they detect automated downloads. Please wait 10-15 minutes and try again."
        elif "unavailable" in error_str or "not available" in error_str:
            user_error = "This video is not available for download. It might be private, deleted, or restricted in your region."
        elif "network" in error_str or "connection" in error_str:
            user_error = "Network connection error. Please check your internet connection and try again."
        else:
            user_error = f"Download failed: {str(e)}"
        
        download_progress[download_id] = {
            'status': 'error',
            'percent': 0,
            'error': user_error,
            'speed_text': "Error",
            'eta_text': "Failed",
            'file_size': "-- MB"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Try alternative video info extraction
        result = get_video_info_alternative(url)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_video_info: {e}")
        
        # Provide user-friendly error messages for common extraction failures
        error_str = str(e).lower()
        if "failed to extract any player response" in error_str:
            user_error = "YouTube is completely blocking video information extraction from this server. This is a severe anti-bot measure. Please try: 1) Wait 15-30 minutes before trying again, 2) Try a different video, 3) This server IP may be blacklisted by YouTube."
        elif "sign in" in error_str or "confirm you're not a bot" in error_str:
            user_error = "YouTube is asking for sign-in verification. This happens when they detect automated access. Please wait 10-15 minutes and try again."
        elif "unavailable" in error_str or "not available" in error_str:
            user_error = "This video is not available for extraction. It might be private, deleted, or restricted in your region."
        elif "network" in error_str or "connection" in error_str:
            user_error = "Network connection error. Please check your connection and try again."
        else:
            user_error = f"Could not extract video information: {str(e)}"
        
        return jsonify({'error': user_error}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id')
        
        if not url or not format_id:
            return jsonify({'error': 'URL and format_id are required'}), 400
        
        # Generate unique download ID
        download_id = str(int(time.time() * 1000))
        
        # Start download in separate thread
        thread = threading.Thread(
            target=download_thread_func,
            args=(url, format_id, download_id)
        )
        thread.daemon = True
        thread.start()
        
        active_downloads[download_id] = thread
        
        return jsonify({
            'download_id': download_id,
            'message': 'Download started'
        })
        
    except Exception as e:
        print(f"Error in download: {e}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/progress/<download_id>')
def get_progress(download_id):
    progress = download_progress.get(download_id, {'status': 'not_found'})
    print(f"Progress request for {download_id}: {progress}")  # Debug log
    
    # Format the progress data for frontend consumption
    if progress['status'] in ['downloading', 'processing']:
        # Ensure all required fields are present
        progress.setdefault('percent', 0)
        progress.setdefault('speed_text', 'Calculating...')
        progress.setdefault('eta_text', 'Calculating...')
        progress.setdefault('file_size', '-- MB')
        progress.setdefault('downloaded', 0)
        progress.setdefault('total', 0)
        progress.setdefault('speed', 0)
        progress.setdefault('eta', 0)
    
    return jsonify(progress)

@app.route('/download_file/<download_id>')
def download_file(download_id):
    """Download file by download_id"""
    try:
        downloads_dir = 'downloads'
        
        # Debug: Print all available progress data
        print(f"Download request for ID: {download_id}")
        print(f"Available progress entries: {list(download_progress.keys())}")
        
        progress = download_progress.get(download_id)
        if not progress:
            print(f"No progress found for download_id: {download_id}")
            return jsonify({'error': 'Download not found'}), 404
        
        print(f"Progress status: {progress.get('status')}")
        
        if progress['status'] not in ['finished', 'completed']:
            print(f"Download not completed, status: {progress['status']}")
            return jsonify({'error': 'Download not completed'}), 400
        
        filename = progress.get('filename')
        if not filename:
            print("No filename in progress data")
            return jsonify({'error': 'No filename available'}), 400
        
        full_path = os.path.join(downloads_dir, filename)
        print(f"Looking for file: {full_path}")
        
        if os.path.exists(full_path):
            print(f"File found, sending: {full_path}")
            return send_file(full_path, as_attachment=True)
        else:
            print(f"File not found: {full_path}")
            # Try to find file by partial matching
            if os.path.exists(downloads_dir):
                files = os.listdir(downloads_dir)
                print(f"Available files: {files}")
                
                # Try fuzzy matching
                for file in files:
                    if filename.lower() in file.lower() or file.lower() in filename.lower():
                        fuzzy_path = os.path.join(downloads_dir, file)
                        print(f"Found fuzzy match: {fuzzy_path}")
                        return send_file(fuzzy_path, as_attachment=True)
            
            return jsonify({'error': f'File not found: {filename}'}), 404
            
    except Exception as e:
        print(f"Error in download_file: {e}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 