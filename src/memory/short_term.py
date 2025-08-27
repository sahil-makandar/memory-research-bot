from typing import List, Optional, Dict, Any
from llama_index.core.llms import ChatMessage
import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger('memory_system')

class ShortTermMemory:
    """Token-limited FIFO buffer for conversation context management."""
    
    def __init__(self, session_id: str, token_limit: int = 40000, db_path: str = "./data/memory.db"):
        self.session_id = session_id
        self.token_limit = token_limit
        self.db_path = db_path
        self.current_tokens = 0
        self.message_buffer: List[ChatMessage] = []
        self._init_database()
        self._load_active_messages()
    
    def _init_database(self):
        """Initialize SQLite database for persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
    
    def _load_active_messages(self):
        """Load active messages from database on initialization"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT message_role, message_content, token_count 
                FROM short_term_memory 
                WHERE session_id = ? AND is_active = TRUE 
                ORDER BY timestamp ASC
            """, (self.session_id,))
            
            for role, content, token_count in cursor.fetchall():
                message = ChatMessage(role=role, content=content)
                self.message_buffer.append(message)
                self.current_tokens += token_count
    
    def add_message(self, message: ChatMessage) -> None:
        """Add message to short-term memory with token management."""
        token_count = self._estimate_tokens(message.content)
        
        while self.current_tokens + token_count > self.token_limit and self.message_buffer:
            self._flush_oldest_message()
        
        self.message_buffer.append(message)
        self.current_tokens += token_count
        self._persist_message(message, token_count)
        
        logger.info(f"Added message to short-term memory. Current tokens: {self.current_tokens}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using rough approximation"""
        return len(text) // 4
    
    def _flush_oldest_message(self) -> None:
        """Remove oldest message and update token count"""
        if self.message_buffer:
            oldest_message = self.message_buffer.pop(0)
            self.current_tokens -= self._estimate_tokens(oldest_message.content)
            self._mark_message_inactive(oldest_message)
            logger.info(f"Flushed oldest message. Remaining tokens: {self.current_tokens}")
    
    def _persist_message(self, message: ChatMessage, token_count: int):
        """Persist message to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO short_term_memory 
                (session_id, message_role, message_content, token_count) 
                VALUES (?, ?, ?, ?)
            """, (self.session_id, message.role, message.content, token_count))
    
    def _mark_message_inactive(self, message: ChatMessage):
        """Mark message as inactive in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE short_term_memory 
                SET is_active = FALSE 
                WHERE session_id = ? AND message_content = ? AND is_active = TRUE
            """, (self.session_id, message.content))
    
    def get_context(self) -> List[ChatMessage]:
        """Retrieve current conversation context"""
        return self.message_buffer.copy()
    
    def get_context_string(self) -> str:
        """Get conversation context as formatted string"""
        context_parts = []
        for msg in self.message_buffer:
            context_parts.append(f"{msg.role}: {msg.content}")
        return "\n".join(context_parts)
    
    def clear_session(self):
        """Clear current session memory"""
        self.message_buffer.clear()
        self.current_tokens = 0
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE short_term_memory 
                SET is_active = FALSE 
                WHERE session_id = ?
            """, (self.session_id,))