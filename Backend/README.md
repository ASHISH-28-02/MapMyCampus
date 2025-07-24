# MapMyCampus Backend

It's built with FastAPI and uses Google's Gemini Pro for natural language understanding, intent classification, and Retrieval-Augmented Generation (RAG) to answer user queries.

---

## Core Features

- **FastAPI Server**: Provides a robust and fast API.
- **SQLite Database**: Stores location data and the knowledge base.
- **RAG Pipeline**: Ingests text documents, creates vector embeddings using `text-embedding-004`, and retrieves relevant information to answer user questions.
- **LLM-Powered Intent Classification**: Determines whether a user is asking for a location or general information.
- **Dynamic Content Generation**: Enriches location descriptions using the generative model.

---

## Setup and Installation

Follow these steps to get the backend server running locally.

### 1. Prerequisites

- Python 3.8+
- `pip` (Python package installer)

### 2. Clone the Repository

First, ensure you have all the necessary files in a single project directory:

- `main.py`
- `ingest_data.py`
- `campus_db.py`

### 3. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

Create a file named `requirements.txt` and add the following lines:

```
fastapi
uvicorn
pydantic
python-dotenv
google-generativeai
numpy
nltk
```

Now, install these packages using pip:

```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables

Create a file named `.env` in your project root directory. This file will store your secret API keys.

```
# Your Google AI Studio API Key for Gemini
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Your Google Maps API Key for the frontend (optional for backend-only testing)
Maps_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
```

Replace `"YOUR_..._KEY"` with your actual keys.

---

## Data and Database Setup

The backend relies on a SQLite database (`campus.db`) which contains two main types of data:
1.  **Static Locations**: A list of buildings, their coordinates, and aliases.
2.  **Knowledge Base**: Text chunks and their vector embeddings for the RAG system.

You must run the provided scripts in the correct order to populate the database.

### Step 1: Create the Location Database

Run the `campus_db.py` script. This will create the `campus.db` file and populate it with the building information defined in the script.

```bash
python campus_db.py
```
You should see a success message: `✅ Database 'campus.db' created and populated successfully!`

### Step 2: Prepare Knowledge Base Data

- Create a directory named `Data` in your project root.
- Place any `.txt` files containing information you want the chatbot to know about inside this `Data` directory. For example, you could have `academics.txt`, `hostel_rules.txt`, etc.

### Step 3: Ingest Data for RAG

Run the `ingest_data.py` script. This script will:
1.  Download the necessary NLTK model for sentence splitting.
2.  Read each `.txt` file from the `Data` directory.
3.  Split the text into sentence-level chunks.
4.  Generate an embedding for each chunk using the Gemini API.
5.  Store the content and its embedding in the `knowledge_base` table within `campus.db`.

```bash
python ingest_data.py
```
This process may take some time depending on the amount of text. You will see progress messages in the console.

---

## Running the Backend Server

Once the setup and data ingestion are complete, you can start the FastAPI server using `uvicorn`.

```bash
uvicorn main:app --reload
```

- `--reload`: This flag enables auto-reloading, so the server will restart automatically when you make changes to the code.

The server will be running at: **`http://127.0.0.1:8000`**

You can access the interactive API documentation (provided by Swagger UI) at: **`http://127.0.0.1:8000/docs`** to test the endpoints directly.

