// --- Configuration & Initialization ---
        const BACKEND_URL = "https://mapmycampus.onrender.com";
        const DEFAULT_MAP_CENTER = { lat: 8.682478, lng: 77.135406 }; 

async function loadGoogleMaps() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/config`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const config = await response.json();
        const apiKey = config.Maps_api_key;
        if (!apiKey) {
            throw new Error("Maps API key not found in server configuration.");
        }
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initMap&libraries=marker`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
    } catch (error) {
        console.error("Failed to load Google Maps:", error);
        const mapDiv = document.getElementById("map");
        if(mapDiv) mapDiv.innerText = "Error: Could not load map configuration from the server.";
    }
}

// --- Global Variables & DOM Elements ---
let map, directionsService, directionsRenderer;
let activeMarkers = [];
const micBtn = document.getElementById('mic-btn');
const userInput = document.getElementById("userInput");
const messagesContainer = document.getElementById("messages-container");
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const collapseBtn = document.getElementById('collapse-btn');
const chatContainer = document.getElementById('chat-container');

// ===================================================================================
// === THEME MANAGEMENT ==============================================================
// ===================================================================================

// Apply saved theme on initial load
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
    }
    loadGoogleMaps();
});

// Theme toggle button event listener
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        // Save the user's preference to localStorage
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
}

// ===================================================================================
// === SPEECH TO TEXT & TEXT TO SPEECH ===============================================
// ===================================================================================

function speakText(text) {
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu;
    const cleanText = text.replace(emojiRegex, '').replace(/<br>/g, '. ').replace(/<[^>]*>/g, '');

    if (!('speechSynthesis' in window)) {
        console.warn("Speech Synthesis is not supported by this browser.");
        return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    const speakMainUtterance = () => {
        const voices = speechSynthesis.getVoices();
        if (voices.length === 0) {
            speechSynthesis.onvoiceschanged = () => {
                speechSynthesis.onvoiceschanged = null; 
                speechSynthesis.speak(utterance);
            };
        } else {
            speechSynthesis.speak(utterance);
        }
    };

    speechSynthesis.cancel();
    
    setTimeout(() => {
        speakMainUtterance();
    }, 100); 
}

// Event Listener for Speaker and Stop Buttons
if (messagesContainer) {
    messagesContainer.addEventListener('click', function(event) {
        const speakerBtn = event.target.closest('.speaker-btn');
        const stopBtn = event.target.closest('.stop-btn');

        if (speakerBtn) {
            const messageWrapper = speakerBtn.closest('.message-wrapper');
            const textToSpeak = messageWrapper.querySelector('.message-text').innerText;
            speakText(textToSpeak);
        }
        
        if (stopBtn) {
            if ('speechSynthesis' in window) {
                speechSynthesis.cancel();
            }
        }
    });
}

// Speech to Text (Voice Input)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        micBtn.classList.remove('listening');
        sendMessage(); // Automatically send after successful transcription
    };

    recognition.onend = () => {
        micBtn.classList.remove('listening');
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        micBtn.classList.remove('listening');
    };

    if (micBtn) {
        micBtn.addEventListener('click', () => {
            if (!recognition) return;
            speechSynthesis.cancel(); 
            micBtn.classList.add('listening');
            recognition.start();
        });
    }

} else {
    console.warn("Speech Recognition is not supported by this browser.");
    if(micBtn) micBtn.style.display = 'none';
}


// ===================================================================================
// === MAP INITIALIZATION & UI CONTROLS ==============================================
// ===================================================================================

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 16,
        center: DEFAULT_MAP_CENTER, 
        mapTypeId: 'hybrid',
        disableDefaultUI: true, zoomControl: true, mapTypeControl: false,
        streetViewControl: false, fullscreenControl: true,
    });
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: false,
        polylineOptions: { strokeColor: "#00A99D", strokeWeight: 6, strokeOpacity: 0.9 }
    });
    directionsRenderer.setMap(map);
    
    if (collapseBtn && chatContainer) {
        collapseBtn.addEventListener('click', () => {
            chatContainer.classList.toggle('collapsed');
            setTimeout(() => {
                google.maps.event.trigger(map, 'resize');
                map.setCenter(DEFAULT_MAP_CENTER); 
            }, 300); // Corresponds to the CSS transition time
        });
    }

    const welcomeText = 'Welcome! Ask for a location or a route on campus.';
    addMessage("Bot", welcomeText);
}

// ===================================================================================
// === MAP & CHAT FUNCTIONS ==========================================================
// ===================================================================================

