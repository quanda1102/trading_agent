"""
SQLite Storage Adapter

Provides SQLite-based storage for short-term memory.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class SQLiteStorage:
    """SQLite storage adapter for short-term memory."""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_session 
                ON memories(user_id, session_id)
            """)
    
    def store_message(self, user_id: str, session_id: str, role: str, content: str):
        """Store a message in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (user_id, session_id, role, content, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, session_id, role, content, datetime.now().isoformat(), datetime.now().isoformat()))
    
    def get_messages(self, user_id: str, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT role, content, timestamp
                FROM memories
                WHERE user_id = ? AND session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, session_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                })
            
            return list(reversed(messages))  # Return in chronological order
    
    def clear_session(self, user_id: str, session_id: str):
        """Clear messages for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM memories
                WHERE user_id = ? AND session_id = ?
            """, (user_id, session_id))
    
    def get_context(self, user_id: str, session_id: str, max_messages: int = 10) -> str:
        """Get conversation context as string."""
        messages = self.get_messages(user_id, session_id, max_messages)
        context_parts = []
        
        for msg in messages:
            context_parts.append(f"{msg['role']}: {msg['content']}")
        
        return "\n".join(context_parts)
