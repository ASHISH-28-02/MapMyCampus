// --- Configuration & Initialization ---
const BACKEND_URL = "https://mapmycampus.onrender.com";
const IISER_TVM_CENTER = { lat: 8.682478, lng: 77.135406 };

async function loadGoogleMaps() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/config`);
        const config = await response.json();
        const apiKey = config.Maps_api_key;
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initMap`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
    } catch (error) {
        console.error("Failed to load Google Maps:", error);
        document.getElementById("map").innerText = "Error: Could not load map configuration from the server.";
    }
}
loadGoogleMaps();

// --- Global Variables ---
let map, directionsService, directionsRenderer;
let activeMarkers = [];

// --- Map Initialization ---
function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 16, center: IISER_TVM_CENTER, mapTypeId: 'hybrid',
        disableDefaultUI: true, zoomControl: true, mapTypeControl: false,
        streetViewControl: false, fullscreenControl: true,
    });
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: false,
        polylineOptions: { strokeColor: "#00796B", strokeWeight: 6, strokeOpacity: 0.9 }
    });
    directionsRenderer.setMap(map);
    const collapseBtn = document.getElementById('collapse-btn');
    const chatContainer = document.getElementById('chat-container');
    collapseBtn.addEventListener('click', () => {
        chatContainer.classList.toggle('collapsed');
        setTimeout(() => {
            google.maps.event.trigger(map, 'resize');
            map.setCenter(IISER_TVM_CENTER);
        }, 300);
    });
    addMessage("Bot", 'Welcome! Ask for a location (e.g., "where is lhc?") or a route ("psb to bsb").');
}

// --- Map & Chat Functions ---
function clearMap() {
    activeMarkers.forEach(marker => marker.setMap(null));
    activeMarkers = [];
    directionsRenderer.setDirections({ routes: [] });
}

function showRoute(origin, destination) {
    const request = {
        origin: { lat: origin.lat, lng: origin.lng },
        destination: { lat: destination.lat, lng: destination.lng },
        travelMode: google.maps.TravelMode.WALKING
    };
    directionsService.route(request, (result, status) => {
        if (status === "OK") directionsRenderer.setDirections(result);
        else {
            console.error("Directions request failed due to " + status);
            addMessage("Bot", "😥 Could not calculate the route. Please try again.");
        }
    });
}

function showLocationMarker(loc) {
    map.setCenter({ lat: loc.lat, lng: loc.lng });
    map.setZoom(18);
    const marker = new google.maps.Marker({
        position: { lat: loc.lat, lng: loc.lng }, map, title: loc.name,
        animation: google.maps.Animation.DROP
    });
    activeMarkers.push(marker);
}

function sendMessage() {
    const input = document.getElementById("userInput");
    const msg = input.value.trim();
    if (!msg) return;
    addMessage("User", msg);
    input.value = "";
    handleQuery(msg);
}

function addMessage(sender, text, messageId = null) {
    const messagesContainer = document.getElementById("messages-container");
    const messageWrapper = document.createElement("div");
    if (messageId) messageWrapper.id = messageId;
    const isUser = sender === "User";
    messageWrapper.className = isUser ? 'message-wrapper user' : 'message-wrapper bot';
    messageWrapper.innerHTML = `
        <p class="message-sender">${sender}</p>
        <div class="message-bubble ${isUser ? 'user' : 'bot'}">
            <p class="message-text">${text}</p>
        </div>`;
    messagesContainer.appendChild(messageWrapper);
    messagesContainer.parentElement.scrollTop = messagesContainer.parentElement.scrollHeight;
}

function updateMessage(messageId, newHtml) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        const textElement = messageElement.querySelector('.message-text');
        if (textElement) {
            textElement.innerHTML = newHtml;
            textElement.classList.remove('thinking-bubble');
        }
    }
}

// --- Core Logic: Communicating with the Backend ---
async function handleQuery(msg) {
    const thinkingMsgId = `bot-msg-${Date.now()}`;
    addMessage("Bot", "<span class='thinking-bubble'>Thinking</span>", thinkingMsgId);

    try {
        const response = await fetch(`${BACKEND_URL}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: msg })
        });
        if (!response.ok) throw new Error(`Backend error: ${response.statusText}`);

        const data = await response.json();
        
        // The thinking bubble is always present, so clear the map only for map-related actions
        if (data.type === 'location' || data.type === 'route') {
            clearMap();
        }

        switch (data.type) {
            case 'location':
                showLocationMarker(data);
                updateMessage(thinkingMsgId, `📍 ${data.name} is marked on the map. <br><br> ${data.description}`);
                break;
            case 'route':
                showRoute(data.from, data.to);
                updateMessage(thinkingMsgId, `🗺️ Showing walking route from ${data.from.name} to ${data.to.name}.`);
                break;
            // *** NEW: Handle conversational messages from the bot ***
            case 'message':
                updateMessage(thinkingMsgId, data.message);
                break;
            case 'error':
                updateMessage(thinkingMsgId, data.message);
                break;
            default:
                throw new Error("Unknown response type from backend.");
        }
    } catch (error) {
        console.error("Failed to handle query:", error);
        updateMessage(thinkingMsgId, "😥 Sorry, something went wrong. I couldn't connect to my brain. Please try again later.");
    }
}
