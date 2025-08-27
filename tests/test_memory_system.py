import unittest
import sqlite3
import tempfile
import os
from datetime import datetime

class TestMemorySystem(unittest.TestCase):
    """Test memory management logic and database operations"""
    
    def setUp(self):
        """Create temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
    
    def tearDown(self):
        """Clean up temporary database"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_database_schema_creation(self):
        """Test database table creation"""
        with sqlite3.connect(self.temp_db.name) as conn:
            # Create short-term memory table
            conn.execute("""
                CREATE TABLE short_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create long-term memory table
            conn.execute("""
                CREATE TABLE extracted_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    confidence_score REAL,
                    source_content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Verify tables exist
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('short_term_memory', tables)
            self.assertIn('extracted_facts', tables)
    
    def test_fifo_buffer_simulation(self):
        """Test FIFO buffer logic for short-term memory"""
        buffer = []
        max_tokens = 100
        current_tokens = 0
        
        messages = [
            ("First message", 25),
            ("Second message", 30),
            ("Third message", 35),
            ("Fourth message", 40)  # This should cause overflow
        ]
        
        for content, tokens in messages:
            # Remove old messages if adding new one exceeds limit
            while current_tokens + tokens > max_tokens and buffer:
                old_content, old_tokens = buffer.pop(0)
                current_tokens -= old_tokens
            
            # Add new message
            buffer.append((content, tokens))
            current_tokens += tokens
        
        # Verify buffer state
        self.assertLessEqual(current_tokens, max_tokens)
        self.assertEqual(len(buffer), 2)  # Should have 2 messages left
        self.assertEqual(buffer[0][0], "Third message")  # First should be third message
        self.assertEqual(buffer[1][0], "Fourth message")  # Second should be fourth message
    
    def test_fact_storage_and_retrieval(self):
        """Test fact storage and retrieval operations"""
        with sqlite3.connect(self.temp_db.name) as conn:
            # Create facts table
            conn.execute("""
                CREATE TABLE extracted_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    confidence_score REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test facts
            facts = [
                ("test_session", "User is a software engineer", 0.9),
                ("test_session", "User prefers Python programming", 0.8),
                ("test_session", "User works at tech company", 0.7)
            ]
            
            for session_id, fact, confidence in facts:
                conn.execute("""
                    INSERT INTO extracted_facts (session_id, fact, confidence_score) 
                    VALUES (?, ?, ?)
                """, (session_id, fact, confidence))
            
            # Retrieve facts by relevance (confidence score)
            cursor = conn.execute("""
                SELECT fact, confidence_score 
                FROM extracted_facts 
                WHERE session_id = ? AND fact LIKE ? 
                ORDER BY confidence_score DESC
            """, ("test_session", "%software%"))
            
            results = cursor.fetchall()
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "User is a software engineer")
            self.assertEqual(results[0][1], 0.9)
    
    def test_memory_block_prioritization(self):
        """Test memory block priority management"""
        blocks = [
            {'type': 'static', 'content': 'System instruction', 'priority': 5},
            {'type': 'fact', 'content': 'User preference', 'priority': 3},
            {'type': 'dynamic', 'content': 'Temporary context', 'priority': 1},
            {'type': 'vector', 'content': 'Document snippet', 'priority': 4}
        ]
        
        # Sort by priority (highest first)
        sorted_blocks = sorted(blocks, key=lambda x: x['priority'], reverse=True)
        
        # Verify correct ordering
        priorities = [block['priority'] for block in sorted_blocks]
        self.assertEqual(priorities, [5, 4, 3, 1])
        
        # Test context selection (top N blocks)
        top_3_blocks = sorted_blocks[:3]
        self.assertEqual(len(top_3_blocks), 3)
        self.assertEqual(top_3_blocks[0]['type'], 'static')
    
    def test_session_isolation(self):
        """Test that different sessions are properly isolated"""
        with sqlite3.connect(self.temp_db.name) as conn:
            conn.execute("""
                CREATE TABLE short_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Insert messages for different sessions
            messages = [
                ("session_1", "Message from session 1"),
                ("session_2", "Message from session 2"),
                ("session_1", "Another message from session 1")
            ]
            
            for session_id, content in messages:
                conn.execute("""
                    INSERT INTO short_term_memory (session_id, message_content) 
                    VALUES (?, ?)
                """, (session_id, content))
            
            # Retrieve messages for session 1 only
            cursor = conn.execute("""
                SELECT message_content 
                FROM short_term_memory 
                WHERE session_id = ? AND is_active = TRUE
            """, ("session_1",))
            
            session_1_messages = [row[0] for row in cursor.fetchall()]
            
            self.assertEqual(len(session_1_messages), 2)
            self.assertIn("Message from session 1", session_1_messages)
            self.assertIn("Another message from session 1", session_1_messages)
            self.assertNotIn("Message from session 2", session_1_messages)

if __name__ == '__main__':
    unittest.main()