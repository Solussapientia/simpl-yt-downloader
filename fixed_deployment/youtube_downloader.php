<?php
// PHP YouTube Downloader
// This is a fallback solution for shared hosting without Python

session_start();

// Handle AJAX requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'get_video_info') {
        $url = $_POST['url'] ?? '';
        if (empty($url)) {
            http_response_code(400);
            echo json_encode(['error' => 'URL is required']);
            exit;
        }
        
        // Try to get video info using yt-dlp (if available)
        $command = "yt-dlp -J " . escapeshellarg($url) . " 2>&1";
        $output = shell_exec($command);
        
        if ($output && strpos($output, 'command not found') === false) {
            // yt-dlp worked
            $video_info = json_decode($output, true);
            if ($video_info) {
                echo json_encode([
                    'title' => $video_info['title'] ?? 'Unknown',
                    'duration' => $video_info['duration'] ?? 0,
                    'thumbnail' => $video_info['thumbnail'] ?? '',
                    'formats' => array_slice($video_info['formats'] ?? [], 0, 10)
                ]);
            } else {
                echo json_encode(['error' => 'Failed to parse video information']);
            }
        } else {
            // Fallback: Use YouTube API or basic info extraction
            echo json_encode([
                'error' => 'Python/yt-dlp not available on this server',
                'message' => 'This hosting provider does not support Python applications. Please contact your hosting provider about Python support.'
            ]);
        }
        exit;
    }
    
    if ($action === 'download') {
        $url = $_POST['url'] ?? '';
        $format = $_POST['format'] ?? 'mp4';
        
        if (empty($url)) {
            http_response_code(400);
            echo json_encode(['error' => 'URL is required']);
            exit;
        }
        
        // Try to download using yt-dlp
        $download_id = uniqid();
        $output_dir = 'downloads/';
        
        if (!is_dir($output_dir)) {
            mkdir($output_dir, 0755, true);
        }
        
        if ($format === 'mp3') {
            $command = "yt-dlp -x --audio-format mp3 -o " . escapeshellarg($output_dir . '%(title)s.%(ext)s') . " " . escapeshellarg($url) . " 2>&1";
        } else {
            $command = "yt-dlp -f 'best[height<=720]' -o " . escapeshellarg($output_dir . '%(title)s.%(ext)s') . " " . escapeshellarg($url) . " 2>&1";
        }
        
        $output = shell_exec($command);
        
        if ($output && strpos($output, 'command not found') === false) {
            // Find the downloaded file
            $files = glob($output_dir . '*');
            if (!empty($files)) {
                $latest_file = array_reduce($files, function($a, $b) {
                    return filemtime($a) > filemtime($b) ? $a : $b;
                });
                
                echo json_encode([
                    'success' => true,
                    'download_id' => $download_id,
                    'file' => basename($latest_file)
                ]);
            } else {
                echo json_encode(['error' => 'Download failed - no file created']);
            }
        } else {
            echo json_encode([
                'error' => 'Python/yt-dlp not available',
                'message' => 'This hosting provider does not support Python applications.'
            ]);
        }
        exit;
    }
}

// HTML Interface
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader - PHP Version</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="icon" type="image/svg+xml" href="/static/images/favicon.svg">
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-4xl font-bold text-center mb-8">
                Simpl YT Downloader
            </h1>
            
            <div class="bg-gray-800 rounded-lg p-6 mb-6">
                <div class="mb-4">
                    <input 
                        type="text" 
                        id="url-input" 
                        placeholder="Enter YouTube URL here..."
                        class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                </div>
                
                <div class="flex gap-4">
                    <button 
                        id="download-video"
                        class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                    >
                        Download Video
                    </button>
                    
                    <button 
                        id="download-mp3"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                    >
                        Download MP3
                    </button>
                </div>
            </div>
            
            <div id="error-message" class="bg-red-600 text-white p-4 rounded-lg mb-4 hidden"></div>
            <div id="success-message" class="bg-green-600 text-white p-4 rounded-lg mb-4 hidden"></div>
            <div id="loading" class="text-center py-4 hidden">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                <p class="mt-2">Processing...</p>
            </div>
            
            <div id="video-info" class="bg-gray-800 rounded-lg p-6 hidden">
                <h3 class="text-xl font-bold mb-4">Video Information</h3>
                <div id="video-details"></div>
            </div>
        </div>
    </div>
    
    <script>
        const urlInput = document.getElementById('url-input');
        const downloadVideoBtn = document.getElementById('download-video');
        const downloadMp3Btn = document.getElementById('download-mp3');
        const errorDiv = document.getElementById('error-message');
        const successDiv = document.getElementById('success-message');
        const loadingDiv = document.getElementById('loading');
        
        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
            successDiv.classList.add('hidden');
        }
        
        function showSuccess(message) {
            successDiv.textContent = message;
            successDiv.classList.remove('hidden');
            errorDiv.classList.add('hidden');
        }
        
        function hideMessages() {
            errorDiv.classList.add('hidden');
            successDiv.classList.add('hidden');
        }
        
        async function handleDownload(format) {
            const url = urlInput.value.trim();
            if (!url) {
                showError('Please enter a YouTube URL');
                return;
            }
            
            hideMessages();
            loadingDiv.classList.remove('hidden');
            
            try {
                const response = await fetch('youtube_downloader.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `action=download&url=${encodeURIComponent(url)}&format=${format}`
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess(`Download completed: ${result.file}`);
                } else {
                    showError(result.error || 'Download failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                loadingDiv.classList.add('hidden');
            }
        }
        
        downloadVideoBtn.addEventListener('click', () => handleDownload('mp4'));
        downloadMp3Btn.addEventListener('click', () => handleDownload('mp3'));
    </script>
</body>
</html> 