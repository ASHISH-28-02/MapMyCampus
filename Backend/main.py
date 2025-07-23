import os
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import json
import numpy as np

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
    version="1.9.0" # Version bump for JSON-based intent classification
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
            WHERE INSTR(LOWER(?), LOWER(REPLACE(a.name, '-', ' '))) > 0
        """, (query.lower(),))
        buildings = [row['name'] for row in cursor.fetchall()]
        return buildings
    finally:
        if conn:
            conn.close()


async def get_enriched_description(building_name: str, default_description: str) -> str:
    """Generates a more engaging description for a building using the generative model."""
    prompt = f"Provide a short, engaging description for '{building_name}' at the IISER Thiruvananthapuram campus. Focus on what a student might do there. Keep it conversational and brief."
    try:
        response = await model.generate_content_async(prompt)
        return response.text
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
                "type": "error",
                "message": "🤖 I can't seem to find information on that. I can help with locations on campus or answer questions about academics and life at IISER TVM."
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
    Processes user queries using an LLM-based intent classification approach.
    1. Handle simple greetings.
    2. Use an LLM to classify the query's intent via structured JSON output.
    3. Route to the appropriate handler (location search or RAG).
    """
    query = request.query.strip()
    lower_query = query.lower()

    # Step 1: Handle simple greetings to save API calls
    GREETINGS = {"hello", "hi", "hey", "hai", "hello."}
    THANKS = {"thanks", "thank you", "ty"}
    if lower_query in GREETINGS:
        return {"type": "greeting", "message": "Hello! How can I help you with IISER TVM today?"}
    if lower_query in THANKS:
        return {"type": "greeting", "message": "You're welcome!"}

    # Step 2: Use LLM to classify the query's primary intent using JSON
    intent = "information_request"  # Default to informational
    prompt = f"""Analyze the user's query and classify its primary intent. The possible intents are "location_search" or "information_request". Respond with only a JSON object containing the intent, like {{"intent": "your_classification"}}.

Examples:
- Query: "where is the library"
  {{"intent": "location_search"}}
- Query: "lhc"
  {{"intent": "location_search"}}
- Query: "route from psb to bsb"
  {{"intent": "location_search"}}
- Query: "who is the director"
  {{"intent": "information_request"}}
- Query: "what are the mess timings"
  {{"intent": "information_request"}}
- Query: "director of iiser"
  {{"intent": "information_request"}}

Query: "{query}"
"""
    try:
        response = await model.generate_content_async(prompt)
        # Clean the response to extract only the JSON part
        json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        intent_data = json.loads(json_str)
        intent = intent_data.get("intent", "information_request")
        print(f"Intent Check for '{query}'. Classified as: {intent}")
    except Exception as e:
        print(f"Error during intent classification: {e}. Defaulting to informational search.")
        intent = "information_request"


    # Step 3: Route based on the classification
    if intent == "location_search":
        print("Handling as a location query.")
        mentioned_keys = find_mentioned_buildings_from_db(query)
        is_route_query = ' to ' in lower_query or ' from ' in lower_query

        if len(mentioned_keys) > 0:
            conn = get_db_connection()
            try:
                if len(mentioned_keys) >= 2 and is_route_query:
                    from_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
                    from_data = dict(from_cursor.fetchone())
                    to_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[1],))
                    to_data = dict(to_cursor.fetchone())
                    if from_data and to_data:
                        return {"type": "route", "from": from_data, "to": to_data}

                if len(mentioned_keys) == 1:
                    cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
                    loc_data_row = cursor.fetchone()
                    if loc_data_row:
                        loc_data = dict(loc_data_row)
                        enriched_description = await get_enriched_description(loc_data['name'], loc_data['description'])
                        response_data = loc_data
                        response_data['description'] = enriched_description
                        return {"type": "location", **response_data}
            finally:
                if conn:
                    conn.close()
        
        # If the intent was 'location' but we couldn't find a specific place, fall through to RAG.
        print("Location search did not yield a specific result. Falling back to knowledge base.")

    # Step 4: This is the default path for "information_request" and failed location searches.
    return await search_knowledge_base(query)


@app.get("/")
def read_root():
    """Root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Campus Navigator API. Now running with a SQLite database and RAG."}
