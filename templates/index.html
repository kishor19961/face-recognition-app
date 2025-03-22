<!DOCTYPE html>
<html lang="en">
<head>
    <!-- ... (keep the existing head and style sections the same) ... -->
</head>
<body>
    <!-- ... (keep the existing HTML structure the same until the script section) ... -->

    <script>
        let stream = null;
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const preview = document.getElementById('preview');
        const startButton = document.getElementById('startCamera');
        const captureButton = document.getElementById('capturePhoto');
        const retakeButton = document.getElementById('retakePhoto');
        const submitButton = document.getElementById('submitButton');
        const photoInput = document.getElementById('photoInput');

        startButton.addEventListener('click', async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: { exact: "environment" }, // This specifies the back camera
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                });
                video.srcObject = stream;
                startButton.disabled = true;
                captureButton.disabled = false;
                video.style.display = 'block';
                preview.style.display = 'none';
            } catch (err) {
                console.error('Error accessing camera:', err);
                // If back camera fails, try falling back to any available camera
                try {
                    stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        } 
                    });
                    video.srcObject = stream;
                    startButton.disabled = true;
                    captureButton.disabled = false;
                    video.style.display = 'block';
                    preview.style.display = 'none';
                } catch (fallbackErr) {
                    console.error('Error accessing any camera:', fallbackErr);
                    alert('Error accessing camera. Please make sure you have granted camera permissions and have a camera available.');
                }
            }
        });

        retakeButton.addEventListener('click', async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: { exact: "environment" }, // This specifies the back camera
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                });
                video.srcObject = stream;
                
                // Reset UI
                video.style.display = 'block';
                preview.style.display = 'none';
                captureButton.classList.remove('hidden');
                retakeButton.classList.add('hidden');
                submitButton.disabled = true;
                photoInput.value = '';
            } catch (err) {
                console.error('Error accessing camera:', err);
                // If back camera fails, try falling back to any available camera
                try {
                    stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        } 
                    });
                    video.srcObject = stream;
                    
                    // Reset UI
                    video.style.display = 'block';
                    preview.style.display = 'none';
                    captureButton.classList.remove('hidden');
                    retakeButton.classList.add('hidden');
                    submitButton.disabled = true;
                    photoInput.value = '';
                } catch (fallbackErr) {
                    console.error('Error accessing any camera:', fallbackErr);
                    alert('Error accessing camera. Please make sure you have granted camera permissions and have a camera available.');
                }
            }
        });

        // Keep the existing captureButton event listener
        captureButton.addEventListener('click', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            // Convert canvas to base64
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            photoInput.value = imageData;
            
            // Show preview
            preview.src = imageData;
            preview.style.display = 'block';
            video.style.display = 'none';
            
            // Update buttons
            captureButton.classList.add('hidden');
            retakeButton.classList.remove('hidden');
            submitButton.disabled = false;
            
            // Stop camera stream
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });

        // Keep the existing form submission event listener
        document.getElementById('recognitionForm').addEventListener('submit', function(e) {
            if (!photoInput.value) {
                e.preventDefault();
                alert('Please capture a photo before submitting.');
            }
        });
    </script>
</body>
</html>
