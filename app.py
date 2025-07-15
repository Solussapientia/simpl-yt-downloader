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
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

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

from flask import Flask, render_template, request, jsonify, redirect
import yt_dlp
import re
import time
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_video_info(url):
    """Extract video information including available MP4 formats"""
    try:
        # yt-dlp configuration for better compatibility
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'ios'],
                    'skip': ['dash', 'hls']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract basic video information
            video_info = {
                'id': info.get('id', ''),
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'formats': []
            }
            
            # Process available formats - show multiple quality options
            seen_qualities = set()
            
            # Get various quality MP4 formats
            for fmt in info.get('formats', []):
                # Only MP4 formats
                if fmt.get('ext') != 'mp4':
                    continue
                
                # Skip HLS/M3U8 formats
                if 'hls' in fmt.get('protocol', '').lower() or 'm3u8' in fmt.get('protocol', '').lower():
                    continue
                
                # Get quality info
                height = fmt.get('height', 0)
                width = fmt.get('width', 0)
                filesize = fmt.get('filesize', 0)
                format_id = fmt.get('format_id', '')
                
                # Create quality label
                if height:
                    quality = f"{height}p"
                else:
                    quality = "Standard"
                    
                # Avoid duplicate qualities (only keep the best one for each resolution)
                if quality in seen_qualities:
                    continue
                seen_qualities.add(quality)
                
                # Format file size
                if filesize:
                    size_mb = filesize / (1024 * 1024)
                    size_text = f"{size_mb:.1f}MB"
                else:
                    size_text = "Unknown size"
                
                video_info['formats'].append({
                        'format_id': format_id,
                    'quality': quality,
                    'size': size_text,
                        'height': height,
                    'width': width
                    })
            
            # Sort formats by quality (highest first)
            video_info['formats'].sort(key=lambda x: x['height'], reverse=True)
            
            # If we don't have many formats, add some common ones
            if len(video_info['formats']) < 3:
                # Add some standard format options
                standard_formats = [
                    {'format_id': 'best[height<=1080]', 'quality': '1080p', 'size': 'Best available', 'height': 1080, 'width': 1920},
                    {'format_id': 'best[height<=720]', 'quality': '720p', 'size': 'Good quality', 'height': 720, 'width': 1280},
                    {'format_id': 'best[height<=480]', 'quality': '480p', 'size': 'Medium quality', 'height': 480, 'width': 854},
                    {'format_id': 'best[height<=360]', 'quality': '360p', 'size': 'Standard quality', 'height': 360, 'width': 640},
                    {'format_id': 'worst', 'quality': 'Lowest', 'size': 'Smallest size', 'height': 240, 'width': 426}
                ]
                
                # Add formats that don't exist yet
                existing_qualities = {f['quality'] for f in video_info['formats']}
                for std_fmt in standard_formats:
                    if std_fmt['quality'] not in existing_qualities:
                        video_info['formats'].append(std_fmt)
                
                # Re-sort by quality
                video_info['formats'].sort(key=lambda x: x['height'], reverse=True)
            
            return video_info
            
    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        return None

def get_download_url(video_url, format_id):
    """Get fresh download URL for a specific format"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': format_id,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'ios'],
                    'skip': ['dash', 'hls']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # For format selectors like 'best[height<=720]', get the selected format
            if 'requested_formats' in info and info['requested_formats']:
                # Multiple formats selected (video + audio)
                for fmt in info['requested_formats']:
                    if fmt.get('url'):
                        return fmt.get('url')
            
            # Single format selected
            if 'url' in info:
                return info['url']
            
            # Fallback: try to find by format_id for simple IDs like '18'
            for fmt in info.get('formats', []):
                if fmt.get('format_id') == format_id:
                    return fmt.get('url')
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting download URL: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return "<h1>Flask app is working!</h1>"

@app.route('/debug')
def debug():
    import os
    return f"""
    <h1>Debug Info</h1>
    <p>Flask app is running!</p>
    <p>PORT: {os.environ.get('PORT', 'Not set')}</p>
    <p>Python version: {os.environ.get('PYTHON_VERSION', 'Not set')}</p>
    <p>Current directory: {os.getcwd()}</p>
    <p>Templates directory exists: {os.path.exists('templates')}</p>
    """

@app.route('/minimal')
def minimal():
    return "<h1>MINIMAL TEST</h1><p>This is the simplest possible route.</p>"

@app.route('/simple')
def simple():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Test</title>
        <style>
            body { background: #1a1a1a; color: white; font-family: Arial; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #0ea5e9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Simpl YT Downloader - Simple Test Page</h1>
            <p>This is a minimal test page to verify the Flask app is working.</p>
            <p>If you see this, the Flask app is running correctly!</p>
        </div>
    </body>
    </html>
    """

