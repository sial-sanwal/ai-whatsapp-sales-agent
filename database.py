"""
Database module for WhatsApp Sales Agent
Handles persistent storage of conversations and lead data using SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
import os

DATABASE_PATH = "whatsapp_agent.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Conversations table - stores individual messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_phone_number 
            ON conversations(phone_number)
        """)
        
        # Conversation states table - stores lead data and state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_states (
                phone_number TEXT PRIMARY KEY,
                stage TEXT NOT NULL,
                lead_data TEXT NOT NULL,
                retry_count TEXT NOT NULL,
                lead_score INTEGER DEFAULT 0,
                last_activity TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Database initialized successfully")


def save_message_to_db(phone_number: str, role: str, content: str, timestamp: str = None):
    """Save a message to the database"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (phone_number, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (phone_number, role, content, timestamp))


def get_conversation_history_from_db(phone_number: str, limit: int = 10) -> List[Dict]:
    """Get conversation history from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, timestamp
            FROM conversations
            WHERE phone_number = ?
            ORDER BY id DESC
            LIMIT ?
        """, (phone_number, limit))
        
        # Reverse to get chronological order
        messages = cursor.fetchall()
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"]
            }
            for msg in reversed(messages)
        ]


def save_conversation_state_to_db(phone_number: str, state: Dict):
    """Save or update conversation state"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Convert complex objects to JSON strings
        lead_data_json = json.dumps(state["lead_data"])
        retry_count_json = json.dumps(state["retry_count"])
        
        cursor.execute("""
            INSERT INTO conversation_states 
            (phone_number, stage, lead_data, retry_count, lead_score, last_activity, message_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone_number) DO UPDATE SET
                stage = excluded.stage,
                lead_data = excluded.lead_data,
                retry_count = excluded.retry_count,
                lead_score = excluded.lead_score,
                last_activity = excluded.last_activity,
                message_count = excluded.message_count,
                updated_at = CURRENT_TIMESTAMP
        """, (
            phone_number,
            state["stage"],
            lead_data_json,
            retry_count_json,
            state["lead_score"],
            state["last_activity"],
            state["message_count"]
        ))


def get_conversation_state_from_db(phone_number: str) -> Optional[Dict]:
    """Get conversation state from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT stage, lead_data, retry_count, lead_score, last_activity, message_count
            FROM conversation_states
            WHERE phone_number = ?
        """, (phone_number,))
        
        row = cursor.fetchone()
        if row:
            return {
                "stage": row["stage"],
                "lead_data": json.loads(row["lead_data"]),
                "retry_count": json.loads(row["retry_count"]),
                "lead_score": row["lead_score"],
                "last_activity": row["last_activity"],
                "message_count": row["message_count"]
            }
        return None


def get_all_leads_from_db() -> List[Dict]:
    """Get all leads with their scores"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT phone_number, stage, lead_data, lead_score, last_activity, message_count
            FROM conversation_states
            WHERE lead_score > 0
            ORDER BY lead_score DESC
        """)
        
        leads = []
        for row in cursor.fetchall():
            leads.append({
                "phone": row["phone_number"],
                "score": row["lead_score"],
                "stage": row["stage"],
                "data": json.loads(row["lead_data"]),
                "last_activity": row["last_activity"],
                "message_count": row["message_count"]
            })
        
        return leads


def delete_conversation(phone_number: str):
    """Delete a conversation (for testing/cleanup)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE phone_number = ?", (phone_number,))
        cursor.execute("DELETE FROM conversation_states WHERE phone_number = ?", (phone_number,))


def get_database_stats() -> Dict:
    """Get database statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total conversations
        cursor.execute("SELECT COUNT(DISTINCT phone_number) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        # Total messages
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_messages = cursor.fetchone()[0]
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM conversation_states WHERE lead_score > 0")
        total_leads = cursor.fetchone()[0]
        
        # High quality leads (70+)
        cursor.execute("SELECT COUNT(*) FROM conversation_states WHERE lead_score >= 70")
        high_quality_leads = cursor.fetchone()[0]
        
        # Database size
        db_size = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_leads": total_leads,
            "high_quality_leads": high_quality_leads,
            "database_size_mb": round(db_size / (1024 * 1024), 2)
        }


# Initialize database on module import
if __name__ != "__main__":
    init_database()
