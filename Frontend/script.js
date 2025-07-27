// --- SCENE SETUP ---
let scene, camera, renderer, plane, particles;
let clock = new THREE.Clock();
const simplex = new SimplexNoise();
const mouse = new THREE.Vector2();

function init() {
    // Scene
    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x020A14, 5, 15);

    // Camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 3, 5);
    camera.lookAt(scene.position);

    // Renderer
    const canvas = document.getElementById('webgl-canvas');
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // --- OBJECT CREATION ---
    
    // Grid
    const grid = new THREE.GridHelper(50, 50, 0x102A43, 0x102A43);
    scene.add(grid);

    // Procedural Buildings (as a plane with displacement)
    const planeGeometry = new THREE.PlaneGeometry(50, 50, 200, 200);
    const planeMaterial = new THREE.MeshStandardMaterial({
        color: 0x00796B, // Your specified teal
        wireframe: true,
        transparent: true,
        opacity: 0.15,
        metalness: 0.1,
        roughness: 0.75,
    });
    plane = new THREE.Mesh(planeGeometry, planeMaterial);
    plane.rotation.x = -Math.PI / 2;
    scene.add(plane);
    
    // Particles
    const particleCount = 5000;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for(let i = 0; i < particleCount; i++) {
        positions[i*3] = (Math.random() - 0.5) * 50;
        positions[i*3+1] = Math.random() * 5;
        positions[i*3+2] = (Math.random() - 0.5) * 50;
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
        color: 0x00796B, // Your specified teal
        size: 0.02,
        transparent: true,
        opacity: 0.5,
        blending: THREE.AdditiveBlending
    });
    particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // Lighting
    const directionalLight = new THREE.DirectionalLight(0x00796B, 1); // Your specified teal
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);
    
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);

    // --- EVENT LISTENERS ---
    window.addEventListener('resize', onWindowResize, false);
    document.addEventListener('mousemove', onMouseMove, false);

    // Start animation loop
    animate();
}

// --- ANIMATION LOOP ---
function animate() {
    requestAnimationFrame(animate);

    const time = clock.getElapsedTime();

    // Animate terrain vertices
    const vertices = plane.geometry.attributes.position.array;
    for (let i = 0; i < vertices.length; i += 3) {
        const x = vertices[i];
        const y = vertices[i + 1];
        
        let noise = simplex.noise3D(x * 0.1, y * 0.1, time * 0.1);
        
        // Quantize noise for blocky buildings
        noise = Math.round(noise * 5) / 5;
        if (noise < 0.3) noise = 0;
        
        vertices[i + 2] = noise * 2; // z-coordinate (height)
    }
    plane.geometry.attributes.position.needsUpdate = true;
    plane.geometry.computeVertexNormals();
    
    // Animate particles
    particles.position.y = (time * 0.1) % 5 - 2.5;

    // Animate camera
    camera.position.x += (mouse.x * 2 - camera.position.x) * 0.02;
    camera.position.y += (-mouse.y * 1 + 3 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
}

// --- EVENT HANDLERS ---
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function onMouseMove(event) {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
}

// --- INITIALIZE ---
init();

// --- REPEATING SCROLL ANIMATION LOGIC ---
const sectionsToAnimate = document.querySelectorAll('.info-section:not(.hero-section)');

const observerOptions = {
  root: null, 
  rootMargin: '0px',
  threshold: 0.25 // A good balance for triggering
};

const observer = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    // If the section is in view, add the class to trigger the animation
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
    } else {
      // If the section is out of view, remove the class to reset the animation
      entry.target.classList.remove('is-visible');
    }
  });
}, observerOptions);

sectionsToAnimate.forEach(section => {
  observer.observe(section);
});

// --- EASTER EGG: DANGER THEME ON 5 CLICKS (INDIVIDUAL CARDS) ---

// A reusable function to change the theme to red
/**
 * Activates the "Danger" theme (red).
 */
// --- SETUP: Store original colors before any changes ---
const originalColor = getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim();
const dangerRed = '#E53935';
const sciFiViolet = '#9D00FF' // Changed from lavender to pink

/**
 * A general function to set the color theme for the UI and the Three.js scene.
 * @param {string} color - The hex color code to apply.
 */
function setTheme(color) {
    // 1. Update the CSS root variable for the entire UI
    document.documentElement.style.setProperty('--accent-color', color);

    // 2. Update the colors in the Three.js scene
    const directionalLight = scene.children.find(child => child instanceof THREE.DirectionalLight);
    if (directionalLight) {
        directionalLight.color.set(color);
    }
    if (plane && plane.material) {
        plane.material.color.set(color);
    }
    if (particles && particles.material) {
        particles.material.color.set(color);
    }
}

/**
 * Toggles a theme on or off. If the theme is already active, it reverts to the original color.
 * @param {string} targetColor - The color of the theme to toggle.
 * @param {string} themeName - The name of the theme for logging.
 */
function toggleTheme(targetColor, themeName) {
    const currentColor = document.documentElement.style.getPropertyValue('--accent-color');

    // If the current theme is the one we're trying to activate, revert to original.
    if (currentColor === targetColor) {
        setTheme(originalColor);
        console.log(`${themeName} theme deactivated.`);
    } else { // Otherwise, set the new theme.
        setTheme(targetColor);
        console.log(`Secret ${themeName} theme activated!`);
    }
}

// --- EVENT LISTENERS ---

// Attach listener to Ashish's card to toggle Danger Mode
const ashishCard = document.getElementById('ashish-card');
if (ashishCard) {
    let clickCount = 0;
    ashishCard.addEventListener('click', () => {
        clickCount++;
        if (clickCount === 5) {
            toggleTheme(dangerRed, 'Danger');
            clickCount = 0; // Reset counter to allow toggling off later
        }
    });
}

// Attach listener to Rayhana's card to toggle Sci-Fi Violet Mode
const rayhanaCard = document.getElementById('rayhana-card');
if (rayhanaCard) {
    let clickCount = 0;
    rayhanaCard.addEventListener('click', () => {
        clickCount++;
        if (clickCount === 5) {
            toggleTheme(sciFiViolet, 'Sci-Fi Violet');
            clickCount = 0; // Reset counter to allow toggling off later
        }
    });
}