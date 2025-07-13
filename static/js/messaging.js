document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const conversationsList = document.getElementById('conversations-list');
    const messagesContainer = document.getElementById('messages-container');
    const noMessages = document.getElementById('no-messages');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const fileUpload = document.getElementById('file-upload');
    const recipientId = document.getElementById('recipient-id');
    const partnerName = document.getElementById('partner-name');
    const partnerRole = document.getElementById('partner-role');
    const partnerAvatar = document.getElementById('partner-avatar');
    const unreadCount = document.getElementById('unread-count');
    
    // Current user data (you would get this from your auth system)
    const currentUser = {
        id: 1, // This should come from your authentication
        role: 'doctor' // or 'patient'
    };
    
    // API Base URL
 const baseUrl = window.location.origin;
  const token = localStorage.getItem("access_token");
    
    // Load conversations on page load
    loadConversations();
    
    // Load all conversations for the user
    async function loadConversations() {
        try {
            const response = await fetch(`${API_BASE}/conversations/`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!response.ok) throw new Error('Failed to load conversations');
            
            const conversations = await response.json();
            renderConversations(conversations);
        } catch (error) {
            console.error('Error loading conversations:', error);
            alert('Failed to load conversations');
        }
    }
    
    // Render conversations list
    function renderConversations(conversations) {
        conversationsList.innerHTML = '';
        
        if (conversations.length === 0) {
            conversationsList.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    No conversations yet
                </div>
            `;
            return;
        }
        
        conversations.forEach(convo => {
            const convoElement = document.createElement('div');
            convoElement.className = `p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 flex items-center ${convo.unread_count > 0 ? 'bg-blue-50' : ''}`;
            convoElement.innerHTML = `
                <img src="${convo.partner.profile_picture || 'https://via.placeholder.com/40'}" 
                     class="w-10 h-10 rounded-full mr-3">
                <div class="flex-1">
                    <div class="flex justify-between items-center">
                        <h3 class="font-medium">${convo.partner.first_name} ${convo.partner.last_name}</h3>
                        <span class="text-xs text-gray-500">${formatTime(convo.last_message?.timestamp)}</span>
                    </div>
                    <p class="text-sm text-gray-500 truncate">${getMessagePreview(convo.last_message)}</p>
                </div>
                ${convo.unread_count > 0 ? 
                    `<span class="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">${convo.unread_count}</span>` : ''}
            `;
            
            convoElement.addEventListener('click', () => {
                loadConversation(convo.partner.id, convo.partner);
            });
            
            conversationsList.appendChild(convoElement);
        });
    }
    
    // Load a specific conversation
    async function loadConversation(partnerId, partnerData = null) {
        try {
            // If we don't have partner data, fetch it
            if (!partnerData) {
                const partnerResponse = await fetch(`${API_BASE}/users/${partnerId}/`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                partnerData = await partnerResponse.json();
            }
            
            // Update UI with partner info
            recipientId.value = partnerId;
            partnerName.textContent = `${partnerData.first_name} ${partnerData.last_name}`;
            partnerRole.textContent = partnerData.role === 'doctor' ? 'Doctor' : 'Patient';
            partnerAvatar.src = partnerData.profile_picture || 'https://via.placeholder.com/40';
            
            // Load messages
            const response = await fetch(`${API_BASE}/conversations/${partnerId}/`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!response.ok) throw new Error('Failed to load messages');
            
            const messages = await response.json();
            renderMessages(messages);
            
            // Mark messages as read
            await fetch(`${API_BASE}/messages/mark-read/${partnerId}/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            // Reload conversations to update unread counts
            loadConversations();
            
        } catch (error) {
            console.error('Error loading conversation:', error);
            alert('Failed to load conversation');
        }
    }
    
    // Render messages in the chat area
    function renderMessages(messages) {
        noMessages.classList.add('hidden');
        messagesContainer.innerHTML = '';
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="flex justify-center items-center h-full text-gray-400">
                    No messages yet. Start the conversation!
                </div>
            `;
            return;
        }
        
        messages.forEach(message => {
            const isCurrentUser = message.sender.id === currentUser.id;
            const messageElement = document.createElement('div');
            messageElement.className = `flex mb-4 ${isCurrentUser ? 'justify-end' : 'justify-start'}`;
            
            messageElement.innerHTML = `
                <div class="${isCurrentUser ? 'bg-blue-500 text-white' : 'bg-white'} rounded-lg p-3 max-w-xs lg:max-w-md shadow">
                    ${renderMessageContent(message)}
                    <div class="text-xs mt-1 ${isCurrentUser ? 'text-blue-100' : 'text-gray-500'}">
                        ${formatTime(message.timestamp)}
                        ${message.is_read ? '<i class="fas fa-check ml-1"></i>' : ''}
                    </div>
                </div>
            `;
            
            messagesContainer.appendChild(messageElement);
        });
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Handle different message types
    function renderMessageContent(message) {
        switch(message.message_type) {
            case 'image':
                return `<img src="${message.file}" class="rounded max-w-full h-auto">`;
            case 'file':
                return `
                    <div class="flex items-center">
                        <i class="fas fa-file-alt text-xl mr-2"></i>
                        <a href="${message.file}" download class="underline">Download file</a>
                    </div>
                `;
            case 'video':
                return `
                    <video controls class="rounded max-w-full">
                        <source src="${message.video}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                `;
            case 'link':
                return `<a href="${message.link}" target="_blank" class="underline">${message.link}</a>`;
            default:
                return `<p>${message.content}</p>`;
        }
    }
    
    // Handle message submission
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('recipient_id', recipientId.value);
        
        if (messageInput.value) {
            formData.append('content', messageInput.value);
        }
        
        if (fileUpload.files[0]) {
            formData.append('file', fileUpload.files[0]);
        }
        
        try {
            const response = await fetch(`${API_BASE}/messages/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (!response.ok) throw new Error('Failed to send message');
            
            // Clear input and reload messages
            messageInput.value = '';
            fileUpload.value = '';
            loadConversation(recipientId.value);
            
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    });
    
    // Helper functions
    function formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    function getMessagePreview(message) {
        if (!message) return 'No messages yet';
        
        switch(message.message_type) {
            case 'image': return '📷 Image';
            case 'file': return '📄 File';
            case 'video': return '🎥 Video';
            case 'link': return '🔗 Link';
            default: return message.content || 'Message';
        }
    }
    
    // Poll for new messages (simplified version)
    setInterval(() => {
        if (recipientId.value) {
            loadConversation(recipientId.value);
        }
    }, 10000); // Poll every 10 seconds
});