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
from flask import Flask, render_template, request, jsonify, send_file, Response, redirect, url_for
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
            
            # Format speed properly
            speed_raw = d.get('speed', 0)
            if speed_raw:
                if speed_raw > 1024 * 1024:  # MB/s
                    speed_text = f"{speed_raw / (1024*1024):.1f} MB/s"
                elif speed_raw > 1024:  # KB/s
                    speed_text = f"{speed_raw / 1024:.1f} KB/s"
                else:  # B/s
                    speed_text = f"{speed_raw:.0f} B/s"
            else:
                speed_text = d.get('_speed_str', '0 B/s') or '0 B/s'
            
            # Format ETA
            eta_raw = d.get('eta', 0)
            if eta_raw:
                if eta_raw > 3600:  # Hours
                    hours = int(eta_raw // 3600)
                    minutes = int((eta_raw % 3600) // 60)
                    eta_text = f"{hours}h {minutes}m"
                elif eta_raw > 60:  # Minutes
                    minutes = int(eta_raw // 60)
                    seconds = int(eta_raw % 60)
                    eta_text = f"{minutes}m {seconds}s"
                else:  # Seconds
                    eta_text = f"{int(eta_raw)}s"
            else:
                eta_text = d.get('_eta_str', 'Unknown') or 'Unknown'
            
            # Handle file size
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total_bytes:
                file_size = f"{total_bytes / (1024*1024):.1f} MB"
            else:
                file_size = "-- MB"
            
            download_progress[self.download_id] = {
                'status': 'downloading',
                'percent': percent,
                'speed_text': speed_text,
                'eta_text': eta_text,
                'file_size': file_size,
                'downloaded': d.get('downloaded_bytes', 0),
                'total': total_bytes,
                'speed': speed_raw,
                'eta': eta_raw
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
    
    # Method 1: Try fastest configuration first
    configs = [
        # Configuration 1: Android client - fastest and most reliable
        {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 10,  # Faster timeout
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'include_live_dash': False,
                }
            }
        },
        # Configuration 2: iOS client - backup
        {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 10,
            'user_agent': random.choice(USER_AGENTS),
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                }
            }
        }
    ]
    
    for i, config in enumerate(configs):
        try:
            print(f"Trying configuration {i+1}/2...")
            
            # Add shorter delay
            if i > 0:
                time.sleep(1)
            
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info and 'formats' in info:
                    print(f"Success with configuration {i+1}")
                    return process_video_info(info)
                    
        except Exception as e:
            print(f"Configuration {i+1} failed: {e}")
            continue
    
    # Method 2: Try page source as faster fallback
    try:
        print("Trying page source method...")
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
        
        # Create basic format list with display names
        video_formats = [
            {
                'format_id': 'best',
                'ext': 'mp4',
                'display_name': 'Best Quality Available (MP4)',
                'height': 1080,
                'vcodec': 'h264',
                'acodec': 'aac'
            },
            {
                'format_id': 'worst',
                'ext': 'mp4',
                'display_name': 'Lowest Quality (MP4)',
                'height': 360,
                'vcodec': 'h264',
                'acodec': 'aac'
            }
        ]
        
        audio_formats = [
            {
                'format_id': 'bestaudio',
                'ext': 'mp3',
                'display_name': 'Best Audio Quality (MP3)',
                'abr': 192,
                'acodec': 'mp3'
            }
        ]
        
        return {
            'video_formats': video_formats,
            'audio_formats': audio_formats,
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
        format_id = fmt.get('format_id', 'unknown')
        ext = fmt.get('ext', 'unknown')
        height = fmt.get('height')
        width = fmt.get('width')
        fps = fmt.get('fps')
        filesize = fmt.get('filesize')
        tbr = fmt.get('tbr')
        abr = fmt.get('abr')
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        
        # Create format info structure
        format_info = {
            'format_id': format_id,
            'ext': ext,
            'format_note': fmt.get('format_note', ''),
            'filesize': filesize,
            'tbr': tbr,
            'vcodec': vcodec,
            'acodec': acodec,
            'resolution': fmt.get('resolution', 'unknown'),
            'fps': fps,
            'abr': abr,
            'height': height,
            'width': width
        }
        
        # Categorize and create display names
        if vcodec != 'none' and vcodec != None and height:
            # Video format
            display_name = f"{height}p"
            if ext:
                display_name += f" ({ext.upper()})"
            if fps and fps > 30:
                display_name += f" {int(fps)}fps"
            if filesize:
                size_mb = filesize / (1024 * 1024)
                display_name += f" - {size_mb:.1f}MB"
            elif tbr:
                display_name += f" - {tbr:.0f}kbps"
            
            format_info['display_name'] = display_name
            video_formats.append(format_info)
            
        elif acodec != 'none' and acodec != None and vcodec == 'none':
            # Audio format
            display_name = "Audio Only"
            if ext:
                display_name += f" ({ext.upper()})"
            if abr:
                display_name += f" - {abr:.0f}kbps"
            elif tbr:
                display_name += f" - {tbr:.0f}kbps"
            if filesize:
                size_mb = filesize / (1024 * 1024)
                display_name += f" - {size_mb:.1f}MB"
            
            format_info['display_name'] = display_name
            audio_formats.append(format_info)
    
    # Sort formats by quality
    video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
    audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
    
    # Add fallback formats if none found
    if not video_formats:
        video_formats = [
            {
                'format_id': 'best',
                'ext': 'mp4',
                'display_name': 'Best Quality Available',
                'height': 1080,
                'vcodec': 'h264',
                'acodec': 'aac'
            },
            {
                'format_id': 'worst',
                'ext': 'mp4',
                'display_name': 'Lowest Quality',
                'height': 360,
                'vcodec': 'h264',
                'acodec': 'aac'
            }
        ]
    
    if not audio_formats:
        audio_formats = [
            {
                'format_id': 'bestaudio',
                'ext': 'mp3',
                'display_name': 'Best Audio Quality',
                'abr': 192,
                'acodec': 'mp3'
            }
        ]
    
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

def download_video_direct(url, format_id, download_id):
    """Extract direct download URL without downloading to server"""
    try:
        download_progress[download_id] = {
            'status': 'extracting',
            'percent': 0,
            'message': 'Extracting download URL...'
        }
        
        # Enhanced yt-dlp options for direct URL extraction
        ydl_opts = {
            'format': format_id,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'dump_single_json': True,
            'no_download': True,  # Don't download, just extract info
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android'],
                    'player_skip': ['webpage', 'configs'],
                }
            }
        }
        
        # Try multiple configurations
        configs = [
            ydl_opts,
            {**ydl_opts, 'extractor_args': {'youtube': {'player_client': ['ios']}}},
            {**ydl_opts, 'extractor_args': {'youtube': {'player_client': ['android']}}},
            {**ydl_opts, 'extractor_args': {'youtube': {'player_client': ['web']}}},
        ]
        
        info = None
        for config in configs:
            try:
                with yt_dlp.YoutubeDL(config) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info and 'url' in info:
                        break
            except Exception as e:
                continue
        
        if not info:
            raise Exception("Could not extract video information")
        
        # Get the direct URL
        direct_url = info.get('url')
        if not direct_url:
            raise Exception("Could not extract direct download URL")
        
        # Get file info
        title = info.get('title', 'video')
        ext = info.get('ext', 'mp4')
        filesize = info.get('filesize') or info.get('filesize_approx', 0)
        
        # Clean filename
        filename = f"{title}.{ext}"
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename[:200]  # Limit length
        
        # Determine content type
        content_type_map = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mkv': 'video/x-matroska',
            'mp3': 'audio/mpeg',
            'aac': 'audio/aac',
            'ogg': 'audio/ogg',
            'm4a': 'audio/mp4',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        
        # Update progress
        download_progress[download_id] = {
            'status': 'ready_for_download',
            'percent': 100,
            'message': 'Ready for download',
            'filename': filename,
            'direct_url': direct_url,
            'content_type': content_type,
            'filesize': filesize,
            'title': title
        }
        
    except Exception as e:
        download_progress[download_id] = {
            'status': 'error',
            'error': str(e),
            'percent': 0
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
        if not request.json:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        url = request.json.get('url')
        format_id = request.json.get('format_id')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Generate unique download ID
        download_id = str(int(time.time() * 1000))
        
        # Start extraction in background thread
        thread = threading.Thread(target=download_video_direct, args=(url, format_id, download_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'download_id': download_id,
            'message': 'Extracting download URL...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/direct_download/<download_id>')
def direct_download(download_id):
    """Stream download directly to user without storing on server"""
    progress = download_progress.get(download_id)
    if not progress:
        return jsonify({'error': 'Download not found'}), 404
    
    if progress['status'] != 'ready_for_download':
        return jsonify({'error': 'Download not ready'}), 400
    
    try:
        # Get the direct URL from the progress data
        direct_url = progress.get('direct_url')
        if not direct_url:
            return jsonify({'error': 'Direct URL not available'}), 400
        
        # Get filename and content type
        filename = progress.get('filename', 'download')
        content_type = progress.get('content_type', 'application/octet-stream')
        
        # Update progress to downloading
        progress['status'] = 'downloading'
        progress['percent'] = 0
        
        # Stream the file directly from the source
        def generate():
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'identity',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                response = requests.get(direct_url, headers=headers, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress['percent'] = percent
                            progress['downloaded'] = downloaded
                            progress['total'] = total_size
                        yield chunk
                
                # Mark as completed
                progress['status'] = 'completed'
                progress['percent'] = 100
                
            except Exception as e:
                progress['status'] = 'error'
                progress['error'] = str(e)
        
        return Response(
            generate(),
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': content_type,
            }
        )
        
    except Exception as e:
        progress['status'] = 'error'
        progress['error'] = str(e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 