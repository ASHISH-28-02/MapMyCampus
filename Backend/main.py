import os
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
DATABASE_FILE = "campus.db"

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Campus Navigator API",
    description="Backend service for the IISER TVM Campus Navigator application.",
    version="1.1.0"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Helper ---
# Creates a connection to the database.
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    # This allows you to access columns by name (like a dictionary)
    conn.row_factory = sqlite3.Row
    return conn

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

# --- Helper Functions ---
def find_mentioned_buildings_from_db(query: str):
    """Searches the database for buildings and aliases that match the query."""
    conn = get_db_connection()
    # Use a JOIN to search both building names and aliases at once
    # The INSTR function finds a substring, making the search flexible
    cursor = conn.execute("""
        SELECT DISTINCT b.name
        FROM buildings b
        JOIN aliases a ON b.id = a.building_id
        WHERE INSTR(LOWER(?), LOWER(REPLACE(a.name, '-', ' '))) > 0
    """, (query.lower(),))
    
    buildings = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return buildings

async def get_enriched_description(building_name: str, default_description: str) -> str:
    """Gets an engaging description from the Gemini API, with a fallback."""
    prompt = f"Provide a short, engaging description for '{building_name}' at the IISER Thiruvananthapuram campus. Focus on what a student might do there. Keep it conversational and brief."
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return default_description

# --- API Endpoints ---
@app.get("/api/config")
def get_config():
    """Provides the Google Maps API key to the frontend."""
    # Note the key name change to match the frontend script
    return {"Maps_api_key": os.getenv("Maps_API_KEY")}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    """Processes user queries for locations or routes using the database."""
    query = request.query
    mentioned_keys = find_mentioned_buildings_from_db(query)
    
    conn = get_db_connection()
    
    is_route_query = ' to ' in query.lower() or ' from ' in query.lower()
    
    if len(mentioned_keys) >= 2 and is_route_query:
        # For routes, fetch data for the first two matched buildings
        from_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
        from_data = dict(from_cursor.fetchone())
        
        to_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[1],))
        to_data = dict(to_cursor.fetchone())
        
        conn.close()
        return {"type": "route", "from": from_data, "to": to_data}

    if len(mentioned_keys) == 1:
        # For a single location, fetch its data
        cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
        loc_data_row = cursor.fetchone()
        conn.close()
        
        if loc_data_row:
            loc_data = dict(loc_data_row)
            enriched_description = await get_enriched_description(loc_data['name'], loc_data['description'])
            
            # Create a response object and add the new description
            response_data = loc_data
            response_data['description'] = enriched_description
            return {"type": "location", **response_data}
        
    conn.close()
    return {
        "type": "error",
        "message": "🤖 Please ask for a single location ('where is the library?') or a route ('hostel to academic block')."
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the Campus Navigator API. Now running with a SQLite database."}
