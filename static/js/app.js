let chatSocket;
let retryCount = 0;
const maxRetries = 5;

// Get WebSocket URL
function getWebSocketUrl(room_name) {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${window.location.host}/ws/chat/${room_name}/`;
}

// Connect to WebSocket
function connectToChat(room_name) {
    if (!room_name) {
        console.error("room_name is missing. Cannot connect to WebSocket.");
        return;
    }

    console.log("Connecting to WebSocket:", room_name);
    const wsUrl = getWebSocketUrl(room_name);
    chatSocket = new WebSocket(wsUrl);

    chatSocket.onopen = function () {
        console.log("✅ WebSocket connected successfully.");
        retryCount = 0; // Reset retry count
    };

    chatSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log("📩 New message received:", data);

        if (data.type === "chat_message") {
            displayMessage(data.message, data.sender_id);
        }
    };

    chatSocket.onclose = function (event) {
        console.warn("❌ WebSocket closed:", event.reason);
        
        if (retryCount < maxRetries) {
            retryCount++;
            console.log(`🔄 Retrying WebSocket connection (${retryCount}/${maxRetries})...`);
            setTimeout(() => connectToChat(room_name), 5000);
        }
    };

    chatSocket.onerror = function (error) {
        console.error("⚠️ WebSocket error:", error);
    };
}

// Send message
function sendMessage(message, sender_id) {
    if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
        console.error("🚫 WebSocket is not open. Cannot send message.");
        return;
    }

    chatSocket.send(JSON.stringify({
        type: "chat_message",
        message: message,
        sender_id: sender_id,
    }));

    displayMessage(message, sender_id, true); // Show the message immediately
}

// Display message
function displayMessage(message, sender_id, isOwnMessage = false) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");

    const currentUserId = parseInt(document.getElementById("current-user-id").dataset.userId);  // Get user ID from HTML

    if (sender_id === currentUserId || isOwnMessage) {
        messageElement.classList.add("sent");
    } else {
        messageElement.classList.add("received");
    }

    messageElement.textContent = message;
    chatBox.appendChild(messageElement);

    // Auto-scroll to the latest message
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Initialize WebSocket on page load
document.addEventListener("DOMContentLoaded", function () {
    const roomNameElement = document.getElementById("room-name");
    if (roomNameElement) {
        const room_name = roomNameElement.dataset.roomName;
        connectToChat(room_name);
    } else {
        console.error("⚠️ Room name element not found.");
    }
});
