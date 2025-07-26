// --- THREE.JS IMPORTS ---
// Note: These are ES6 module imports. Your HTML must include <script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

// --- ORIGINAL CHATBOT & UI SCRIPT ---
const BACKEND_URL = "https://mapmycampus.onrender.com";
const micBtn = document.getElementById('mic-btn');
const userInput = document.getElementById("userInput");
const messagesContainer = document.getElementById("messages-container");
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const collapseBtn = document.getElementById('collapse-btn');
const chatContainer = document.getElementById('chat-container');
const modelViewer = document.querySelector('#map');

themeToggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
    // Also update tour background if it's active
    if (tourInitialized && scene) {
        scene.background = new THREE.Color(document.body.classList.contains('dark-mode') ? 0x0a0a2a : 0x87ceeb);
    }
});

collapseBtn.addEventListener('click', () => {
    const isCurrentlyCollapsed = chatContainer.classList.contains('collapsed');
    if (isCurrentlyCollapsed && document.body.classList.contains('tour-active')) {
        endTour();
    }
    chatContainer.classList.toggle('collapsed');
});

window.onload = () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') document.body.classList.add('dark-mode');
    addMessage("Bot", 'Welcome to the 3D View! Click "Start Tour" for a cinematic fly-through, or ask me anything about the campus.');
};

function sendMessage() {
    const msg = userInput.value.trim();
    if (!msg) return;
    addMessage("User", msg);
    userInput.value = "";
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    // handleQuery(msg); // Placeholder for your backend logic
}

function addMessage(sender, text, messageId = null) {
    const messageWrapper = document.createElement("div");
    if (messageId) messageWrapper.id = messageId;
    const isUser = sender === "User";
    messageWrapper.className = `message-wrapper ${isUser ? 'user' : 'bot'}`;
    const controlsHTML = isUser ? '' : `<div class="message-controls"><button class="speaker-btn" title="Read out loud"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path></svg></button><button class="stop-btn" title="Stop reading"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h12v12H6z"></path></svg></button></div>`;
    messageWrapper.innerHTML = `<p class="message-sender">${sender}</p><div class="message-bubble ${isUser ? 'user' : 'bot'}"><p class="message-text">${text}</p></div>${controlsHTML}`;
    messagesContainer.appendChild(messageWrapper);
    messagesContainer.parentElement.scrollTop = messagesContainer.parentElement.scrollHeight;
}

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
        hotspot.addEventListener('mouseover', () => { if(annotation) annotation.style.visibility = 'visible'; });
        hotspot.addEventListener('mouseout', () => { if(annotation) annotation.style.visibility = 'hidden'; });
        hotspot.addEventListener('focus', () => { if(annotation) annotation.style.visibility = 'visible'; });
        hotspot.addEventListener('blur', () => { if(annotation) annotation.style.visibility = 'hidden'; });
        hotspot.addEventListener('click', () => { if (annotation) queryFromHotspot(annotation.innerText); });
    });
});

// --- CINEMATIC TOUR LOGIC ---
const tourBtn = document.getElementById('tour-btn');
const mapWrapper = document.getElementById('map-wrapper');
const tourCanvas = document.getElementById('tour-canvas');
const tourLoader = document.getElementById('loader-container');

let tourInitialized = false;
let animationFrameId;
let scene, camera, renderer, labelRenderer, clock, cameraPath, parsedHotspots;

// Define the indices of the hotspots that are part of the tour
const tourStopIndices = [0, 1, 2, 3, 8, 9, 11, 12, 15, 16, 20, 17, 18, 23, 22];

tourBtn.addEventListener('click', () => {
    document.body.classList.contains('tour-active') ? endTour() : startTour();
});

/**
 * Creates a randomized camera path for the tour.
 * It picks a random starting point from the tourStopIndices, reorders the tour sequence,
 * and generates a smooth Catmull-Rom curve for the camera to follow.
 */
