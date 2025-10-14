# backend/database.py
import sqlite3
import json

DB_FILE = "chatbot.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            cart TEXT,
            name TEXT,
            delivery TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_session(session_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        session = dict(row)
        session["cart"] = json.loads(session["cart"]) if session["cart"] else []
        return session
    return None

def save_session(session_id, session_data):
    conn = get_db_connection()
    c = conn.cursor()
    cart_json = json.dumps(session_data.get("cart", []))
    c.execute("""
        INSERT OR REPLACE INTO sessions (session_id, cart, name, delivery)
        VALUES (?, ?, ?, ?)
    """, (session_id, cart_json, session_data.get("name"), session_data.get("delivery")))
    conn.commit()
    conn.close()

# Initialize the database and tables when this module is loaded
create_tables()
