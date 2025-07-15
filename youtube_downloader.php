<?php
// PHP YouTube Downloader
// This is a fallback solution for shared hosting without Python

session_start();

// Enhanced Python/yt-dlp detection function
function detectPythonEnvironment() {
    $python_commands = [
        'python3',
        'python',
        'python3.9',
        'python3.8',
        'python3.10',
        'python3.11',
        '/usr/bin/python3',
        '/usr/local/bin/python3',
        '/opt/python/bin/python3',
        '/usr/bin/python',
        '/usr/local/bin/python'
    ];
    
    $results = [];
    
    foreach ($python_commands as $cmd) {
        // Test if command exists
        $which_output = shell_exec("which $cmd 2>&1");
        $version_output = shell_exec("$cmd --version 2>&1");
        
        $results[] = [
            'command' => $cmd,
            'which' => trim($which_output),
            'version' => trim($version_output),
            'available' => !empty($which_output) && strpos($which_output, 'no ') === false
        ];
    }
    
    // Check for yt-dlp specifically
    $ytdlp_check = shell_exec("yt-dlp --version 2>&1");
    $results['ytdlp'] = [
        'output' => trim($ytdlp_check),
        'available' => !empty($ytdlp_check) && strpos($ytdlp_check, 'command not found') === false
    ];
    
    // Check PATH environment
    $path_env = getenv('PATH');
    $results['environment'] = [
        'path' => $path_env ?: 'Not set',
        'python_libs' => glob('/usr/local/lib/python*') ?: []
    ];
    
    return $results;
}

