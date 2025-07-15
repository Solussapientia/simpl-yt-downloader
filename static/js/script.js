document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript loaded - Version 7');
    
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
    
    // Debug: Check which elements are null
    console.log('Element check:', {
        urlInput: !!urlInput,
        downloadBtn: !!downloadBtn,
        downloadMp3Btn: !!downloadMp3Btn,
        btnText: !!btnText,
        btnLoading: !!btnLoading,
        btnMp3Text: !!btnMp3Text,
        btnMp3Loading: !!btnMp3Loading,
        videoInfo: !!videoInfo,
        startDownloadBtn: !!startDownloadBtn,
        downloadProgress: !!downloadProgress,
        downloadComplete: !!downloadComplete,
        finalDownloadBtn: !!finalDownloadBtn,
        videoTitle: !!videoTitle,
        videoUploader: !!videoUploader,
        videoDuration: !!videoDuration,
        videoThumbnail: !!videoThumbnail,
        qualitySelect: !!qualitySelect,
        downloadSpeed: !!downloadSpeed,
        downloadStatus: !!downloadStatus,
        errorMessage: !!errorMessage,
        errorText: !!errorText
    });

    let currentVideoInfo = null;
    let currentDownloadId = null;
    let currentDownloadType = 'video'; // 'video' or 'mp3'

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

    // Get video information
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

    // Display video information
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

        // Populate quality options for video downloads
        if (currentDownloadType === 'video' && qualitySelect) {
            qualitySelect.innerHTML = '';
            if (videoData.formats && videoData.formats.length > 0) {
                videoData.formats.forEach(format => {
                    const option = document.createElement('option');
                    // Use quality label as value instead of format_id
                    option.value = format.format_note || format.format_id;
                    option.textContent = format.format_note || format.format_id;
                    qualitySelect.appendChild(option);
                });
            }
            // If no formats available, add a default option
            if (qualitySelect.children.length === 0) {
                const option = document.createElement('option');
                option.value = 'mp4';
                option.textContent = 'MP4 (Default)';
                qualitySelect.appendChild(option);
            }
            if (qualitySelect.parentElement) {
                qualitySelect.parentElement.classList.remove('hidden');
            }
        } else if (qualitySelect && qualitySelect.parentElement) {
            // Hide quality selection for MP3 downloads
            qualitySelect.parentElement.classList.add('hidden');
        }

        // Show video info section
        if (videoInfo) {
            videoInfo.classList.remove('hidden');
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

    // Handle download MP3 button click
    if (downloadMp3Btn) {
        downloadMp3Btn.addEventListener('click', async function() {
            const url = urlInput.value.trim();
            if (!url) {
                showError('Please enter a YouTube URL');
                return;
            }

            currentDownloadType = 'mp3';
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
            const url = urlInput.value.trim();
            if (!url) {
                showError('Please enter a YouTube URL');
                return;
            }

            // Hide video info and show progress
            if (videoInfo) {
                videoInfo.classList.add('hidden');
            }
            if (downloadProgress) {
                downloadProgress.classList.remove('hidden');
            }
            
            // Reset progress
            if (downloadSpeed) {
                downloadSpeed.textContent = '--';
            }
            if (downloadStatus) {
                downloadStatus.textContent = 'Starting...';
            }

            try {
                let quality = 'mp4';
                let format = 'mp4';
                
                if (currentDownloadType === 'video') {
                    quality = qualitySelect ? (qualitySelect.value || 'mp4') : 'mp4';
                    format = 'mp4';
                } else {
                    format = 'mp3';
                }

                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        url: url, 
                        quality: quality,
                        format: format
                    })
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to start download');
                }

                currentDownloadId = data.download_id;
                startProgressTracking();
                
            } catch (error) {
                showError(error.message);
            }
        });
    }

    // Start tracking download progress
    function startProgressTracking() {
        if (!currentDownloadId) return;

        const pollProgress = async () => {
            try {
                const response = await fetch(`/progress/${currentDownloadId}`);
                const data = await response.json();

                // Handle progress updates
                if (data.status === 'downloading') {
                    // Update progress stats
                    updateProgressStats(data.speed, data.eta, data.total);
                    
                    // Continue polling
                    setTimeout(pollProgress, 1000);
                } else if (data.status === 'processing') {
                    // Show processing status
                    if (downloadSpeed) {
                        downloadSpeed.textContent = 'Processing...';
                    }
                    if (downloadStatus) {
                        downloadStatus.textContent = 'Processing...';
                    }
                    
                    // Continue polling
                    setTimeout(pollProgress, 1000);
                } else if (data.status === 'completed') {
                    // Download completed
                    if (downloadSpeed) {
                        downloadSpeed.textContent = 'Completed';
                    }
                    if (downloadStatus) {
                        downloadStatus.textContent = 'Completed';
                    }
                    
                    // Show completion message
                    if (downloadProgress) {
                        downloadProgress.classList.add('hidden');
                    }
                    if (downloadComplete) {
                        downloadComplete.classList.remove('hidden');
                    }
                    
                    // Set download button data
                    if (finalDownloadBtn) {
                        finalDownloadBtn.setAttribute('data-filename', data.filename);
                        finalDownloadBtn.setAttribute('data-download-id', currentDownloadId);
                    }
                    
                    console.log('Download completed:', data.filename);
                } else if (data.status === 'error') {
                    // Download failed
                    showError(data.error || 'Download failed');
                    if (downloadProgress) {
                        downloadProgress.classList.add('hidden');
                    }
                } else {
                    // Continue polling for other statuses
                    setTimeout(pollProgress, 1000);
                }
            } catch (error) {
                console.error('Failed to get download progress:', error);
                // Optionally show a temporary error message or re-attempt polling
            }
        };

        // Initial poll
        pollProgress();
    }

    // Update progress display (simplified)
    function updateProgressStats(speed, eta, total) {
        if (downloadSpeed) {
            downloadSpeed.textContent = speed || '--';
        }
        if (downloadStatus) {
            downloadStatus.textContent = 'Downloading...';
        }
    }

    // Show download complete
    function showDownloadComplete() {
        // This function is now handled by startProgressTracking's polling
    }

    // Handle download file button click
    if (finalDownloadBtn) {
        finalDownloadBtn.addEventListener('click', function() {
            if (currentDownloadId) {
                window.location.href = `/download_file/${currentDownloadId}`;
            }
        });
    }

    // Allow Enter key to trigger download
    if (urlInput) {
        urlInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                if (currentDownloadType === 'mp3' && downloadMp3Btn) {
                    downloadMp3Btn.click();
                } else if (downloadBtn) {
                    downloadBtn.click();
                }
            }
        });
    }
    
    } catch (error) {
        console.error('JavaScript error caught:', error);
        console.error('Error stack:', error.stack);
    }
}); 