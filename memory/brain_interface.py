"""
MODULE: Brain Interface - Zentra Memory Vault
DESCRIPTION: Centralized manager for semantic and episodic memory.
"""

import json
import os
import sqlite3
from datetime import datetime
from core.logging import logger

# File paths
BASE_DIR = "memory"
PATH_IDENTITY = os.path.join(BASE_DIR, "identita_core.json")
PATH_PROFILE = os.path.join(BASE_DIR, "profilo_utente.json")
PATH_DB = os.path.join(BASE_DIR, "archivio_chat.db")

def initialize_vault():
    """Creates the folder and databases if they don't exist."""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    
    conn = sqlite3.connect(PATH_DB)
    cursor = conn.cursor()
    # Ensure the history table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_context():
    """Retrieves AI and Admin identity for the System Prompt."""
    try:
        if not os.path.exists(PATH_IDENTITY) or not os.path.exists(PATH_PROFILE):
            return ""

        with open(PATH_IDENTITY, "r", encoding="utf-8") as f:
            id_data = json.load(f)
        
        with open(PATH_PROFILE, "r", encoding="utf-8") as f:
            prof_data = json.load(f)
            
        from core.system.version import VERSION
        context = f"\n[ACTIVE IDENTITY MEMORY]\n"
        
        # AI Identity
        ai_name = id_data.get('ai', {}).get('name', 'Zentra')
        ai_nature = id_data.get('ai', {}).get('nature', 'AI Assistant')
        ai_protocol = id_data.get('ai', {}).get('protocol', 'Standard')
        
        context += f"You are {ai_name}, version {VERSION}. {ai_nature}.\n"
        context += f"Your Creator (Admin) is {id_data.get('author', {}).get('name', 'Admin')}. Protocol: {ai_protocol}.\n"
        
        # Admin Biographical Notes
        notes = prof_data.get('author', {}).get('notes', 'No specific notes.')
        context += f"Admin notes: {notes}\n"
        
        return context
    except Exception as e:
        logger.error(f"Memory Context Error: {e}")
        return ""

def update_profile(key, value):
    """Updates a specific field in the user profile JSON."""
    try:
        if not os.path.exists(PATH_PROFILE):
            # Create a default profile if missing
            data = {"author": {"name": "Admin", "role": "Root User", "notes": ""}}
        else:
            with open(PATH_PROFILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        # Ensure 'author' section exists
        if "author" not in data:
            data["author"] = {}
            
        # Standardize: we usually update 'notes'
        if key == "notes" or key == "note_biografiche":
            data["author"]["notes"] = value
        else:
            data["author"][key] = value
            
        with open(PATH_PROFILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Profile Update Error: {e}")
        return False

def save_message(role, message):
    """Stores an exchange in episodic memory (DB)."""
    try:
        conn = sqlite3.connect(PATH_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO history (timestamp, role, message) VALUES (?, ?, ?)",
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, message))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Memory Save Error: {e}")

def get_history(limit=10):
    """Retrieves the last N messages from the history."""
    try:
        conn = sqlite3.connect(PATH_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT role, message FROM history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        # Return in chronological order (oldest first)
        rows.reverse()
        return rows
    except Exception as e:
        logger.error(f"Memory Read Error: {e}")
        return []

def clear_history():
    """Wipes the episodic history table."""
    try:
        conn = sqlite3.connect(PATH_DB)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Memory Reset Error: {e}")
        return False

# Alias for backward compatibility (renamed from get_context during ITA→ENG migration)
def get_memory_context():
    """Alias for get_context() — returns AI and Admin identity for the System Prompt."""
    return get_context()