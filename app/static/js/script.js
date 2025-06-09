document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const chatMessages = document.getElementById('chat-messages');
    const questionInput = document.getElementById('question-input');
    const sendButton = document.getElementById('send-btn');
    const fileInfo = document.getElementById('file-info');
    const filenameDisplay = document.getElementById('filename-display');
    const chunksDisplay = document.getElementById('chunks-display');
    
    let documentUploaded = false;
    let currentFileName = '';
    
    // Show filename immediately when a file is selected
    fileInput.addEventListener('change', function() {
        if (fileInput.files[0]) {
            currentFileName = fileInput.files[0].name;
            filenameDisplay.textContent = currentFileName;
            chunksDisplay.textContent = 'Ready to upload';
            chunksDisplay.className = 'chunks-info ready';
            fileInfo.classList.remove('hidden');
        } else {
            fileInfo.classList.add('hidden');
        }
    });
    
    // File upload handling
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!fileInput.files[0]) {
            showUploadStatus('Please select a file to upload.', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        currentFileName = fileInput.files[0].name;
        
        // Update chunks display to show processing
        chunksDisplay.textContent = 'Processing...';
        chunksDisplay.className = 'chunks-info';
        
        showUploadStatus('Uploading and processing document...', 'info');
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showUploadStatus(data.message, 'success');
                enableChat();
                
                // Update file info display
                filenameDisplay.textContent = currentFileName;
                chunksDisplay.textContent = `${data.chunks_count} chunks created`;
                fileInfo.classList.remove('hidden');
                
                // Add success message to chat
                addMessage(`Document "${currentFileName}" uploaded successfully. You can now ask questions.`, 'system');
            } else {
                showUploadStatus(data.error || 'Unknown error occurred.', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showUploadStatus('Error uploading file: ' + error.message, 'error');
        });
    });
    
    // File drag and drop
    const fileUpload = document.querySelector('.file-upload');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUpload.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileUpload.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileUpload.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        fileUpload.classList.add('highlight');
    }
    
    function unhighlight() {
        fileUpload.classList.remove('highlight');
    }
    
    fileUpload.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        // Update file info display when a file is dropped
        if (files.length > 0) {
            currentFileName = files[0].name;
            filenameDisplay.textContent = currentFileName;
            chunksDisplay.textContent = 'Ready to upload';
            chunksDisplay.className = 'chunks-info ready';
            fileInfo.classList.remove('hidden');
        }
    }
    
    // Chat handling
    sendButton.addEventListener('click', sendQuestion);
    
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendQuestion();
        }
    });
    
    function sendQuestion() {
        const question = questionInput.value.trim();
        if (!question || !documentUploaded) return;
        
        // Add user's question to chat
        addMessage(question, 'user');
        
        // Clear input
        questionInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot typing';
        typingIndicator.innerHTML = '<p><em>Thinking...</em></p>';
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Set message status
        sendButton.disabled = true;
        
        // Send question to backend
        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => {
            // Check for response status
            console.log('Response status:', response.status);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Error response:', text);
                    throw new Error('Network response was not ok: ' + response.status);
                });
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            chatMessages.removeChild(typingIndicator);
            
            // Check if we have a valid answer
            if (!data.answer) {
                throw new Error('No answer received from server');
            }
            
            // Add bot's response to chat
            addMessage(data.answer, 'bot');
            
            // Re-enable send button
            sendButton.disabled = false;
        })
        .catch(error => {
            // Remove typing indicator if it still exists
            if (typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            console.error('Error:', error);
            addMessage('Error: ' + error.message + '. Please check the console for details.', 'system');
            
            // Re-enable send button
            sendButton.disabled = false;
        });
    }
    
    function addMessage(text, type) {
        const message = document.createElement('div');
        message.className = `message ${type}`;
        
        // For bot messages, we parse markdown-like formatting
        if (type === 'bot') {
            // Basic markdown parsing (you can enhance this)
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                       .replace(/\*(.*?)\*/g, '<em>$1</em>')
                       .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
                       .replace(/`(.*?)`/g, '<code>$1</code>')
                       .replace(/\n/g, '<br>');
            
            message.innerHTML = `<p>${text}</p>`;
        } else {
            message.innerHTML = `<p>${text}</p>`;
        }
        
        chatMessages.appendChild(message);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function enableChat() {
        documentUploaded = true;
        questionInput.disabled = false;
        sendButton.disabled = false;
        questionInput.placeholder = "Ask a question about your document...";
    }
    
    function showUploadStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = `status ${type}`;
    }
});