function createRandomizedTourPath() {
    if (!parsedHotspots || parsedHotspots.length === 0) return;

    // 1. Pick a random starting index from our defined tour stops
    const randomStartIndex = Math.floor(Math.random() * tourStopIndices.length);

    // 2. "Rotate" the array of indices to start from the random point
    const rotatedIndices = tourStopIndices.slice(randomStartIndex).concat(tourStopIndices.slice(0, randomStartIndex));
    
    // 3. Map these indices to the actual hotspot data to create the new sequence
    const tourSequence = rotatedIndices.map(index => parsedHotspots[index]);

    // 4. Create the spline curve for the camera to follow
    // We add an offset to fly slightly above the hotspot positions and subtract the model's center
    const pathPoints = tourSequence.map(hotspot => 
        hotspot.position.clone().add(new THREE.Vector3(0, 30, 0)).sub(scene.userData.center)
    );

    // Create a closed Catmull-Rom curve, which will loop smoothly
    cameraPath = new THREE.CatmullRomCurve3(pathPoints, true);
}

/**
 * Starts the cinematic tour.
 * If it's the first time, it initializes the entire Three.js scene.
 * Otherwise, it just creates a new random path and restarts the animation.
 */
function startTour() {
    chatContainer.classList.add('collapsed');
    document.body.classList.add('tour-active');

    if (!tourInitialized) {
        initTour();
    } else {
        // If tour is already initialized, just create a new random path and restart the clock
        createRandomizedTourPath();
        if (clock) {
            clock.stop();
            clock.start();
        }
        animateTour();
    }
}

/**
 * Ends the cinematic tour and cleans up resources.
 */
function endTour() {
    document.body.classList.remove('tour-active');
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
    if(clock) clock.stop();
    
    // Clean up the label renderer's DOM element to prevent duplicates
    if (labelRenderer && labelRenderer.domElement.parentNode) {
        labelRenderer.domElement.parentNode.removeChild(labelRenderer.domElement);
    }
    
    // Reset state. We keep the scene and its contents in memory for faster restart,
    // but mark it as not initialized to handle re-adding the DOM element.
    tourInitialized = false; 
    labelRenderer = null;
}

/**
 * Initializes the Three.js scene, camera, renderer, lights, and loads the 3D model.
 * This is only called once when the tour is first started.
 */
