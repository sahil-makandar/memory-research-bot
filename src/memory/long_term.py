from typing import List, Dict, Any, Optional
import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger('memory_system')

class LongTermMemory:
    def __init__(self, session_id: str, db_path: str = "./data/memory.db", max_facts: int = 100):
        self.session_id = session_id
        self.db_path = db_path
        self.max_facts = max_facts
        self._init_database()
        self.facts = []
    
    def _init_database(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS extracted_facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        fact TEXT NOT NULL,
                        confidence_score REAL,
                        source_content TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except:
            pass
    
    def store_fact(self, fact: str, confidence: float = 0.8):
        self.facts.append({'fact': fact, 'confidence': confidence})
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO extracted_facts 
                    (session_id, fact, confidence_score) 
                    VALUES (?, ?, ?)
                """, (self.session_id, fact, confidence))
        except:
            pass
    
    def get_all_facts(self) -> List[Dict[str, Any]]:
        return self.facts
    
    def get_fact_count(self) -> int:
        return len(self.facts)
    
    def get_relevant_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        relevant = []
        query_lower = query.lower()
        
        for fact_data in self.facts:
            if query_lower in fact_data['fact'].lower():
                relevant.append(fact_data)
        
        return relevant[:limit]
    
