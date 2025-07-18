#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file, url_for, send_from_directory
from datetime import datetime, timedelta
import yt_dlp
import tempfile
import threading
import time
from urllib.parse import urlparse
import re
import glob

app = Flask(__name__)

# Performance and SEO Headers
@app.after_request
def after_request(response):
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    
    # Performance headers
    response.headers['Server'] = 'Simpl YT/1.0'
    response.headers['X-Robots-Tag'] = 'index, follow'
    
    # Static file caching
    if request.endpoint == 'static':
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year for static files
        response.headers['Expires'] = (datetime.utcnow() + timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    elif request.endpoint in ['robots_txt', 'sitemap_xml', 'humans_txt', 'ads_txt']:
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day for SEO files
    elif request.endpoint == 'index':
        response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour for main page
    
    return response

# Global variables
download_progress = {}

# SEO Routes
@app.route('/robots.txt')
def robots_txt():
    response = send_from_directory('.', 'robots.txt')
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/sitemap.xml')
def sitemap_xml():
    response = send_from_directory('.', 'sitemap.xml')
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/humans.txt')
def humans_txt():
    response = send_from_directory('.', 'humans.txt')
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/ads.txt')
def ads_txt():
    response = send_from_directory('.', 'ads.txt')
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/.well-known/security.txt')
def security_txt():
    response = send_from_directory('static/.well-known', 'security.txt')
    response.headers['Content-Type'] = 'text/plain'
    return response

# Content Pages
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    if bytes_value is None or bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def format_speed(speed):
    """Convert speed to human readable format"""
    if speed is None or speed == 0:
        return "0 B/s"
    return f"{format_bytes(speed)}/s"

def format_eta(eta):
    """Convert ETA to human readable format"""
    if eta is None or eta == 0:
        return "0s"
    
    if eta < 60:
        return f"{int(eta)}s"
    elif eta < 3600:
        minutes = int(eta // 60)
        seconds = int(eta % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)
        return f"{hours}h {minutes}m"

class ProgressHook:
    def __init__(self, download_id):
        self.download_id = download_id
        self.last_update = time.time()
        
    def __call__(self, d):
        current_time = time.time()
        
        # Only update every 0.5 seconds to avoid too frequent updates
        if current_time - self.last_update < 0.5:
            return
            
        self.last_update = current_time
        
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            
            if total > 0:
                percent = min(100, (downloaded / total) * 100)
            else:
                percent = 0
                
            # Update progress
            download_progress[self.download_id] = {
                'status': 'downloading',
                'percent': round(percent, 1),
                'downloaded': downloaded,
                'total': total,
                'speed': speed or 0,
                'eta': eta or 0,
                'speed_text': format_speed(speed),
                'eta_text': format_eta(eta),
                'file_size': format_bytes(total) if total > 0 else "-- MB"
            }
            
        elif d['status'] == 'finished':
            # Download finished, but might need processing (like merging)
            download_progress[self.download_id] = {
                'status': 'processing',
                'percent': 99,
                'downloaded': d.get('downloaded_bytes', 0),
                'total': d.get('total_bytes') or d.get('total_bytes_estimate', 0),
                'speed': 0,
                'eta': 0,
                'speed_text': "Processing...",
                'eta_text': "Almost done",
                'file_size': format_bytes(d.get('total_bytes') or d.get('total_bytes_estimate', 0))
            }
            
        elif d['status'] == 'error':
            download_progress[self.download_id] = {
                'status': 'error',
                'percent': 0,
                'error': d.get('error', 'Unknown error'),
                'speed_text': "Error",
                'eta_text': "Failed",
                'file_size': "-- MB"
            }

def is_valid_youtube_url(url):
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return youtube_regex.match(url) is not None

def format_description(format_info):
    """Create a simple resolution string for video format"""
    height = format_info.get('height', 0)
    width = format_info.get('width', 0)
    fps = format_info.get('fps', 0)
    
    if height >= 2160:
        quality = "4K (2160p)"
    elif height >= 1440:
        quality = "2K (1440p)"
    elif height >= 1080:
        quality = "1080p"
    elif height >= 720:
        quality = "720p"
    elif height >= 480:
        quality = "480p"
    elif height >= 360:
        quality = "360p"
    elif height >= 240:
        quality = "240p"
    elif height >= 144:
        quality = "144p"
    else:
        quality = "Unknown Quality"
    
    # Add fps info if available and not standard
    if fps and fps > 30:
        quality += f" {int(fps)}fps"
    
    return quality

def download_thread_func(url, ydl_opts, download_id):
    """Function to handle download in a separate thread"""
    try:
        downloads_dir = 'downloads'
        
        # Initialize progress
        download_progress[download_id] = {
            'status': 'starting',
            'percent': 0,
            'speed_text': "Starting...",
            'eta_text': "Calculating...",
            'file_size': "-- MB"
        }
        
        # Create a progress hook instance
        progress_hook = ProgressHook(download_id)
        ydl_opts['progress_hooks'] = [progress_hook]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First, extract info to get the video title
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            
            # Determine expected file extension based on format type
            format_type = 'mp3' if ydl_opts.get('postprocessors') else 'mp4'
            expected_extension = '.mp3' if format_type == 'mp3' else '.mp4'
            
            # Get list of files before download
            files_before = set()
            if os.path.exists(downloads_dir):
                files_before = set(os.listdir(downloads_dir))
            
            # Update status to show we're starting the download
            download_progress[download_id]['status'] = 'downloading'
            download_progress[download_id]['speed_text'] = "Initializing..."
            
            # Download the video/audio
            ydl.download([url])
        
        # Wait longer for MP3 processing to complete
        if format_type == 'mp3':
            time.sleep(3)  # Extra time for audio conversion
        else:
            time.sleep(1)
        
        # Find the actual file that was created
        final_filename = None
        
        if os.path.exists(downloads_dir):
            files_after = set(os.listdir(downloads_dir))
            
            # First, look for new files with the correct extension
            new_files = files_after - files_before
            for new_file in new_files:
                if new_file.endswith(expected_extension):
                    final_filename = new_file
                    print(f"Found new file with correct extension: {final_filename}")
                    break
            
            # If no new file found, look for existing files that match the title
            if not final_filename:
                # Clean the title for basic matching
                clean_title = re.sub(r'[<>:"/\\|?*？：]', '', video_title)
                
                # Look for files that contain parts of the title with correct extension
                for filename in os.listdir(downloads_dir):
                    if filename.endswith(expected_extension):
                        # Check if the filename contains significant parts of the title
                        filename_clean = re.sub(r'[<>:"/\\|?*？：]', '', filename)
                        title_words = clean_title.split()
                        
                        # If at least 3 words from the title are in the filename, it's likely a match
                        if len(title_words) >= 3:
                            matches = sum(1 for word in title_words if len(word) > 2 and word.lower() in filename_clean.lower())
                            if matches >= 3:
                                final_filename = filename
                                print(f"Found file by title matching: {final_filename}")
                                break
                        elif len(title_words) < 3:
                            # For short titles, be more lenient
                            if clean_title.lower() in filename_clean.lower():
                                final_filename = filename
                                print(f"Found file by title matching (short): {final_filename}")
                                break
        
        # Update progress with completion status
        if final_filename:
            file_path = os.path.join(downloads_dir, final_filename)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                download_progress[download_id] = {
                    'status': 'completed',
                    'percent': 100,
                    'filename': final_filename,
                    'total': file_size,
                    'speed': 0,
                    'eta': 0,
                    'speed_text': "Completed",
                    'eta_text': "Done",
                    'file_size': format_bytes(file_size)
                }
                
                print(f"Download completed: {final_filename} ({file_size} bytes)")
            else:
                print(f"Error: Final file not found: {final_filename}")
                download_progress[download_id] = {
                    'status': 'error',
                    'percent': 0,
                    'error': f'Final file not found: {final_filename}',
                    'speed_text': "Error",
                    'eta_text': "Failed",
                    'file_size': "-- MB"
                }
        else:
            print(f"Error: No downloaded file found for download {download_id}")
            download_progress[download_id] = {
                'status': 'error',
                'percent': 0,
                'error': f'No downloaded file found for download {download_id}',
                'speed_text': "Error",
                'eta_text': "Failed",
                'file_size': "-- MB"
            }
            
    except Exception as e:
        print(f"Error in download_thread_func: {e}")
        download_progress[download_id] = {
            'status': 'error',
            'percent': 0,
            'error': str(e),
            'speed_text': "Error",
            'eta_text': "Failed",
            'file_size': "-- MB"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url', '').strip()
    quality = data.get('quality', 'best')
    format_type = data.get('format', 'mp4')  # 'mp4' or 'mp3'
    
    if not url:
        return jsonify({'error': 'Please provide a YouTube URL'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Please provide a valid YouTube URL'}), 400
    
    # Generate unique download ID
    download_id = str(int(time.time() * 1000))
    
    # Create downloads directory if it doesn't exist
    downloads_dir = 'downloads'
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
    
    # Configure format selector based on download type with direct format codes
    if format_type == 'mp3':
        # For MP3, extract audio only
        format_selector = 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best'
    else:
        # For MP4, use specific format codes that work better
        quality_lower = quality.lower()
        
        if quality == 'best':
            format_selector = 'best[ext=mp4]/best'
        elif '2160' in quality_lower or '4k' in quality_lower:
            # 4K formats: 313 (webm), 271 (webm), 401 (mp4), 337 (webm)
            format_selector = '401+140/313+140/271+140/337+140/best[height>=2160]/best'
        elif '1440' in quality_lower:
            # 1440p formats: 271 (webm), 308 (webm), 264 (mp4)
            format_selector = '264+140/271+140/308+140/best[height>=1440]/best'
        elif '1080' in quality_lower:
            # 1080p formats: 137 (mp4), 299 (mp4), 248 (webm), 303 (webm)
            format_selector = '137+140/299+140/248+140/303+140/best[height>=1080]/best'
        elif '720' in quality_lower:
            # 720p formats: 136 (mp4), 298 (mp4), 247 (webm), 302 (webm)
            format_selector = '136+140/298+140/247+140/302+140/best[height>=720]/best'
        elif '480' in quality_lower:
            # 480p formats: 135 (mp4), 244 (webm)
            format_selector = '135+140/244+140/best[height>=480]/best'
        elif '360' in quality_lower:
            # 360p formats: 134 (mp4), 243 (webm), 18 (mp4)
            format_selector = '134+140/243+140/18/best[height>=360]/best'
        else:
            # Default fallback
            format_selector = 'best[ext=mp4]/best'
    
    # Initialize progress
    download_progress[download_id] = {
        'status': 'starting',
        'percent': 0,
        'total': 0,
        'speed': 0,
        'eta': 0
    }
    
    # Simplified yt-dlp configuration to avoid errors
    ydl_opts = {
        'format': format_selector,
        'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
        'no_warnings': True,
        'merge_output_format': 'mp4' if format_type == 'mp4' else None,
        'overwrites': True,
        'ignoreerrors': False,
        'retries': 5,
        'fragment_retries': 5,
        'skip_unavailable_fragments': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    
    # Debug output
    print(f"DEBUG: Quality selected: {quality}")
    print(f"DEBUG: Format selector: {format_selector}")
    print(f"DEBUG: Format type: {format_type}")
    
    # Add audio extraction options for MP3
    if format_type == 'mp3':
        ydl_opts.update({
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    
    # Start download in a separate thread
    download_thread = threading.Thread(target=download_thread_func, args=(url, ydl_opts, download_id))
    download_thread.daemon = True
    download_thread.start()
    
    return jsonify({'download_id': download_id, 'status': 'started'})

@app.route('/progress/<download_id>')
def get_progress(download_id):
    progress = download_progress.get(download_id, {'status': 'not_found'})
    
    # Format the progress data for frontend consumption
    if progress.get('status') == 'downloading':
        formatted_progress = {
            'status': 'downloading',
            'progress': progress.get('percent', 0),
            'speed': progress.get('speed_text', '0 B/s'),
            'eta': progress.get('eta_text', '0s'),
            'file_size': progress.get('file_size', '-- MB')
        }
    elif progress.get('status') == 'processing':
        formatted_progress = {
            'status': 'processing',
            'progress': 99,
            'speed': progress.get('speed_text', '0 B/s'),
            'eta': progress.get('eta_text', '0s'),
            'file_size': progress.get('file_size', '-- MB')
        }
    elif progress.get('status') == 'completed':
        formatted_progress = {
            'status': 'completed',
            'progress': 100,
            'speed': progress.get('speed_text', '0 B/s'),
            'eta': progress.get('eta_text', '0s'),
            'file_size': progress.get('file_size', '-- MB'),
            'filename': progress.get('filename', '')
        }
    elif progress.get('status') == 'finished':
        formatted_progress = {
            'status': 'completed',
            'progress': 100,
            'speed': progress.get('speed_text', '0 B/s'),
            'eta': progress.get('eta_text', '0s'),
            'file_size': progress.get('file_size', '-- MB'),
            'filename': progress.get('filename', '')
        }
    elif progress.get('status') == 'error':
        formatted_progress = {
            'status': 'error',
            'progress': 0,
            'error': progress.get('error', 'Unknown error'),
            'speed': progress.get('speed_text', '0 B/s'),
            'eta': progress.get('eta_text', '0s'),
            'file_size': progress.get('file_size', '-- MB')
        }
    else:
        formatted_progress = {
            'status': progress.get('status', 'unknown'),
            'progress': progress.get('percent', 0),
            'speed': '--',
            'eta': '--',
            'file_size': '--'
        }
    
    return jsonify(formatted_progress)

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'Please provide a YouTube URL'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Please provide a valid YouTube URL'}), 400
    
    try:
        # Simplified yt-dlp configuration to avoid the 'bool' object is not iterable error
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'retries': 3,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Validate that we got proper video info
            if not info:
                return jsonify({'error': 'Failed to extract video information'}), 500
            
            # Extract available formats with proper type checking
            formats = []
            seen_qualities = set()
            
            # Get formats from info
            raw_formats = info.get('formats', [])
            if not isinstance(raw_formats, list):
                raw_formats = []
            
            # Process each format
            for f in raw_formats:
                if not isinstance(f, dict):
                    continue
                
                format_id = f.get('format_id', '')
                height = f.get('height')
                width = f.get('width')
                vcodec = f.get('vcodec', '')
                acodec = f.get('acodec', '')
                
                # Skip if no format ID
                if not format_id:
                    continue
                
                # Skip audio-only formats for video download options
                if vcodec == 'none' or not height:
                    continue
                
                # Create quality label based on height
                if height:
                    if height >= 2160:
                        quality_label = "4K (2160p)"
                        sort_key = 2160
                    elif height >= 1440:
                        quality_label = "1440p"
                        sort_key = 1440
                    elif height >= 1080:
                        quality_label = "1080p"
                        sort_key = 1080
                    elif height >= 720:
                        quality_label = "720p"
                        sort_key = 720
                    elif height >= 480:
                        quality_label = "480p"
                        sort_key = 480
                    elif height >= 360:
                        quality_label = "360p"
                        sort_key = 360
                    elif height >= 240:
                        quality_label = "240p"
                        sort_key = 240
                    elif height >= 144:
                        quality_label = "144p"
                        sort_key = 144
                    else:
                        continue  # Skip very low quality
                    
                    # Check if we already have this quality
                    if quality_label in seen_qualities:
                        continue
                    
                    seen_qualities.add(quality_label)
                    
                    formats.append({
                        'format_id': format_id,
                        'format_note': quality_label,
                        'height': height,
                        'sort_key': sort_key
                    })
            
            # Sort formats by quality (highest first)
            formats.sort(key=lambda x: x['sort_key'], reverse=True)
            
            # If no formats found, add fallback options
            if not formats:
                formats = [
                    {'format_id': 'best', 'format_note': 'Best Available', 'height': 1080, 'sort_key': 1080},
                    {'format_id': 'worst', 'format_note': 'Lowest Quality', 'height': 360, 'sort_key': 360}
                ]
            
            return jsonify({
                'title': info.get('title', 'Unknown Title'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'view_count': info.get('view_count', 0),
                'formats': formats
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to get video information: {str(e)}'}), 500

@app.route('/download_file/<download_id>')
def download_file(download_id):
    progress = download_progress.get(download_id)
    if not progress or progress['status'] not in ['finished', 'completed']:
        return jsonify({'error': 'Download not completed'}), 400
    
    filename = progress.get('filename')
    if not filename:
        return jsonify({'error': 'No filename available'}), 400
    
    downloads_dir = 'downloads'
    full_path = os.path.join(downloads_dir, filename)
    
    if os.path.exists(full_path):
        return send_file(full_path, as_attachment=True)
    else:
        return jsonify({'error': f'File not found: {filename}'}), 404

if __name__ == '__main__':
    # For production, remove debug=True and use proper WSGI server
    app.run(debug=False, host='0.0.0.0', port=8000) 