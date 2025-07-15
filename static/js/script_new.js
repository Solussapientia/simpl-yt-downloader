document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript loaded - Version 8 - Dynamic Formats');
    
    try {
    
    // Elements
    const urlInput = document.getElementById('youtube-url');
    const downloadBtn = document.getElementById('download-btn');
    const downloadMp3Btn = document.getElementById('download-mp3-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoading = document.getElementById('btn-loading');
    const btnMp3Text = document.getElementById('btn-mp3-text');
    const btnMp3Loading = document.getElementById('btn-mp3-loading');
    const videoInfo = document.getElementById('video-info');
    const startDownloadBtn = document.getElementById('start-download-btn');
    const downloadProgress = document.getElementById('download-progress');
    const downloadComplete = document.getElementById('download-complete');
    const finalDownloadBtn = document.getElementById('final-download-btn');
    
    // Video info elements
    const videoTitle = document.getElementById('video-title');
    const videoUploader = document.getElementById('video-uploader');
    const videoDuration = document.getElementById('video-duration');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const qualitySelect = document.getElementById('quality-select');
    
    // Progress elements
    const downloadSpeed = document.getElementById('download-speed');
    const downloadStatus = document.getElementById('download-status');
    
    // Error elements
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    let currentVideoInfo = null;
    let currentDownloadId = null;
    let currentDownloadType = 'video'; // 'video' or 'audio'

    // Format duration from seconds to MM:SS or HH:MM:SS
    function formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return 'Unknown';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    // Show error message
    function showError(message) {
        if (errorText) {
            errorText.textContent = message;
        }
        if (errorMessage) {
            errorMessage.classList.remove('hidden');
        }
        if (videoInfo) {
            videoInfo.classList.add('hidden');
        }
        if (downloadProgress) {
            downloadProgress.classList.add('hidden');
        }
        if (downloadComplete) {
            downloadComplete.classList.add('hidden');
        }
    }

    // Hide error message
    function hideError() {
        if (errorMessage) {
            errorMessage.classList.add('hidden');
        }
    }

    // Reset UI state
    function resetUI() {
        hideError();
        if (videoInfo) {
            videoInfo.classList.add('hidden');
        }
        if (downloadProgress) {
            downloadProgress.classList.add('hidden');
        }
        if (downloadComplete) {
            downloadComplete.classList.add('hidden');
        }
        
        // Reset video download button
        if (btnText) {
            btnText.textContent = 'Download Video';
        }
        if (btnLoading) {
            btnLoading.classList.add('hidden');
        }
        if (downloadBtn) {
            downloadBtn.disabled = false;
        }
        
        // Reset MP3 download button
        if (btnMp3Text) {
            btnMp3Text.textContent = 'Download MP3';
        }
        if (btnMp3Loading) {
            btnMp3Loading.classList.add('hidden');
        }
        if (downloadMp3Btn) {
            downloadMp3Btn.disabled = false;
        }
    }

    // Get video information and available formats
    async function getVideoInfo(url) {
        try {
            const response = await fetch('/get_video_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to get video information');
            }

            return data;
        } catch (error) {
            throw error;
        }
    }

    // Display video information and format options
    function displayVideoInfo(videoData) {
        currentVideoInfo = videoData;
        
        // Set video details
        if (videoTitle) {
            videoTitle.textContent = videoData.title || 'Unknown Title';
        }
        if (videoUploader) {
            videoUploader.textContent = `Channel: ${videoData.uploader || 'Unknown'}`;
        }
        if (videoDuration) {
            videoDuration.textContent = `Duration: ${formatDuration(videoData.duration)}`;
        }
        if (videoThumbnail) {
            videoThumbnail.src = videoData.thumbnail || '';
            videoThumbnail.alt = videoData.title || 'Video thumbnail';
        }

        // Create format selection UI
        createFormatSelector(videoData);

        // Show video info section
        if (videoInfo) {
            videoInfo.classList.remove('hidden');
        }
    }

    // Create format selector based on available formats
    function createFormatSelector(videoData) {
        if (!qualitySelect) return;

        // Clear existing options
        qualitySelect.innerHTML = '';

        if (currentDownloadType === 'video' && videoData.video_formats) {
            // Add video format options
            videoData.video_formats.forEach(format => {
                const option = document.createElement('option');
                option.value = format.format_id;
                option.textContent = format.display_name;
                option.setAttribute('data-format-type', 'video');
                qualitySelect.appendChild(option);
            });
        } else if (currentDownloadType === 'audio' && videoData.audio_formats) {
            // Add audio format options
            videoData.audio_formats.forEach(format => {
                const option = document.createElement('option');
                option.value = format.format_id;
                option.textContent = format.display_name;
                option.setAttribute('data-format-type', 'audio');
                qualitySelect.appendChild(option);
            });
        }

        // Show quality selection
        if (qualitySelect.parentElement) {
            qualitySelect.parentElement.classList.remove('hidden');
        }
    }

    // Download video with selected format
    async function downloadVideo(url, formatId, formatType) {
        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    format_id: formatId,
                    format_type: formatType
                })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Download failed');
            }

            currentDownloadId = data.download_id;
            return data;
        } catch (error) {
            throw error;
        }
    }

    // Poll download progress
    async function pollProgress(downloadId) {
        try {
            const response = await fetch(`/progress/${downloadId}`);
            const data = await response.json();
            
            if (downloadProgress) {
                downloadProgress.classList.remove('hidden');
            }
            
            // Update progress UI
            updateProgressUI(data);
            
            // Continue polling if not finished
            if (data.status === 'downloading' || data.status === 'processing') {
                setTimeout(() => pollProgress(downloadId), 1000);
            }
            
        } catch (error) {
            console.error('Error polling progress:', error);
        }
    }

    // Update progress UI
    function updateProgressUI(progressData) {
        if (downloadStatus) {
            downloadStatus.textContent = progressData.status;
        }
        if (downloadSpeed) {
            downloadSpeed.textContent = progressData.speed || '0 B/s';
        }
        
        // Update progress bar if it exists
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progressData.progress || 0}%`;
        }
        
        // Show completion
        if (progressData.status === 'completed' && progressData.filename) {
            showDownloadComplete(progressData.filename);
        } else if (progressData.status === 'error') {
            showError(progressData.error || 'Download failed');
        }
    }

    // Show download complete
    function showDownloadComplete(filename) {
        if (downloadProgress) {
            downloadProgress.classList.add('hidden');
        }
        if (downloadComplete) {
            downloadComplete.classList.remove('hidden');
        }
        if (finalDownloadBtn) {
            finalDownloadBtn.href = `/download_file/${currentDownloadId}`;
            finalDownloadBtn.textContent = `Download ${filename}`;
        }
    }

    // Handle download button click (Video)
    if (downloadBtn) {
        downloadBtn.addEventListener('click', async function() {
            const url = urlInput.value.trim();
            if (!url) {
                showError('Please enter a YouTube URL');
                return;
            }

            currentDownloadType = 'video';
            resetUI();
            
            // Show loading state
            if (btnText) {
                btnText.classList.add('hidden');
            }
            if (btnLoading) {
                btnLoading.classList.remove('hidden');
            }
            if (downloadBtn) {
                downloadBtn.disabled = true;
            }

            try {
                const videoData = await getVideoInfo(url);
                displayVideoInfo(videoData);
            } catch (error) {
                showError(error.message);
            } finally {
                if (btnText) {
                    btnText.classList.remove('hidden');
                }
                if (btnLoading) {
                    btnLoading.classList.add('hidden');
                }
                if (downloadBtn) {
                    downloadBtn.disabled = false;
                }
            }
        });
    }

    // Handle download button click (MP3)
    if (downloadMp3Btn) {
        downloadMp3Btn.addEventListener('click', async function() {
            const url = urlInput.value.trim();
            if (!url) {
                showError('Please enter a YouTube URL');
                return;
            }

            currentDownloadType = 'audio';
            resetUI();
            
            // Show loading state
            if (btnMp3Text) {
                btnMp3Text.classList.add('hidden');
            }
            if (btnMp3Loading) {
                btnMp3Loading.classList.remove('hidden');
            }
            if (downloadMp3Btn) {
                downloadMp3Btn.disabled = true;
            }

            try {
                const videoData = await getVideoInfo(url);
                displayVideoInfo(videoData);
            } catch (error) {
                showError(error.message);
            } finally {
                if (btnMp3Text) {
                    btnMp3Text.classList.remove('hidden');
                }
                if (btnMp3Loading) {
                    btnMp3Loading.classList.add('hidden');
                }
                if (downloadMp3Btn) {
                    downloadMp3Btn.disabled = false;
                }
            }
        });
    }

    // Handle start download button click
    if (startDownloadBtn) {
        startDownloadBtn.addEventListener('click', async function() {
            if (!currentVideoInfo || !qualitySelect) {
                showError('Please select a format first');
                return;
            }

            const selectedOption = qualitySelect.options[qualitySelect.selectedIndex];
            const formatId = selectedOption.value;
            const formatType = selectedOption.getAttribute('data-format-type') || currentDownloadType;

            if (!formatId) {
                showError('Please select a valid format');
                return;
            }

            try {
                const url = urlInput.value.trim();
                await downloadVideo(url, formatId, formatType);
                pollProgress(currentDownloadId);
            } catch (error) {
                showError(error.message);
            }
        });
    }

    } catch (error) {
        console.error('JavaScript initialization error:', error);
    }
}); 