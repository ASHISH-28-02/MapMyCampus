# MapMyCampus Frontend 🗺️

This document provides a complete technical guide to the frontend of the MapMyCampus application. It covers both the 2D Google Maps interface and the 3D model viewer, with a focus on configuration and dependencies.

---

 ## Technologies Used 💻

* **HTML5/CSS3/ES6+ JavaScript:** The standard trio for the application's structure, style, and logic.
* **Google Maps JavaScript API:** Dynamically loaded to power the entire 2D map view, including markers, routing, and map tiles.
* **Google `<model-viewer>`:** A web component loaded directly from an `ajax.googleapis.com` CDN. This handles all the heavy lifting for rendering the `.glb` 3D model, camera controls, and AR functionality without needing a local 3D library like Three.js.
* **Web Speech API:** Used for both `SpeechRecognition` (voice input) and `SpeechSynthesis` (audio responses).

---

## Project Structure 📂

The file paths are relative. **Do not change this structure**, or the links between the 2D and 3D views will break.


.
├── index.html            # Main HTML file for the 2D Map View
├── script.js             # JavaScript for the 2D Map View
├── style.css             # CSS for 2D view
├── IISER/
│   ├── campus.html       # HTML file for the 3D Viewer
│   ├── script.js         # JavaScript for the 3D Viewer
│   ├── style.css         # CSS for 2D view
│   └── IISER.glb         # The 3D model file (CRITICAL ASSET)   
└── README.md             # This file


---
## Frontend Setup & Configuration

Follow these steps carefully to get the project running.

### Step 1: Verify Critical Assets (Especially the `.glb` file)

The 3D viewer is useless without its model.

* **Confirm `IISER.glb` File:** Before anything else, confirm that the `IISER.glb` file exists inside the `IISER/` directory. If this file is missing or corrupted, the 3D viewer page will fail to load the main component.
* **Check the HTML Reference:** Open `IISER/campus.html` and ensure the `<model-viewer>` `src` attribute is pointing to the correct local file path. It should look exactly like this:

    ```html
    <model-viewer
        id="map"
        src="IISER.glb"
        alt="A 3D map of the IISER campus"
        ...
    >
    </model-viewer>
    ```

### Step 2: Configure the Backend Connection URL

This is the most common point of failure. The frontend needs to know where your backend is running to function correctly. You must update this in **TWO** separate JavaScript files.

1.  **For the 2D Map View:**
    * Open the `script.js` file in the **root directory**.
    * Find the `BACKEND_URL` constant at the top of the file.
    * Change the URL to your backend server's address.

    ```javascript
    // In ./script.js
    const BACKEND_URL = "[https://mapmycampus.onrender.com](https://mapmycampus.onrender.com)"; // <-- CHANGE THIS
    ```

2.  **For the 3D Viewer:**
    * Open the `script.js` file inside the **`IISER/` directory**.
    * Find the `BACKEND_URL` constant.
    * Change this URL as well.

    ```javascript
    // In ./IISER/script.js
    const BACKEND_URL = "[https://mapmycampus.onrender.com](https://mapmycampus.onrender.com)"; // <-- CHANGE THIS TOO
    ```

    *Example:* If your backend is running locally, you would change both to `http://localhost:8000` (or whatever port you are using).

    ```

### Step 3: Running the Application

You cannot just open the `index.html` file directly in your browser from the file system (`file:///...`). This will fail due to browser security policies (CORS) related to making API requests.

1.  **Use a Live Server:** The easiest method is to use a local development server.
2.  **VS Code Example:** If you use Visual Studio Code, install the [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) extension.
3.  **Launch:** Right-click on the `index.html` file in your editor and select "Open with Live Server".
4.  **Access:** Your browser will open with a local URL like `http://127.0.0.1:5500/index.html`. The application should now work correctly, provided your backend is running and the URLs are configured properly.

