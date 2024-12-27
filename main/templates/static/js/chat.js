// static/js/chat.js

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const websitePreview = document.getElementById('website-preview');
    const assignTaskBtn = document.getElementById('assign-task-btn');

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message === "") return;

        // Display user message
        appendMessage('user', message);
        userInput.value = '';

        // Send message to the server via AJAX
        fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // Display assistant's response
                appendMessage('bot', data.reply);

                // Update website preview if there's HTML content
                if (data.html_content) {
                    websitePreview.srcdoc = data.html_content;
                }

                // Optionally, update the progress bar based on response
                if (data.progress) {
                    updateProgressBar(data.progress);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });

    assignTaskBtn.addEventListener('click', function() {
        const task = prompt("Enter the task you want to assign:");
        if (task) {
            appendMessage('user', `Assign task: ${task}`);

            // Send task to the server via AJAX
            fetch('/assign-task/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ task: task })
                })
                .then(response => response.json())
                .then(data => {
                    appendMessage('bot', data.reply);

                    // Optionally, update the progress bar based on response
                    if (data.progress) {
                        updateProgressBar(data.progress);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }
    });

    function appendMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);

        const messageContent = document.createElement('div');
        messageContent.classList.add('message');
        messageContent.innerText = message;

        const timestamp = document.createElement('div');
        timestamp.classList.add('timestamp');
        const now = new Date();
        timestamp.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageElement.appendChild(messageContent);
        messageElement.appendChild(timestamp);
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function updateProgressBar(progress) {
        const progressBar = document.querySelector('.progress-bar');
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }

    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});