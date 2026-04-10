class JarvisWebApp {
    constructor() {
        this.socket = io();
        this.currentChatId = null;
        this.chats = {};
        this.currentSessionId = null;
        this.isProcessing = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadChats();
        this.setupSocketListeners();
    }

    initializeElements() {
        this.chatList = document.getElementById('chat-list');
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.loadingOverlay = document.getElementById('loading-overlay');
    }

    bindEvents() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.newChatBtn.addEventListener('click', () => this.createNewChat());
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('agent_response', (data) => {
            this.handleAgentResponse(data);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
    }

    async loadChats() {
        try {
            const response = await fetch('/api/chats');
            this.chats = await response.json();
            this.renderChatList();
            
            // Load most recent chat or create new one
            const chatIds = Object.keys(this.chats);
            if (chatIds.length > 0) {
                this.loadChat(chatIds[chatIds.length - 1]);
            } else {
                this.createNewChat();
            }
        } catch (error) {
            console.error('Error loading chats:', error);
        }
    }

    renderChatList() {
        const chatIds = Object.keys(this.chats);
        
        if (chatIds.length === 0) {
            this.chatList.innerHTML = '<div class="no-chats">No chats yet</div>';
            return;
        }

        // Sort by creation time (newest first)
        chatIds.sort((a, b) => {
            const dateA = new Date(this.chats[a].created);
            const dateB = new Date(this.chats[b].created);
            return dateB - dateA;
        });

        this.chatList.innerHTML = chatIds.map(chatId => `
            <div class="chat-item ${chatId === this.currentChatId ? 'active' : ''}" data-chat-id="${chatId}">
                <div class="chat-item-content" onclick="app.loadChat('${chatId}')">
                    <div class="chat-item-title">${this.escapeHtml(this.chats[chatId].title)}</div>
                    <div class="chat-item-date">${this.chats[chatId].created}</div>
                </div>
                <button class="chat-item-delete" onclick="app.deleteChat('${chatId}', event)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    async loadChat(chatId) {
        try {
            const response = await fetch(`/api/chats/${chatId}`);
            if (!response.ok) {
                throw new Error('Chat not found');
            }
            
            this.currentChatId = chatId;
            const chat = await response.json();
            this.renderMessages(chat.messages);
            this.renderChatList();
            this.scrollToBottom();
        } catch (error) {
            console.error('Error loading chat:', error);
        }
    }

    renderMessages(messages) {
        this.chatMessages.innerHTML = messages.map(msg => `
            <div class="message ${msg.sender.toLowerCase() === 'you' ? 'user' : 'agent'}">
                <div class="message-sender">${msg.sender}</div>
                <div class="message-bubble">
                    <div class="message-text">${this.escapeHtml(msg.text)}</div>
                    <div class="message-actions">
                        <button class="copy-btn" onclick="app.copyToClipboard('${this.escapeHtml(msg.text)}')">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async createNewChat() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/chats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            this.chats[data.chat_id] = data.chat;
            this.loadChat(data.chat_id);
            this.renderChatList();
        } catch (error) {
            console.error('Error creating chat:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async deleteChat(chatId, event) {
        event.stopPropagation();
        
        if (!confirm('Are you sure you want to delete this chat?')) {
            return;
        }

        try {
            const response = await fetch(`/api/chats/${chatId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                delete this.chats[chatId];
                this.renderChatList();
                
                if (this.currentChatId === chatId) {
                    const chatIds = Object.keys(this.chats);
                    if (chatIds.length > 0) {
                        this.loadChat(chatIds[chatIds.length - 1]);
                    } else {
                        this.createNewChat();
                    }
                }
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isProcessing) {
            return;
        }

        if (!this.currentChatId) {
            await this.createNewChat();
        }

        // Add user message immediately
        this.addMessage('You', message, 'user');
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        this.setProcessingState(true);

        try {
            const response = await fetch(`/api/chats/${this.currentChatId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    sender: 'You'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.currentSessionId = data.session_id;
                // Add streaming agent bubble
                this.addStreamingBubble();
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.setProcessingState(false);
        }
    }

    addMessage(sender, text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <div class="message-sender">${sender}</div>
            <div class="message-bubble">
                <div class="message-text">${this.escapeHtml(text)}</div>
                <div class="message-actions">
                    <button class="copy-btn" onclick="app.copyToClipboard('${this.escapeHtml(text)}')">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addStreamingBubble() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message agent';
        messageDiv.id = 'streaming-message';
        messageDiv.innerHTML = `
            <div class="message-sender">Agent</div>
            <div class="message-bubble streaming">
                <div class="message-text">...</div>
                <div class="message-actions">
                    <button class="copy-btn" onclick="app.copyToClipboard(app.getStreamingText())">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    handleAgentResponse(data) {
        if (data.session_id !== this.currentSessionId) {
            return;
        }

        const streamingMessage = document.getElementById('streaming-message');
        if (streamingMessage) {
            const messageText = streamingMessage.querySelector('.message-text');
            
            if (data.type === 'stream') {
                // Update streaming text - ensure we don't duplicate content
                const currentText = messageText.textContent || '';
                const newMessage = data.message;
                
                // Only append if the new message isn't already at the end
                if (!currentText.endsWith(newMessage)) {
                    messageText.textContent = currentText + newMessage + '\n';
                }
            } else if (data.type === 'complete') {
                // Finalize the message in place without reloading
                streamingMessage.classList.remove('streaming');
                this.setProcessingState(false);
                this.currentSessionId = null;
                
                // Update the message ID to make it permanent
                streamingMessage.id = '';
                
                // Use the final text from backend if provided, otherwise use current text
                const finalText = data.message || messageText.textContent;
                messageText.textContent = finalText;
                
                // Update copy button to use the final text
                const copyBtn = streamingMessage.querySelector('.copy-btn');
                if (copyBtn) {
                    copyBtn.setAttribute('onclick', `app.copyToClipboard('${this.escapeHtml(finalText)}')`);
                }
            } else if (data.type === 'error') {
                messageText.textContent = data.message;
                streamingMessage.classList.remove('streaming');
                this.setProcessingState(false);
                this.currentSessionId = null;
            }
            
            this.scrollToBottom();
        }
    }

    getStreamingText() {
        const streamingMessage = document.getElementById('streaming-message');
        if (streamingMessage) {
            const messageText = streamingMessage.querySelector('.message-text');
            return messageText.textContent;
        }
        return '';
    }

    setProcessingState(processing) {
        this.isProcessing = processing;
        this.sendBtn.disabled = processing;
        this.messageInput.disabled = processing;
        
        if (processing) {
            this.statusDot.style.color = '#f4a74a';
            this.statusText.textContent = 'Thinking...';
        } else {
            this.statusDot.style.color = '#4ec9b0';
            this.statusText.textContent = 'Idle';
        }
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Show success feedback
            const originalText = event.target.innerHTML;
            event.target.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                event.target.innerHTML = originalText;
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    }

    scrollToBottom() {
        const container = document.querySelector('.chat-container');
        container.scrollTop = container.scrollHeight;
    }

    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new JarvisWebApp();
});