// Handle AJAX requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'check_environment') {
        $env_check = detectPythonEnvironment();
        echo json_encode($env_check);
        exit;
    }
    
    if ($action === 'get_video_info') {
        $url = $_POST['url'] ?? '';
        if (empty($url)) {
            http_response_code(400);
            echo json_encode(['error' => 'URL is required']);
            exit;
        }
        
        // Try multiple yt-dlp commands
        $commands = [
            "yt-dlp -J " . escapeshellarg($url) . " 2>&1",
            "/usr/local/bin/yt-dlp -J " . escapeshellarg($url) . " 2>&1",
            "python3 -m yt_dlp -J " . escapeshellarg($url) . " 2>&1",
            "/usr/local/bin/python3 -m yt_dlp -J " . escapeshellarg($url) . " 2>&1"
        ];
        
        $output = null;
        $successful_command = null;
        
        foreach ($commands as $command) {
            $output = shell_exec($command);
            if ($output && strpos($output, 'command not found') === false && strpos($output, 'No such file') === false) {
                $successful_command = $command;
                break;
            }
        }
        
        if ($output && $successful_command) {
            // yt-dlp worked
            $video_info = json_decode($output, true);
            if ($video_info) {
                echo json_encode([
                    'title' => $video_info['title'] ?? 'Unknown',
                    'duration' => $video_info['duration'] ?? 0,
                    'thumbnail' => $video_info['thumbnail'] ?? '',
                    'formats' => array_slice($video_info['formats'] ?? [], 0, 10),
                    'command_used' => $successful_command
                ]);
            } else {
                echo json_encode(['error' => 'Failed to parse video information']);
            }
        } else {
            // Enhanced error message with diagnostics
            echo json_encode([
                'error' => 'Python/yt-dlp not available on this server',
                'message' => 'This hosting provider does not support Python applications or yt-dlp is not installed.',
                'suggestions' => [
                    'Contact your hosting provider about Python support',
                    'Ask about installing yt-dlp or enabling Python modules',
                    'Consider upgrading to a hosting plan with Python support',
                    'Try using a VPS or dedicated server instead'
                ],
                'technical_details' => 'Python libraries found but executable not in PATH'
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
        
        // Try to download using multiple yt-dlp commands
        $download_id = uniqid();
        $output_dir = 'downloads/';
        
        if (!is_dir($output_dir)) {
            mkdir($output_dir, 0755, true);
        }
        
        $base_commands = [
            "yt-dlp",
            "/usr/local/bin/yt-dlp",
            "python3 -m yt_dlp",
            "/usr/local/bin/python3 -m yt_dlp"
        ];
        
        foreach ($base_commands as $base_cmd) {
            if ($format === 'mp3') {
                $command = "$base_cmd -x --audio-format mp3 -o " . escapeshellarg($output_dir . '%(title)s.%(ext)s') . " " . escapeshellarg($url) . " 2>&1";
            } else {
                $command = "$base_cmd -f 'best[height<=720]' -o " . escapeshellarg($output_dir . '%(title)s.%(ext)s') . " " . escapeshellarg($url) . " 2>&1";
            }
            
            $output = shell_exec($command);
            
            if ($output && strpos($output, 'command not found') === false && strpos($output, 'No such file') === false) {
                // Find the downloaded file
                $files = glob($output_dir . '*');
                if (!empty($files)) {
                    $latest_file = array_reduce($files, function($a, $b) {
                        return filemtime($a) > filemtime($b) ? $a : $b;
                    });
                    
                    echo json_encode([
                        'success' => true,
                        'download_id' => $download_id,
                        'file' => basename($latest_file),
                        'command_used' => $base_cmd
                    ]);
                    exit;
                }
            }
        }
        
        // If we get here, none of the commands worked
        echo json_encode([
            'error' => 'Python/yt-dlp not available',
            'message' => 'This hosting provider does not support Python applications.',
            'suggestions' => [
                'Contact your hosting provider about Python support',
                'Ask about installing yt-dlp or enabling Python modules',
                'Consider upgrading to a hosting plan with Python support'
            ]
        ]);
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
            
            <!-- Environment Status -->
            <div class="bg-gray-800 rounded-lg p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">Server Environment Status</h2>
                <button 
                    id="check-env"
                    class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors mb-4"
                >
                    Check Environment
                </button>
                <div id="env-results" class="hidden bg-gray-700 rounded-lg p-4 text-sm"></div>
            </div>
            
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
            
            <div id="error-message" class="bg-red-600 text-white p-4 rounded-lg mb-4 hidden">
                <div id="error-text"></div>
                <div id="error-suggestions" class="mt-2 text-sm"></div>
            </div>
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
        const checkEnvBtn = document.getElementById('check-env');
        const errorDiv = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        const errorSuggestions = document.getElementById('error-suggestions');
        const successDiv = document.getElementById('success-message');
        const loadingDiv = document.getElementById('loading');
        const envResults = document.getElementById('env-results');
        
        function showError(message, suggestions = []) {
            errorText.textContent = message;
            
            if (suggestions.length > 0) {
                errorSuggestions.innerHTML = '<strong>Suggestions:</strong><ul class="list-disc list-inside mt-1">' + 
                    suggestions.map(s => `<li>${s}</li>`).join('') + '</ul>';
            } else {
                errorSuggestions.innerHTML = '';
            }
            
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
        
        // Check environment function
        checkEnvBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('youtube_downloader.php', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'action=check_environment'
                });
                
                const result = await response.json();
                
                let html = '<h3 class="font-bold mb-2">Python Detection Results:</h3>';
                
                // Show Python command results
                for (let i = 0; i < result.length - 2; i++) {
                    const cmd = result[i];
                    const status = cmd.available ? '✅' : '❌';
                    html += `<div class="mb-1">${status} ${cmd.command}: ${cmd.which || 'Not found'}</div>`;
                }
                
                // Show yt-dlp status
                const ytdlpStatus = result.ytdlp.available ? '✅' : '❌';
                html += `<div class="mb-2">${ytdlpStatus} yt-dlp: ${result.ytdlp.output || 'Not found'}</div>`;
                
                // Show environment info
                html += `<div class="mt-4"><strong>Environment:</strong></div>`;
                html += `<div>PATH: ${result.environment.path}</div>`;
                
                if (result.environment.python_libs.length > 0) {
                    html += `<div class="mt-2"><strong>Python Libraries Found:</strong></div>`;
                    result.environment.python_libs.forEach(lib => {
                        html += `<div class="text-xs">📁 ${lib}</div>`;
                    });
                }
                
                envResults.innerHTML = html;
                envResults.classList.remove('hidden');
                
            } catch (error) {
                envResults.innerHTML = '<div class="text-red-400">Error checking environment: ' + error.message + '</div>';
                envResults.classList.remove('hidden');
            }
        });
        
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
                    showError(result.error || 'Download failed', result.suggestions || []);
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