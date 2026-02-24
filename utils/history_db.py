"""Search history database management."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class SearchHistoryDB:
    """Manages search history in SQLite database."""

    def __init__(self, db_path: str = "data/search_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_image_path TEXT NOT NULL,
                query_image_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                top_k INTEGER NOT NULL,
                min_similarity REAL NOT NULL,
                results_json TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_search(self, query_image_path: str, query_image_name: str,
                   top_k: int, min_similarity: float, results: List[Dict]) -> int:
        """Add a search record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_history
            (query_image_path, query_image_name, timestamp, top_k, min_similarity, results_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (query_image_path, query_image_name, datetime.now(),
              top_k, min_similarity, json.dumps(results)))
        search_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return search_id

    def get_recent_searches(self, limit: int = 100) -> List[Dict]:
        """Get recent search records."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'query_image_path': row['query_image_path'],
                'query_image_name': row['query_image_name'],
                'timestamp': row['timestamp'],
                'top_k': row['top_k'],
                'min_similarity': row['min_similarity'],
                'results': json.loads(row['results_json'])
            })
        return results

    def get_search_by_id(self, search_id: int) -> Optional[Dict]:
        """Get a specific search record."""
        searches = self.get_recent_searches(limit=1000)
        for search in searches:
            if search['id'] == search_id:
                return search
        return None

    def cleanup_old_records(self, keep_recent: int = 100):
        """Keep only recent N records."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM search_history
            WHERE id NOT IN (
                SELECT id FROM search_history
                ORDER BY timestamp DESC
                LIMIT ?
            )
        """, (keep_recent,))
        conn.commit()
        conn.close()
