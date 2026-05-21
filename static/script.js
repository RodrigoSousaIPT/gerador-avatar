document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('avatar-form');
    const imageUpload = document.getElementById('image-upload');
    const fileLabel = document.querySelector('.file-upload-label');
    const fileNameDisplay = document.getElementById('file-name');
    const submitBtn = document.getElementById('generate-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = submitBtn.querySelector('.loader');
    
    const emptyState = document.getElementById('empty-state');
    const resultContent = document.getElementById('result-content');
    const resultImage = document.getElementById('result-image');
    const resultAudio = document.getElementById('result-audio');

    // Handle Drag and Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileLabel.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileLabel.addEventListener(eventName, () => {
            fileLabel.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileLabel.addEventListener(eventName, () => {
            fileLabel.classList.remove('dragover');
        }, false);
    });

    fileLabel.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if(files.length > 0) {
            imageUpload.files = files;
            updateFileName();
        }
    });

    imageUpload.addEventListener('change', updateFileName);

    function updateFileName() {
        if(imageUpload.files.length > 0) {
            fileNameDisplay.textContent = imageUpload.files[0].name;
            fileNameDisplay.style.color = '#a855f7';
            fileNameDisplay.style.fontWeight = 'bold';
        } else {
            fileNameDisplay.textContent = 'Faça upload de uma face';
            fileNameDisplay.style.color = '';
            fileNameDisplay.style.fontWeight = '';
        }
    }

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (imageUpload.files.length === 0) {
            alert('Por favor, selecione uma imagem.');
            return;
        }

        // UI Loading State
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';
        
        // Form Data
        const formData = new FormData(form);

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Update UI with result
                emptyState.style.display = 'none';
                resultContent.style.display = 'flex';
                
                // Add timestamp to prevent caching
                const timestamp = new Date().getTime();
                
                if (data.video_url) {
                    // Hide image and audio, show video
                    resultImage.style.display = 'none';
                    resultAudio.parentElement.style.display = 'none';
                    
                    // Create or update video element
                    let videoEl = document.getElementById('result-video');
                    if (!videoEl) {
                        videoEl = document.createElement('video');
                        videoEl.id = 'result-video';
                        videoEl.controls = true;
                        videoEl.autoplay = true;
                        videoEl.style.width = '100%';
                        videoEl.style.borderRadius = '20px';
                        videoEl.style.marginTop = '1rem';
                        resultContent.insertBefore(videoEl, resultAudio.parentElement);
                    }
                    videoEl.src = `${data.video_url}?t=${timestamp}`;
                    videoEl.style.display = 'block';
                    
                    const pulseRing = document.querySelector('.pulse-ring');
                    if(pulseRing) pulseRing.style.display = 'none';
                    
                    const avatarDisplay = document.querySelector('.avatar-display');
                    if(avatarDisplay) {
                        avatarDisplay.style.background = 'transparent';
                        avatarDisplay.style.width = '100%';
                        avatarDisplay.style.height = 'auto';
                        avatarDisplay.style.borderRadius = '20px';
                    }
                } else {
                    resultImage.src = `${data.image_url}?t=${timestamp}`;
                    
                    resultAudio.src = `${data.audio_url}?t=${timestamp}`;
                    resultAudio.load();
                    
                    // Optional: Play audio automatically after image loads
                    resultImage.onload = () => {
                        resultAudio.play().catch(e => console.log("Auto-play prevented by browser"));
                    };
                }

            } else {
                alert('Erro ao gerar avatar: ' + data.error);
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            alert('Ocorreu um erro ao comunicar com o servidor.');
        } finally {
            // Restore UI State
            submitBtn.disabled = false;
            btnText.style.display = 'block';
            loader.style.display = 'none';
        }
    });
});