function clearMap() {
    activeMarkers.forEach(marker => marker.setMap(null));
    activeMarkers = [];
    directionsRenderer.setDirections({ routes: [] });
}

/**
 * **NEW & IMPROVED:** This function now handles drawing the route on the map.
 * @param {object} origin - The starting location object {lat, lng, name}.
 * @param {object} destination - The ending location object {lat, lng, name}.
 */
function showRoute(origin, destination) {
    if (!directionsService || !directionsRenderer) {
        console.error("Directions services not initialized.");
        return;
    }

    const request = {
        origin: { lat: origin.lat, lng: origin.lng },
        destination: { lat: destination.lat, lng: destination.lng },
        travelMode: google.maps.TravelMode.WALKING
    };
    
    directionsService.route(request, (result, status) => {
        if (status === "OK") {
            directionsRenderer.setDirections(result);
        } else {
            console.error("Directions request failed due to " + status);
            const errorText = "😥 Could not calculate the route. Please try again.";
            addMessage("Bot", errorText);
        }
    });
}

function showLocationMarker(loc) {
    map.setCenter({ lat: loc.lat, lng: loc.lng });
    map.setZoom(18);
    const marker = new google.maps.marker.AdvancedMarkerElement({
        position: { lat: loc.lat, lng: loc.lng },
        map,
        title: loc.name,
    });
    activeMarkers.push(marker);
}

function sendMessage() {
    const msg = userInput.value.trim();
    if (!msg) return;
    addMessage("User", msg);
    userInput.value = "";
    speechSynthesis.cancel();
    handleQuery(msg);
}

function addMessage(sender, text, messageId = null) {
    const messageWrapper = document.createElement("div");
    if (messageId) messageWrapper.id = messageId;
    const isUser = sender === "User";
    messageWrapper.className = isUser ? 'message-wrapper user' : 'message-wrapper bot';
    
    const controlsHTML = isUser ? '' : `
        <div class="message-controls">
            <button class="speaker-btn" title="Read out loud">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path>
                </svg>
            </button>
            <button class="stop-btn" title="Stop reading">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 6h12v12H6z"></path>
                </svg>
            </button>
        </div>
    `;

    messageWrapper.innerHTML = `
        <p class="message-sender">${sender}</p>
        <div class="message-bubble ${isUser ? 'user' : 'bot'}">
            <p class="message-text">${text}</p>
        </div>
        ${controlsHTML}
    `;
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
        if (!messageElement.querySelector('.message-controls')) {
            const controlsHTML = `
                <div class="message-controls">
                    <button class="speaker-btn" title="Read out loud">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path>
                        </svg>
                    </button>
                    <button class="stop-btn" title="Stop reading">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M6 6h12v12H6z"></path>
                        </svg>
                    </button>
                </div>`;
            messageElement.insertAdjacentHTML('beforeend', controlsHTML);
        }
    }
}

// --- Core Logic: Communicating with the Backend ---
async function handleQuery(msg) {
    const thinkingMsgId = `bot-msg-${Date.now()}`;
    addMessage("Bot", "<span class='thinking-bubble'>...</span>", thinkingMsgId);

    try {
        const response = await fetch(`${BACKEND_URL}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: msg })
        });
        if (!response.ok) throw new Error(`Backend error: ${response.statusText}`);

        const data = await response.json();
        
        // Always clear the map if the query is for a location or route
        if (data.type === 'location' || data.type === 'route') {
            clearMap();
        }

        let botReplyText = ""; 

        switch (data.type) {
            case 'location':
                showLocationMarker(data);
                botReplyText = `📍 ${data.name} is marked on the map. ${data.description}`;
                updateMessage(thinkingMsgId, botReplyText.replace(/\. /g, '. <br><br>'));
                break;
            case 'route':
                // **THIS IS THE KEY LOGIC**
                // This case now calls the showRoute function with the data from the backend.
                showRoute(data.from, data.to);
                botReplyText = `🗺️ Showing walking route from ${data.from.name} to ${data.to.name}.`;
                updateMessage(thinkingMsgId, botReplyText);
                break;
            case 'greeting':
            case 'answer':
            case 'error':
                botReplyText = data.message;
                updateMessage(thinkingMsgId, botReplyText);
                break;
            default:
                console.error("Unknown response type from backend:", data.type);
                throw new Error("Unknown response type from backend.");
        }

    } catch (error) {
        console.error("Failed to handle query:", error);
        const errorText = "😥 Sorry, something went wrong. I couldn't connect to my brain. Please try again later.";
        updateMessage(thinkingMsgId, errorText);
    }
}
