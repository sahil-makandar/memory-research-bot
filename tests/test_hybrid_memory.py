import pytest
import tempfile
import os
from src.memory.hybrid_memory import HybridMemory

class TestHybridMemory:
    def setup_method(self):
        # Use temporary database for clean tests
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create memory components with temp database
        from src.memory.short_term import ShortTermMemory
        from src.memory.long_term import LongTermMemory
        from src.vector_store import VectorStore
        
        # Create clean instances
        self.memory = HybridMemory("test_session")
        self.memory.short_term = ShortTermMemory("test_session", db_path=self.temp_db.name)
        self.memory.long_term = LongTermMemory("test_session", db_path=self.temp_db.name)
        self.memory.vector_memory = VectorStore("test_memory")
    
    def teardown_method(self):
        # Clean up temp database
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_add_conversation(self):
        """Test adding conversation to hybrid memory"""
        user_msg = "What is AI?"
        assistant_msg = "AI is artificial intelligence..."
        facts = ["User asked about AI"]
        
        self.memory.add_conversation(user_msg, assistant_msg, facts)
        
        # Check short-term memory
        assert len(self.memory.short_term.messages) >= 2
        
        # Check long-term memory
        stored_facts = self.memory.long_term.get_all_facts()
        assert len(stored_facts) >= 1
        assert any(fact['fact'] == "User asked about AI" for fact in stored_facts)
    
    def test_retrieve_context(self):
        """Test context retrieval from hybrid memory"""
        # Add some conversation
        self.memory.add_conversation(
            "What is machine learning?",
            "Machine learning is a subset of AI...",
            ["User interested in machine learning"]
        )
        
        # Retrieve context
        context = self.memory.retrieve_context("Tell me about AI")
        
        assert 'short_term' in context
        assert 'long_term_facts' in context
        assert 'semantic_matches' in context
        assert context['retrieval_method'] == 'hybrid'
    
    def test_memory_stats(self):
        """Test memory statistics"""
        # Add some data
        self.memory.add_conversation(
            "Test query",
            "Test response",
            ["Test fact"]
        )
        
        stats = self.memory.get_memory_stats()
        
        assert 'short_term_messages' in stats
        assert 'long_term_facts' in stats
        assert 'vector_documents' in stats
        assert stats['session_id'] == "test_session"
        assert stats['short_term_messages'] >= 2
        assert stats['long_term_facts'] >= 1