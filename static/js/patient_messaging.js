document.addEventListener("DOMContentLoaded", function () {
  const baseUrl = window.location.origin;
  const token = localStorage.getItem("access_token");
  let currentRecipient = null;

  // DOM Elements
  const messagingContainer = document.getElementById('messaging-container');
  const conversationList = document.getElementById('conversation-list');
  const messageList = document.getElementById('message-list');
  const messageInput = document.getElementById('message-input');
  const fileInput = document.getElementById('file-input');
  const sendButton = document.getElementById('send-button');
  const newMessageButton = document.getElementById('new-message-button');
  const searchInput = document.getElementById('search-contacts');

  async function getPatientProfile() {
    try {
      const response = await fetch(`${baseUrl}/api/users/patient/profile/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error('Failed to fetch patient data');
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function getConversations() {
    try {
      const response = await fetch(`${baseUrl}/api/users/messages/conversations/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        renderConversations(data);
      } else {
        throw new Error('Failed to fetch conversations');
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function getMessages(userId) {
    try {
      const response = await fetch(`${baseUrl}/api/users/messages/ ${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        renderMessages(data);
        currentRecipient = userId;
      } else {
        throw new Error('Failed to fetch messages');
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function sendMessage() {
    const content = messageInput.value.trim();
    const file = fileInput.files[0];
    
    if (!content && !file) return;

    const formData = new FormData();
    if (content) formData.append('content', content);
    if (file) formData.append('file', file);
    formData.append('recipient_id', currentRecipient);

    try {
      const response = await fetch(`${baseUrl}/api/users/messages/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        messageInput.value = '';
        fileInput.value = '';
        getMessages(currentRecipient);
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error(error);
    }
  }

  function renderConversations(conversations) {
    conversationList.innerHTML = '';
    
    conversations.forEach(conversation => {
      const conversationElement = document.createElement('div');
      conversationElement.className = `p-3 border-b border-gray-200 cursor-pointer hover:bg-gray-50 flex items-center ${
        conversation.unread_count > 0 ? 'bg-blue-50' : ''
      }`;
      conversationElement.innerHTML = `
        <div class="flex-shrink-0 h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
          ${conversation.other_user.first_name.charAt(0)}${conversation.other_user.last_name.charAt(0)}
        </div>
        <div class="ml-3 flex-1 overflow-hidden">
          <div class="flex justify-between items-center">
            <h3 class="text-sm font-medium text-gray-900 truncate">
              Dr. ${conversation.other_user.first_name} ${conversation.other_user.last_name}
            </h3>
            <span class="text-xs text-gray-500">${new Date(conversation.last_message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
          </div>
          <p class="text-sm text-gray-500 truncate">${conversation.last_message.content || 'Attachment'}</p>
          ${conversation.unread_count > 0 ? `<span class="inline-block bg-blue-500 text-white text-xs px-2 py-1 rounded-full">${conversation.unread_count}</span>` : ''}
        </div>
      `;
      conversationElement.addEventListener('click', () => getMessages(conversation.other_user.id));
      conversationList.appendChild(conversationElement);
    });
  }

  function renderMessages(messages) {
    messageList.innerHTML = '';
    
    messages.forEach(message => {
      const messageElement = document.createElement('div');
      messageElement.className = `mb-4 flex ${message.sender.id === currentUser.id ? 'justify-end' : 'justify-start'}`;
      
      let contentHtml = '';
      if (message.content) {
        contentHtml = `<p class="text-gray-800">${message.content}</p>`;
      } else if (message.file) {
        if (message.message_type === 'image') {
          contentHtml = `<img src="${message.file_url}" alt="Attachment" class="max-w-xs rounded-lg">`;
        } else {
          contentHtml = `<a href="${message.file_url}" class="text-blue-500 hover:underline" download>Download file</a>`;
        }
      } else if (message.video) {
        contentHtml = `
          <video controls class="max-w-xs">
            <source src="${message.video_url}" type="video/mp4">
            Your browser does not support the video tag.
          </video>
        `;
      } else if (message.link) {
        contentHtml = `<a href="${message.link}" target="_blank" class="text-blue-500 hover:underline">${message.link}</a>`;
      }
      
      messageElement.innerHTML = `
        <div class="${message.sender.id === currentUser.id ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'} rounded-lg py-2 px-4 max-w-xs">
          ${contentHtml}
          <div class="text-xs mt-1 ${message.sender.id === currentUser.id ? 'text-blue-100' : 'text-gray-500'}">
            ${new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
        </div>
      `;
      messageList.appendChild(messageElement);
    });
    
    // Scroll to bottom
    messageList.scrollTop = messageList.scrollHeight;
  }

  // Event Listeners
  sendButton.addEventListener('click', sendMessage);
  messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // Initialize
  getConversations();
});