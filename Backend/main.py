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
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel('gemini-1.5-flash')
DATABASE_FILE = "campus.db"

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Campus Navigator API",
    description="Backend service for the IISER TVM Campus Navigator application.",
    version="2.5.0" # Version bump for improved route parsing
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
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def check_table_exists(conn, table_name):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str
    is_3d: Optional[bool] = Field(None, alias='is_3d')

# --- Helper Functions ---

def find_mentioned_buildings_from_db(query: str):
    """
    **FIXED FUNCTION:** Finds all building names mentioned in the query by checking every alias
    against the query string. This correctly handles multiple mentions for routes.
    """
    conn = get_db_connection()
    mentioned_buildings = []
    try:
        if not check_table_exists(conn, "aliases"):
            print("Warning: 'aliases' table not found.")
            return []
        
        cursor = conn.execute("SELECT b.name as building_name, a.name as alias_name FROM buildings b JOIN aliases a ON b.id = a.building_id")
        all_aliases = cursor.fetchall()
        
        # Sort by alias length (descending) to match longer names first (e.g., "lecture hall complex" before "lhc")
        sorted_aliases = sorted(all_aliases, key=lambda x: len(x['alias_name']), reverse=True)

        lower_query = query.lower()
        found_buildings = {} # Use a dict to store found buildings and their index in the query

        for row in sorted_aliases:
            alias = row['alias_name'].lower()
            building_name = row['building_name']
            
            # Find all occurrences of the alias in the query
            for match in re.finditer(r'\b' + re.escape(alias) + r'\b', lower_query):
                # Only add if this building hasn't been found already
                if building_name not in found_buildings:
                    found_buildings[building_name] = match.start()

        # Sort the found buildings by their order of appearance in the query string
        sorted_found_buildings = sorted(found_buildings.keys(), key=lambda b: found_buildings[b])
        
        return sorted_found_buildings
    finally:
        if conn:
            conn.close()


async def get_enriched_description(building_name: str, default_description: str) -> str:
    prompt = f"""Rewrite the following factual description of "{building_name}" into a short, engaging, single-paragraph response for a student. Do not add new facts or use newline characters. Factual Description: "{default_description}" """
    try:
        response = await model.generate_content_async(prompt)
        text_no_newlines = response.text.replace('\n', ' ')
        clean_text = re.sub(r'\s+', ' ', text_no_newlines).strip()
        return clean_text if clean_text else default_description
    except Exception as e:
        print(f"Gemini API error during enrichment: {e}")
        return default_description

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def find_relevant_knowledge(query_embedding, conn, top_k=3):
    cursor = conn.execute("SELECT content, embedding FROM knowledge_base")
    knowledge_chunks = cursor.fetchall()
    if not knowledge_chunks: return []

    similarities = [(cosine_similarity(query_embedding, np.array(json.loads(row['embedding']))), row['content']) for row in knowledge_chunks]
    similarities.sort(key=lambda x: x[0], reverse=True)
    return [content for sim, content in similarities[:top_k]]

async def search_knowledge_base(query: str):
    print(f"Handling as informational query. Searching knowledge base for: '{query}'")
    conn = None
    try:
        conn = get_db_connection()
        if not check_table_exists(conn, "knowledge_base"):
            return {"type": "error", "message": "My knowledge base isn't set up."}
        
        query_embedding_result = genai.embed_content(model="models/text-embedding-004", content=query, task_type="RETRIEVAL_QUERY")
        context_chunks = find_relevant_knowledge(query_embedding_result['embedding'], conn)

        if not context_chunks:
            return {"type": "answer", "message": "Sorry, I couldn't find an answer."}

        context_str = "\n\n".join(context_chunks)
        prompt = f"""Answer the user's question using ONLY the provided context. Be concise. If the answer is not in the context, say you don't have information on that topic. Context: --- {context_str} --- Question: {query} Direct Answer:"""
        response = await model.generate_content_async(prompt)
        return {"type": "answer", "message": response.text}
    except Exception as e:
        print(f"Error during knowledge base query: {e}")
        return {"type": "error", "message": "I encountered a problem trying to answer your question."}
    finally:
        if conn: conn.close()

# --- API Endpoints ---
@app.get("/api/config")
def get_config():
    return {"Maps_api_key": os.getenv("Maps_API_KEY")}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    query = request.query.strip()
    lower_query = query.lower()

    GREETINGS = {"hello", "hi", "hey", "hai", "hello."}
    if lower_query in GREETINGS:
        return {"type": "greeting", "message": "Hello! How can I help you with IISER TVM today?"}

    print(f"Searching for location mentions in query: '{query}'")
    mentioned_keys = find_mentioned_buildings_from_db(query)
    
    if not mentioned_keys:
        print("No specific location found in DB. Handling as informational query.")
        return await search_knowledge_base(query)

    print(f"Found location mentions: {mentioned_keys}. Handling as location query.")
    conn = get_db_connection()
    try:
        if len(mentioned_keys) >= 2:
            from_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
            from_data_row = from_cursor.fetchone()
            to_cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[1],))
            to_data_row = to_cursor.fetchone()
            if from_data_row and to_data_row:
                return {"type": "route", "from": dict(from_data_row), "to": dict(to_data_row)}

        cursor = conn.execute("SELECT * FROM buildings WHERE name = ?", (mentioned_keys[0],))
        loc_data_row = cursor.fetchone()
        if loc_data_row:
            loc_data = dict(loc_data_row)
            enriched_description = await get_enriched_description(loc_data['name'], loc_data['description'])
            loc_data['description'] = enriched_description
            return {"type": "location", **loc_data}
            
    finally:
        if conn: conn.close()

    # Fallback if DB lookup fails for some reason
    return await search_knowledge_base(query)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Campus Navigator API."}
