# YouTube Video Downloader

A modern, responsive web application for downloading YouTube videos with an intuitive user interface.

## Features

- ✅ Modern, responsive design
- ✅ YouTube video information preview
- ✅ Multiple quality options
- ✅ Real-time download progress tracking
- ✅ Easy-to-use interface
- ✅ File download functionality

## Requirements

- Python 3.7 or higher
- Internet connection
- ffmpeg (for merging high-quality video and audio streams)

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Install ffmpeg (if not already installed):

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html or use chocolatey:
```bash
choco install ffmpeg
```

4. Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:

```bash
python app.py
```

2. Open your web browser and go to `http://localhost:8000`

3. Paste a YouTube video URL into the input field

4. Click "Get Info" to preview the video information

5. Select your preferred quality and click "Download Video"

6. Wait for the download to complete and click "Download File" to save it to your device

## Features Overview

### Video Information
- Video title and thumbnail
- Channel name and video duration
- Available quality options

### Download Options
- Best quality (auto-selected)
- Best video + audio merge
- Multiple resolution options (4K, 1080p, 720p, etc.)
- Various formats (MP4, WebM, etc.)
- Video-only and audio-only formats
- File size information for each format

### Progress Tracking
- Real-time download progress
- Download speed and ETA
- File size information

## File Structure

```
SIMEPLE YT DOWNLOADER/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── script.js     # Frontend JavaScript
└── downloads/            # Downloaded videos folder (created automatically)
```

## Technical Details

### Backend
- **Flask**: Web framework
- **yt-dlp**: YouTube video downloading library
- **Threading**: For non-blocking downloads
- **JSON API**: For frontend communication

### Frontend
- **Vanilla JavaScript**: No external frameworks
- **CSS Grid/Flexbox**: Modern responsive layout
- **Font Awesome**: Icons
- **Fetch API**: For server communication

## Important Notes

⚠️ **Legal Disclaimer**: This tool is for personal use only. Please respect copyright laws and YouTube's terms of service. Only download videos you have permission to download.

⚠️ **Network**: A stable internet connection is required for downloading videos.

⚠️ **Storage**: Downloaded videos will be saved in the `downloads/` folder in the project directory.

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure all dependencies are installed with `pip install -r requirements.txt`
2. **Download Fails**: Check your internet connection and verify the YouTube URL is valid
3. **Port Already in Use**: If port 8000 is occupied, change the port in `app.py` to another available port (like 5001 or 3000)

### Browser Compatibility

This application works best with modern browsers:
- Chrome 70+
- Firefox 65+
- Safari 12+
- Edge 79+

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes only. Use responsibly and in accordance with applicable laws and terms of service. 