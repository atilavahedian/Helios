// static/js/scripts.js

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const assignTaskBtn = document.querySelector('.action-button button');

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (message === "") return;

        // Append user message
        appendMessage('user', message);
        userInput.value = '';

        // Simulate bot response
        setTimeout(() => {
            appendMessage('bot', 'This is a placeholder response.');
        }, 1000);
    });

    assignTaskBtn.addEventListener('click', function() {
        const task = prompt("Enter the task you want to assign:");
        if (task) {
            appendMessage('user', `Assign task: ${task}`);

            // Simulate bot confirmation
            setTimeout(() => {
                appendMessage('bot', 'Task has been assigned successfully.');
            }, 1000);
        }
    });

    function appendMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);

        const header = document.createElement('div');
        header.classList.add('message-header');
        header.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Assistant'}</strong> <span class="timestamp">${getCurrentTime()}</span>`;

        const content = document.createElement('div');
        content.classList.add('message-content');
        content.innerText = message;

        messageElement.appendChild(header);
        messageElement.appendChild(content);
        chatBox.appendChild(messageElement);

        // Scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
});