import os
import sqlite3
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai
import json
import numpy as np
from typing import Optional

# --- Configuration ---
load_dotenv()
# Make sure to set your GEMINI_API_KEY in a .env file
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel('gemini-1.5-flash')
DATABASE_FILE = "campus.db"

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Campus Navigator API",
    description="Backend service for the IISER TVM Campus Navigator application.",
    version="2.4.3" # Version bump for robust query logic
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# --- Database Helper ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def check_table_exists(conn, table_name):
    """Checks if a table exists in the database."""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    is_3d: Optional[bool] = Field(None, alias='is_3d')


# --- Helper Functions ---
def find_mentioned_buildings_from_db(query: str):
    """Finds building names mentioned in the query by checking against aliases."""
    conn = get_db_connection()
    try:
        if not check_table_exists(conn, "buildings") or not check_table_exists(conn, "aliases"):
            print("Warning: 'buildings' or 'aliases' table not found. Location search will be skipped.")
            return []
        
        cursor = conn.execute("""
            SELECT DISTINCT b.name
            FROM buildings b
            JOIN aliases a ON b.id = a.building_id
            WHERE INSTR(LOWER(a.name), LOWER(?)) > 0
        """, (query.lower(),))
        buildings = [row['name'] for row in cursor.fetchall()]
        return buildings
    finally:
        if conn:
            conn.close()


async def get_enriched_description(building_name: str, default_description: str) -> str:
    """
    Generates an engaging description for a building by rewriting the factual default
    description, preventing hallucination and cleaning up formatting.
    """
    prompt = f"""You are a helpful campus guide assistant. Your task is to rewrite a factual description to make it more engaging and conversational for a student.
IMPORTANT:
- Do not add any new facts or change the core purpose of the building described.
- The entire response MUST be a single, continuous paragraph.
- ABSOLUTELY DO NOT use any newline characters (`\\n`). Keep titles like "Dr." on the same line as the name that follows.

Factual Information:
- Building Name: "{building_name}"
- Factual Description: "{default_description}"

Rewrite the factual description into a short, engaging, single-paragraph response for a student:
"""
    try:
        response = await model.generate_content_async(prompt)
        
        text_no_newlines = response.text.replace('\n', ' ')
        clean_text = re.sub(r'\s+', ' ', text_no_newlines).strip()

        if clean_text:
            return clean_text
        else:
            print(f"Gemini returned an empty description for '{building_name}'. Falling back to default.")
            return default_description
            
    except Exception as e:
        print(f"Gemini API error during enrichment: {e}")
        return default_description

def cosine_similarity(v1, v2):
    """Calculates cosine similarity between two vectors."""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def find_relevant_knowledge(query_embedding, conn, top_k=3):
    """Finds the top_k most relevant knowledge chunks from the database using cosine similarity."""
    cursor = conn.execute("SELECT content, embedding FROM knowledge_base")
    knowledge_chunks = cursor.fetchall()

    if not knowledge_chunks:
        return []

    similarities = []
    for row in knowledge_chunks:
        content = row['content']
        db_embedding = np.array(json.loads(row['embedding']))
        sim = cosine_similarity(query_embedding, db_embedding)
        similarities.append((sim, content))

    similarities.sort(key=lambda x: x[0], reverse=True)
    return [content for sim, content in similarities[:top_k]]

