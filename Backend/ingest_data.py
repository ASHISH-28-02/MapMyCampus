import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import nltk

# --- Configuration ---
load_dotenv()
# Make sure to set your GEMINI_API_KEY in a .env file
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
genai.configure(api_key=gemini_api_key)

DATABASE_FILE = "campus.db"
DATA_DIR = "Data"

def setup_nltk():
    """Downloads the necessary NLTK models for sentence tokenization."""
    resources_to_download = {
        'punkt': 'tokenizers/punkt',
        'punkt_tab': 'tokenizers/punkt_tab' # --- FIX: Added the missing resource ---
    }
    
    for resource_name, resource_path in resources_to_download.items():
        try:
            nltk.data.find(resource_path)
            print(f"NLTK '{resource_name}' model already downloaded.")
        except LookupError:
            print(f"Downloading NLTK '{resource_name}' model...")
            nltk.download(resource_name)
            print(f"Download of '{resource_name}' complete.")


def create_knowledge_base_table(conn):
    """Creates the knowledge_base table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL
        );
    """)
    print("Table 'knowledge_base' is ready.")

def ingest_data():
    """Reads data, chunks it by sentence, creates embeddings, and stores them in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    create_knowledge_base_table(conn)
    
    # Clear old data to prevent duplicates on re-runs
    conn.execute("DELETE FROM knowledge_base")
    print("Cleared old data from knowledge_base.")

    # Ensure the Data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created directory {DATA_DIR}. Please add your .txt files there.")
        return

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(DATA_DIR, filename)
            print(f"Processing {filepath}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                # Chunking by sentence instead of paragraph
                chunks = nltk.sent_tokenize(text)
                
                for chunk in chunks:
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    
                    # Use the embedding model
                    try:
                        result = genai.embed_content(
                            model="models/text-embedding-004",
                            content=chunk,
                            task_type="RETRIEVAL_DOCUMENT",
                            title=f"Content from {filename}" # Optional: Add a title for better embeddings
                        )
                        embedding = result['embedding']
                        
                        # Store embedding as a JSON string
                        conn.execute(
                            "INSERT INTO knowledge_base (content, embedding) VALUES (?, ?)",
                            (chunk, json.dumps(embedding))
                        )
                        print(f"  - Embedded and stored sentence: '{chunk[:60]}...'")
                        
                    except Exception as e:
                        print(f"Error embedding chunk: {e}")

    conn.commit()
    conn.close()
    print("\nData ingestion complete. Your knowledge base is updated with sentence-level chunks.")

if __name__ == "__main__":
    setup_nltk()
    ingest_data()