function initTour() {
    tourLoader.classList.add('visible');
    scene = new THREE.Scene();
    scene.userData = {}; // An object to store custom data like the model's center

    // Set background color based on current theme
    if (document.body.classList.contains('dark-mode')) {
        scene.background = new THREE.Color(0x0a0a2a);
    } else {
        scene.background = new THREE.Color(0x87ceeb);
    }

    // Setup camera and WebGL renderer
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 4000);
    renderer = new THREE.WebGLRenderer({ canvas: tourCanvas, antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Setup the CSS2D renderer for labels
    labelRenderer = new CSS2DRenderer();
    labelRenderer.setSize(window.innerWidth, window.innerHeight);
    labelRenderer.domElement.style.position = 'absolute';
    labelRenderer.domElement.style.top = '0px';
    labelRenderer.domElement.style.pointerEvents = 'none';
    mapWrapper.appendChild(labelRenderer.domElement);

    // Setup lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
    directionalLight.position.set(-100, 100, 50);
    scene.add(directionalLight);

    if (document.body.classList.contains('dark-mode')) {
        ambientLight.color.setHex(0x404060);
        directionalLight.intensity = 0.5;
    }

    // Hotspot data for tour and labels
    const hotspotData = [ { name: "IISER TVM Second gate", pos: "78.99m 116.16m 460.25m" }, { name: "Indoor Sports Complex", pos: "193.14m 128.21m 526.31m" }, { name: "Anamudi Block", pos: "318.45m 137.27m 549.39m" }, { name: "PhD Hostel Block 5", pos: "312.38m 129.25m 382.30m" }, { name: "PhD Hostel Block 4", pos: "327.43m 142.19m 348.86m" }, { name: "PhD Hostel Block 3", pos: "249.41m 134.82m 298.40m" }, { name: "PhD Hostel Block 6", pos: "235.95m 119.93m 332.48m" }, { name: "Agasthya", pos: "359.33m 149.36m 329.97m" }, { name: "Ponmudi", pos: "280.47m 146.58m 271.49m" }, { name: "Central Dining Hall", pos: "347.53m 154.65m 276.91m" }, { name: "IISER Substation 2", pos: "406.22m 158.24m 293.27m" }, { name: "Animal House", pos: "500.53m 196.21m 208.16m" }, { name: "Dept. of Biological Sciences", pos: "417.93m 190.55m 152.58m" }, { name: "Dept. of Chemical Sciences", pos: "320.62m 172.92m 101.76m" }, { name: "MOBEL Lab", pos: "258.20m 159.48m 97.95m" }, { name: "Dept. of Physical Sciences", pos: "196.87m 166.10m 59.70m" }, { name: "Lecture Hall Complex", pos: "176.71m 166.55m -43.85m" }, { name: "Shopping Complex", pos: "-62.55m 147.33m -109.67m" }, { name: "Health Centre", pos: "-92.75m 138.40m -42.56m" }, { name: "Visitors Forest Retreat", pos: "-31.60m 136.84m 86.18m" }, { name: "Central Library", pos: "70.30m 146.46m 143.39m" }, { name: "Tasty Restaurant", pos: "117.65m 134.44m 217.22m" }, { name: "Residence Block", pos: "-711.03m 121.53m -306.61m" }, { name: "Director's Bungalow", pos: "-559.21m 168.22m -363.05m" }, { name: "IISER Substation 3", pos: "-649.36m 151.16m -414.41m" } ];
    const parsePosition = (posString) => { const [x, y, z] = posString.replace(/m/g, '').split(' ').map(Number); return new THREE.Vector3(x, y, z); };
    
    // Populate the globally scoped parsedHotspots variable
    parsedHotspots = hotspotData.map(data => ({ name: data.name, position: parsePosition(data.pos) }));

    // Setup GLTF model loader with DRACO compression
    const modelURL = 'IISER.glb';
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/libs/draco/gltf/');
    const loader = new GLTFLoader();
    loader.setDRACOLoader(dracoLoader);

    loader.load(modelURL, (gltf) => {
        const campusModel = gltf.scene;
        const box = new THREE.Box3().setFromObject(campusModel);
        const center = box.getCenter(new THREE.Vector3());

        // Store the center point on the scene's userData for access in other functions
        scene.userData.center = center;
        
        // Center the model in the scene
        campusModel.position.sub(center);
        scene.add(campusModel);

        // Create and add labels for each hotspot
        parsedHotspots.forEach(hotspot => {
            const hotspotDiv = document.createElement('div');
            hotspotDiv.className = 'hotspot tour-label';
            const annotationDiv = document.createElement('div');
            annotationDiv.className = 'hotspot-annotation';
            annotationDiv.textContent = hotspot.name;
            annotationDiv.style.visibility = 'visible';
            hotspotDiv.appendChild(annotationDiv);
            const label = new CSS2DObject(hotspotDiv);
            label.position.copy(hotspot.position).sub(center);
            scene.add(label);
        });
        
        // Create the initial randomized tour path
        createRandomizedTourPath();
        
        tourLoader.classList.remove('visible');
        tourInitialized = true;
        clock = new THREE.Clock();
        animateTour();

    }, undefined, (error) => {
        console.error("Tour model loading error:", error);
        tourLoader.innerHTML = 'Error: Could not load tour.';
        endTour();
    });
}

/**
 * The main animation loop for the tour.
 */
function animateTour() {
    animationFrameId = requestAnimationFrame(animateTour);
    const elapsedTime = clock.getElapsedTime();
    if (cameraPath) {
        const loopTime = 90; // Duration of one full loop in seconds
        const progress = (elapsedTime % loopTime) / loopTime;
        
        // Get current position and a point slightly ahead to look at
        const cameraPos = cameraPath.getPointAt(progress);
        const lookAtPos = cameraPath.getPointAt((progress + 0.005) % 1);

        if (!cameraPos.equals(lookAtPos)) {
            camera.position.copy(cameraPos);
            camera.lookAt(lookAtPos);
        }
    }
    // Render both the 3D scene and the 2D labels
    renderer.render(scene, camera);
    if (labelRenderer) {
        labelRenderer.render(scene, camera);
    }
}

/**
 * Handles window resize events to keep the tour viewport correct.
 */
function onWindowResize() {
    if (tourInitialized && camera && renderer && labelRenderer) {
        const w = window.innerWidth;
        const h = window.innerHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
        labelRenderer.setSize(w, h);
    }
}
window.addEventListener('resize', onWindowResize);
