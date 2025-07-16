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

        // Create direct download buttons (ytmate style)
        const downloadOptionsContainer = document.getElementById('download-options');
        if (downloadOptionsContainer) {
            downloadOptionsContainer.innerHTML = '';
            
            if (currentDownloadType === 'video' && videoData.formats) {
                // Add video format download buttons
                videoData.formats.forEach(format => {
                    if (format.format_id !== 'mp3') {  // Skip audio format for video downloads
                        const button = document.createElement('button');
                        button.className = 'hero-button w-full bg-hero-blue hover:bg-blue-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium shadow-hero mb-2';
                        button.innerHTML = `<i class="fas fa-download mr-2"></i>${format.format_note || format.format_id}`;
                        button.onclick = () => {
                            // Direct link to stream endpoint - opens in new tab
                            const streamUrl = `/stream/${videoData.video_id}/${format.format_id}`;
                            window.open(streamUrl, '_blank');
                        };
                        downloadOptionsContainer.appendChild(button);
                    }
                });
            } else if (currentDownloadType === 'mp3') {
                // Add MP3 download button
                const button = document.createElement('button');
                button.className = 'hero-button w-full bg-hero-green hover:bg-green-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium shadow-hero mb-2';
                button.innerHTML = `<i class="fas fa-music mr-2"></i>Download MP3 Audio`;
                button.onclick = () => {
                    // Direct link to stream endpoint for MP3
                    const streamUrl = `/stream/${videoData.video_id}/mp3`;
                    window.open(streamUrl, '_blank');
                };
                downloadOptionsContainer.appendChild(button);
            }
        }

        // Hide quality selection - using direct buttons instead
        if (qualitySelect && qualitySelect.parentElement) {
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

    // Start download button is no longer needed - using direct download buttons

    // Progress tracking is no longer needed - using direct download buttons

    // Direct download function - no longer used with new ytmate-style buttons
    function triggerDirectDownload(downloadId, filename) {
        // This function is kept for compatibility but not used with new direct buttons
        const streamUrl = `/direct_download/${downloadId}?stream=true`;
        window.open(streamUrl, '_blank');
        console.log('Stream opened in new tab:', filename);
    }

    // Helper functions no longer needed - using direct download buttons

    // Handle download file button click - for re-downloading
    if (finalDownloadBtn) {
        finalDownloadBtn.addEventListener('click', function() {
            const filename = this.getAttribute('data-filename');
            const downloadId = this.getAttribute('data-download-id');
            
            if (downloadId) {
                // Trigger direct download again
                triggerDirectDownload(downloadId, filename);
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