async def search_knowledge_base(query: str):
    """Performs a RAG search against the knowledge base."""
    print(f"Handling as informational query. Searching knowledge base for: '{query}'")
    conn = None
    try:
        conn = get_db_connection()
        
        if not check_table_exists(conn, "knowledge_base"):
            print("Error: knowledge_base table not found in the database.")
            return {
                "type": "error",
                "message": "🤖 My knowledge base hasn't been set up. Please ensure the ingest.py script has been run successfully."
            }
        
        query_embedding_result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="RETRIEVAL_QUERY"
        )
        query_embedding = query_embedding_result['embedding']
        context_chunks = find_relevant_knowledge(query_embedding, conn)

        if not context_chunks:
            return {
                "type": "answer",
                "message": "Sorry, I couldn't find an answer."
            }

        context_str = "\n\n".join(context_chunks)
        
        prompt = f"""You are a highly precise question-answering assistant for IISER TVM. Your task is to directly answer the user's question using ONLY the provided context. Be concise and extract the specific information requested. Do not add any extra conversational text. If the answer is not in the context, state that you do not have information on that topic.

Context:
---
{context_str}
---

Question: {query}

Direct Answer:"""

        response = await model.generate_content_async(prompt)
        return {"type": "answer", "message": response.text}

    except Exception as e:
        print(f"Error during knowledge base query: {e}")
        return {"type": "error", "message": "🤖 I encountered a problem trying to answer your question. Please try again."}
    finally:
        if conn:
            conn.close()

# --- API Endpoints ---
@app.get("/api/config")
def get_config():
    """Returns public configuration like API keys for the frontend."""
    return {"Maps_api_key": os.getenv("Maps_API_KEY")}


@app.post("/api/query")
async def handle_query(request: QueryRequest):
    """
    Processes user queries by prioritizing a direct database search first.
    1. Handle simple greetings.
    2. Search the database for any mentioned locations.
    3. If locations are found, handle as a location/route query.
    4. If no locations are found, fall back to the RAG knowledge base.
    """
    query = request.query.strip()
    lower_query = query.lower()

    # Step 1: Handle simple greetings
    GREETINGS = {"hello", "hi", "hey", "hai", "hello."}
    THANKS = {"thanks", "thank you", "ty"}
    if lower_query in GREETINGS:
        return {"type": "greeting", "message": "Hello! How can I help you with IISER TVM today?"}
    if lower_query in THANKS:
        return {"type": "greeting", "message": "You're welcome!"}

    # Step 2: Search for a location in the database.
    print(f"Searching for location mentions in query: '{query}'")
    mentioned_keys = find_mentioned_buildings_from_db(query)
    
    # **FIX:** This logic is now restructured to be more robust.
    # If no location is mentioned, we proceed to the knowledge base.
    if not mentioned_keys:
        print("No specific location found in DB. Handling as informational query.")
        return await search_knowledge_base(query)

    # If a location IS mentioned, we commit to handling it as a location/route query.
    print(f"Found location mentions: {mentioned_keys}. Handling as location query.")
    is_route_query = ' to ' in lower_query or ' from ' in lower_query
    conn = get_db_connection()
    try:
        # Handle route queries (2 or more locations)
        if len(mentioned_keys) >= 2 and is_route_query:
            from_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
            from_data_row = from_cursor.fetchone()
            to_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[1],))
            to_data_row = to_cursor.fetchone()
            if from_data_row and to_data_row:
                return {"type": "route", "from": dict(from_data_row), "to": dict(to_data_row)}
            else:
                # Handle case where route locations are recognized but data isn't found
                return {"type": "answer", "message": "I recognized the locations for the route, but couldn't find the path. Please try rephrasing."}

        # Handle single location queries
        cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
        loc_data_row = cursor.fetchone()
        if loc_data_row:
            loc_data = dict(loc_data_row)
            enriched_description = await get_enriched_description(loc_data['name'], loc_data['description'])
            response_data = loc_data
            response_data['description'] = enriched_description
            return {"type": "location", **response_data}
        else:
            # This handles the case where an alias is found but the building data lookup fails
            return {"type": "answer", "message": f"I recognized '{mentioned_keys[0]}' in your query, but I couldn't retrieve its specific details."}
            
    except Exception as e:
        print(f"Error during location/route processing: {e}")
        return {"type": "error", "message": "🤖 I encountered a problem processing the location. Please try again."}
    finally:
        if conn:
            conn.close()