@app.route('/extract', methods=['POST'])
def extract():
    """Extract video information"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Basic URL validation
        if not ('youtube.com' in url or 'youtu.be' in url):
            return jsonify({'error': 'Please enter a valid YouTube URL'}), 400
            
        # Extract video information
        video_info = extract_video_info(url)
        
        if not video_info:
            return jsonify({'error': 'Could not extract video information'}), 500
            
        # Add extraction timestamp and original URL
        video_info['original_url'] = url
        video_info['extracted_at'] = time.time()
        
        return jsonify({
            'success': True,
            'video': video_info
        })
        
    except Exception as e:
        logger.error(f"Error in extract endpoint: {str(e)}")
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/download/<video_id>/<format_id>')
def download(video_id, format_id):
    """Get direct download URL and redirect"""
    try:
        # Reconstruct YouTube URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Get fresh download URL
        download_url = get_download_url(video_url, format_id)
        
        if not download_url:
            return jsonify({'error': 'Could not get download URL'}), 500
            
        # Redirect to the direct YouTube URL
        return redirect(download_url)
        
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}")
        return jsonify({'error': 'Server error occurred'}), 500

# ================================
# SEO and Marketing Routes
# ================================

@app.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap.xml for SEO"""
    try:
        # Create root element
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Define base URL
        base_url = request.host_url.rstrip('/')
        
        # Main pages
        pages = [
            {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
            {'loc': '/about', 'priority': '0.8', 'changefreq': 'weekly'},
            {'loc': '/privacy', 'priority': '0.7', 'changefreq': 'monthly'},
            {'loc': '/terms', 'priority': '0.7', 'changefreq': 'monthly'},
        ]
        
        # Add URLs to sitemap
        for page in pages:
            url = SubElement(urlset, 'url')
            
            loc = SubElement(url, 'loc')
            loc.text = f"{base_url}{page['loc']}"
            
            lastmod = SubElement(url, 'lastmod')
            lastmod.text = datetime.now().strftime('%Y-%m-%d')
            
            changefreq = SubElement(url, 'changefreq')
            changefreq.text = page['changefreq']
            
            priority = SubElement(url, 'priority')
            priority.text = page['priority']
        
        # Convert to string and format
        rough_string = tostring(urlset, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        
        response = Response(reparsed.toprettyxml(indent="  "), mimetype='application/xml')
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        return "Error generating sitemap", 500

@app.route('/robots.txt')
def robots_txt():
    """Generate robots.txt for SEO"""
    try:
        base_url = request.host_url.rstrip('/')
        
        robots_content = f"""User-agent: *
Allow: /
Disallow: /downloads/
Disallow: /static/
Disallow: /progress/
Disallow: /download/

# Sitemap
Sitemap: {base_url}/sitemap.xml

# Crawl-delay for being respectful
Crawl-delay: 1

# Allow major search engines
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /

User-agent: facebookexternalhit
Allow: /

User-agent: Twitterbot
Allow: /
"""
        
        response = Response(robots_content, mimetype='text/plain')
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error(f"Error generating robots.txt: {str(e)}")
        return "Error generating robots.txt", 500

@app.route('/about')
def about():
    """About page with SEO content"""
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@app.route('/humans.txt')
def humans_txt():
    """Humans.txt file for giving credit to developers"""
    humans_content = """/* TEAM */
    Developer: Simpl YT Downloader Team
    Site: https://simpl-yt-downloader.up.railway.app/
    Location: Global

/* THANKS */
    YouTube-dl community
    yt-dlp developers
    Flask framework
    TailwindCSS
    FontAwesome

/* SITE */
    Last update: 2024/01/15
    Language: English
    Doctype: HTML5
    IDE: Visual Studio Code
    
/* TECHNOLOGY */
    Python, Flask, yt-dlp, TailwindCSS, HTML5, JavaScript
    Hosted on Railway
    
/* CONTACT */
    Email: support@simpl-yt-downloader.com
    Twitter: @SimplYTDownloader
"""
    
    response = Response(humans_content, mimetype='text/plain')
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

@app.route('/ads.txt')
def ads_txt():
    """Ads.txt file for ad network verification"""
    ads_content = """# ads.txt file for Simpl YT Downloader
# This file is used to authorize digital ad sellers

# Google AdSense (example - replace with actual if using)
# google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0

# Currently no ads running - keeping file for future use
# Add your ad network entries here when implementing monetization
"""
    
    response = Response(ads_content, mimetype='text/plain')
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

@app.route('/manifest.json')
def manifest():
    """Progressive Web App manifest"""
    manifest_data = {
        "name": "Simpl YT Downloader",
        "short_name": "YT Downloader",
        "description": "Free YouTube video downloader with beautiful interface",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#111827",
        "theme_color": "#0ea5e9",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/images/favicon-16x16.png",
                "sizes": "16x16",
                "type": "image/png"
            },
            {
                "src": "/static/images/favicon-32x32.png",
                "sizes": "32x32",
                "type": "image/png"
            },
            {
                "src": "/static/images/apple-touch-icon.png",
                "sizes": "180x180",
                "type": "image/png"
            },
            {
                "src": "/static/images/android-chrome-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/android-chrome-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["utilities", "multimedia", "productivity"],
        "lang": "en-US",
        "dir": "ltr",
        "scope": "/",
        "prefer_related_applications": False
    }
    
    response = Response(json.dumps(manifest_data, indent=2), mimetype='application/json')
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# Add security headers for SEO and security
@app.after_request
def after_request(response):
    """Add security and SEO headers"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Performance headers
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    # Compression
    if response.content_type.startswith('text/') or response.content_type.startswith('application/json'):
        response.headers['Content-Encoding'] = 'gzip'
    
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port) 