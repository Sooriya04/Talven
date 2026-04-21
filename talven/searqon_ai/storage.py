# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import sqlite3
import datetime
from talven.sqlitedb import SQLiteAppl

class SearqonHistoryDB(SQLiteAppl):
    """Storage for Searqon AI request and response history."""
    
    DB_SCHEMA = 1
    
    DDL_CREATE_TABLES = {
        'history': """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                intent TEXT,
                results TEXT, -- JSON string of search results
                summary TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
    }

    def add_entry(self, query, intent, results, summary):
        """Add a new search entry to history."""
        with self.DB:
            results_json = json.dumps(results)
            self.DB.execute(
                "INSERT INTO history (query, intent, results, summary) VALUES (?, ?, ?, ?)",
                (query, intent, results_json, summary)
            )

    def get_history(self, limit=50):
        """Retrieve recent search history."""
        cursor = self.DB.execute(
            "SELECT id, query, intent, results, summary, timestamp FROM history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        history = []
        for row in cursor:
            history.append({
                "id": row[0],
                "query": row[1],
                "intent": row[2],
                "results": json.loads(row[3]),
                "summary": row[4],
                "timestamp": row[5]
            })
        return history

# Global instance for easy access
# Default path matches talven/search_logs.sqlite or a separate one
import os
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'searqon_ai_history.sqlite')
history_db = SearqonHistoryDB(DB_PATH)
