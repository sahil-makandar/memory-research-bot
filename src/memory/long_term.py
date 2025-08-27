from typing import List, Dict, Any, Optional
import sqlite3
import json
from datetime import datetime
import logging
from llama_index.core.llms import LLM
from ..utils.azure_client import get_azure_llm

logger = logging.getLogger('memory_system')

class LongTermMemory:
    """Persistent fact extraction and storage system."""
    
    def __init__(self, session_id: str, db_path: str = "./data/memory.db", max_facts: int = 100):
        self.session_id = session_id
        self.db_path = db_path
        self.max_facts = max_facts
        self.llm = get_azure_llm()
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for long-term memory"""
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
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def extract_facts(self, conversation_content: str) -> List[Dict[str, Any]]:
        """Extract key facts from conversation content using LLM"""
        extraction_prompt = f"""
        Extract key facts and insights from the following conversation content.
        Focus on:
        - Important information that should be remembered
        - User preferences and requirements
        - Key decisions or conclusions
        - Factual information about topics discussed
        
        Return facts as a JSON list with format:
        [{{"fact": "extracted fact", "confidence": 0.8}}]
        
        Conversation content:
        {conversation_content}
        """
        
        try:
            response = await self.llm.acomplete(extraction_prompt)
            facts_data = json.loads(response.text.strip())
            
            extracted_facts = []
            for fact_item in facts_data:
                fact_dict = {
                    'fact': fact_item['fact'],
                    'confidence_score': fact_item['confidence'],
                    'source_content': conversation_content[:500]  # Store snippet
                }
                extracted_facts.append(fact_dict)
            
            return extracted_facts
            
        except Exception as e:
            logger.error(f"Error extracting facts: {e}")
            return []
    
    def store_facts(self, facts: List[Dict[str, Any]]):
        """Store extracted facts in database"""
        with sqlite3.connect(self.db_path) as conn:
            for fact in facts:
                conn.execute("""
                    INSERT INTO extracted_facts 
                    (session_id, fact, confidence_score, source_content) 
                    VALUES (?, ?, ?, ?)
                """, (
                    self.session_id,
                    fact['fact'],
                    fact['confidence_score'],
                    fact['source_content']
                ))
        
        self._manage_fact_limit()
        logger.info(f"Stored {len(facts)} facts to long-term memory")
    
    def _manage_fact_limit(self):
        """Remove oldest facts if limit exceeded"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM extracted_facts WHERE session_id = ?
            """, (self.session_id,))
            
            count = cursor.fetchone()[0]
            
            if count > self.max_facts:
                excess = count - self.max_facts
                conn.execute("""
                    DELETE FROM extracted_facts 
                    WHERE session_id = ? 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                """, (self.session_id, excess))
    
    def retrieve_relevant_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve facts relevant to current query"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT fact, confidence_score, timestamp 
                FROM extracted_facts 
                WHERE session_id = ? AND fact LIKE ? 
                ORDER BY confidence_score DESC, timestamp DESC 
                LIMIT ?
            """, (self.session_id, f"%{query}%", limit))
            
            facts = []
            for fact, confidence, timestamp in cursor.fetchall():
                facts.append({
                    'fact': fact,
                    'confidence_score': confidence,
                    'timestamp': timestamp
                })
            
            return facts
    
    def get_memory_summary(self) -> str:
        """Get summary of stored facts for context"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT fact FROM extracted_facts 
                WHERE session_id = ? 
                ORDER BY confidence_score DESC, timestamp DESC 
                LIMIT 20
            """, (self.session_id,))
            
            facts = [row[0] for row in cursor.fetchall()]
            return "\n".join([f"- {fact}" for fact in facts])
    
    def add_memory_block(self, block_type: str, content: str, priority: int = 1):
        """Add a memory block for persistent information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memory_blocks (block_type, content, priority, session_id) 
                VALUES (?, ?, ?, ?)
            """, (block_type, content, priority, self.session_id))
        
        logger.info(f"Added memory block of type: {block_type}")
    
    def get_memory_blocks(self, block_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve memory blocks by type"""
        with sqlite3.connect(self.db_path) as conn:
            if block_type:
                cursor = conn.execute("""
                    SELECT content, priority, created_at 
                    FROM memory_blocks 
                    WHERE session_id = ? AND block_type = ? 
                    ORDER BY priority DESC, created_at DESC
                """, (self.session_id, block_type))
            else:
                cursor = conn.execute("""
                    SELECT content, priority, created_at 
                    FROM memory_blocks 
                    WHERE session_id = ? 
                    ORDER BY priority DESC, created_at DESC
                """, (self.session_id,))
            
            blocks = []
            for content, priority, created_at in cursor.fetchall():
                blocks.append({
                    'content': content,
                    'priority': priority,
                    'created_at': created_at
                })
            
            return blocks