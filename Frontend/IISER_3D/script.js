// --- CHATBOT & THEME JAVASCRIPT ---
        const BACKEND_URL = "https://mapmycampus.onrender.com";
        const micBtn = document.getElementById('mic-btn');
        const userInput = document.getElementById("userInput");
        const messagesContainer = document.getElementById("messages-container");
        const themeToggleBtn = document.getElementById('theme-toggle-btn');
        const collapseBtn = document.getElementById('collapse-btn');
        const chatContainer = document.getElementById('chat-container');
        const modelViewer = document.querySelector('#map');

        // --- THEME TOGGLE LOGIC ---
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            // Save the user's preference to localStorage
            if (document.body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
        });

        // --- SPEECH SYNTHESIS & RECOGNITION ---
        function speakText(text) {
            const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu;
            const cleanText = text.replace(emojiRegex, '').replace(/<br>/g, '. ').replace(/<[^>]*>/g, '');
            if (!('speechSynthesis' in window)) { return; }
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
            setTimeout(speakMainUtterance, 100);
        }

        messagesContainer.addEventListener('click', function(event) {
            const speakerBtn = event.target.closest('.speaker-btn');
            const stopBtn = event.target.closest('.stop-btn');
            if (speakerBtn) {
                const textToSpeak = speakerBtn.closest('.message-wrapper').querySelector('.message-text').innerText;
                speakText(textToSpeak);
            }
            if (stopBtn) {
                if ('speechSynthesis' in window) {
                    speechSynthesis.cancel();
                }
            }
        });

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition;
        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'en-US';
            recognition.onresult = (event) => {
                userInput.value = event.results[0][0].transcript;
                micBtn.classList.remove('listening');
                sendMessage();
            };
            recognition.onend = () => micBtn.classList.remove('listening');
            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
                micBtn.classList.remove('listening');
            };
            micBtn.addEventListener('click', () => {
                if (!recognition) return;
                speechSynthesis.cancel();
                micBtn.classList.add('listening');
                recognition.start();
            });
        } else {
            if(micBtn) micBtn.style.display = 'none';
        }

        // --- UI & CHAT LOGIC ---
        collapseBtn.addEventListener('click', () => {
            chatContainer.classList.toggle('collapsed');
        });

        window.onload = () => {
            // Apply saved theme on load
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-mode');
            }
            const welcomeText = 'Welcome to the 3D View! Click on a location or ask me anything about the campus.';
            addMessage("Bot", welcomeText);
        };

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
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path></svg>
                    </button>
                    <button class="stop-btn" title="Stop reading">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h12v12H6z"></path></svg>
                    </button>
                </div>`;
            messageWrapper.innerHTML = `
                <p class="message-sender">${sender}</p>
                <div class="message-bubble ${isUser ? 'user' : 'bot'}"><p class="message-text">${text}</p></div>
                ${controlsHTML}`;
            messagesContainer.appendChild(messageWrapper);
            messagesContainer.parentElement.scrollTop = messagesContainer.parentElement.scrollHeight;
        }

        function updateMessage(messageId, newHtml) {
            const messageElement = document.getElementById(messageId);
            if (!messageElement) return;
            const textElement = messageElement.querySelector('.message-text');
            if (textElement) {
                textElement.innerHTML = newHtml;
                textElement.classList.remove('thinking-bubble');
            }
            if (!messageElement.querySelector('.message-controls')) {
                const controlsHTML = `
                    <div class="message-controls">
                        <button class="speaker-btn" title="Read out loud"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path></svg></button>
                        <button class="stop-btn" title="Stop reading"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h12v12H6z"></path></svg></button>
                    </div>`;
                messageElement.insertAdjacentHTML('beforeend', controlsHTML);
            }
        }

        function dropMarkerOnHotspot(query) {
            const normalizedQuery = query.toLowerCase().trim();
            const allHotspots = document.querySelectorAll('.hotspot');
            const marker = document.getElementById('marker');
            let foundHotspot = null;

            for (const hotspot of allHotspots) {
                const name = hotspot.dataset.name.toLowerCase();
                const aliases = (hotspot.dataset.aliases || '').split(',').map(a => a.trim().toLowerCase());
                const allNames = [name, ...aliases].filter(n => n);

                if (allNames.some(n => normalizedQuery.includes(n))) {
                    foundHotspot = hotspot;
                    break;
                }
            }

            if (foundHotspot) {
                marker.slot = foundHotspot.slot;
                marker.style.display = 'block';
            } else {
                marker.style.display = 'none';
            }
        }

        async function handleQuery(msg) {
            dropMarkerOnHotspot(msg);

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
                
                let botReplyText = "";
                switch (data.type) {
                    case 'location':
                        botReplyText = `📍 ${data.name} is marked on the map. ${data.description}`;
                        updateMessage(thinkingMsgId, botReplyText.replace(/\. /g, '. <br><br>'));
                        break;
                    case 'route':
                        botReplyText = `🗺️ To get from ${data.from.name} to ${data.to.name}, you would follow the route shown on the 2D map.`;
                        updateMessage(thinkingMsgId, botReplyText);
                        break;
                    case 'greeting':
                    case 'answer':
                    case 'error':
                        botReplyText = data.message;
                        updateMessage(thinkingMsgId, botReplyText);
                        break;
                    default:
                        throw new Error("Unknown response type from backend.");
                }
            } catch (error) {
                console.error("Failed to handle query:", error);
                const errorText = "😥 Sorry, something went wrong. I couldn't connect to my brain. Please try again later.";
                updateMessage(thinkingMsgId, errorText);
            }
        }

        // --- 3D MODEL & HOTSPOT LOGIC ---
        function queryFromHotspot(locationName) {
            if (chatContainer.classList.contains('collapsed')) {
                chatContainer.classList.remove('collapsed');
            }
            userInput.value = `${locationName}`;
            sendMessage();
        }

        modelViewer.addEventListener('load', () => {
            const hotspots = modelViewer.querySelectorAll('.hotspot');

            hotspots.forEach((hotspot) => {
                const annotation = hotspot.querySelector('.hotspot-annotation');

                hotspot.addEventListener('mouseover', () => {
                    if(annotation) annotation.style.visibility = 'visible';
                });
                hotspot.addEventListener('mouseout', () => {
                    if(annotation) annotation.style.visibility = 'hidden';
                });
                hotspot.addEventListener('focus', () => {
                    if(annotation) annotation.style.visibility = 'visible';
                });
                hotspot.addEventListener('blur', () => {
                    if(annotation) annotation.style.visibility = 'hidden';
                });

                hotspot.addEventListener('click', () => {
                    if (annotation) {
                        const locationName = annotation.innerText;
                        queryFromHotspot(locationName);
                    }
                });
            });
        });