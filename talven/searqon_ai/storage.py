# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import sqlite3
import datetime
import time
import secrets
import uuid
from talven.sqlitedb import SQLiteAppl

def generate_uuid7():
    """
    Generate a UUIDv7 string.
    UUIDv7 format: 48 bits timestamp (ms) + 4 bits version (7) + 12 bits randomness + 2 bits variant (2) + 62 bits randomness
    """
    # 48-bit timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    # 12 bits of randomness for the first section
    rand_a = secrets.randbits(12)
    
    # 62 bits of randomness for the second section
    rand_b = secrets.randbits(62)
    
    # Construct UUID components
    # Section 1: timestamp_ms (48 bits)
    # Section 2: version 7 (4 bits) + rand_a (12 bits) = 16 bits
    # Section 3: variant 2 (2 bits) + rand_b_top (14 bits) = 16 bits
    # Section 4: rand_b_bottom (48 bits)
    
    part1 = timestamp_ms & 0xFFFFFFFFFFFF
    part2 = (7 << 12) | (rand_a & 0x0FFF)
    part3 = (2 << 14) | ((rand_b >> 48) & 0x3FFF)
    part4 = rand_b & 0xFFFFFFFFFFFF
    
    # Format as UUID hex string: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    return f"{part1 >> 16:08x}-{(part1 & 0xFFFF):04x}-{part2:04x}-{part3:04x}-{part4:012x}"

class SearqonChatDB(SQLiteAppl):
    """Advanced Storage for Searqon AI Conversations using UUIDv7."""
    
    DB_SCHEMA = 2 # Increment schema version
    
    DDL_CREATE_TABLES = {
        'conversations': """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY, -- UUIDv7
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'messages': """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, -- UUIDv7
                conversation_id TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """
    }

    def create_conversation(self, title="New Chat"):
        """Create a new conversation and return its UUIDv7."""
        conv_id = generate_uuid7()
        with self.DB:
            self.DB.execute(
                "INSERT INTO conversations (id, title) VALUES (?, ?)",
                (conv_id, title)
            )
        return conv_id

    def add_message(self, conversation_id, role, content):
        """Add a message to a conversation."""
        msg_id = generate_uuid7()
        with self.DB:
            self.DB.execute(
                "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
                (msg_id, conversation_id, role, content)
            )
        return msg_id

    def get_messages(self, conversation_id):
        """Retrieve all messages for a specific conversation in chronological order."""
        cursor = self.DB.execute(
            "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        )
        return [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in cursor]

    def list_conversations(self, limit=50):
        """List all conversations, most recent first."""
        cursor = self.DB.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [{"id": row[0], "title": row[1], "created_at": row[2]} for row in cursor]

    def delete_conversation(self, conversation_id):
        """Delete a conversation and all its messages."""
        with self.DB:
            self.DB.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

# Global instance
import os
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'searqon_ai_chat.sqlite')
history_db = SearqonChatDB(DB_PATH)
