import pytest
from src.memory.hybrid_memory import HybridMemory
from llama_index.core.llms import ChatMessage

class TestHybridMemorySystem:
    def setup_method(self):
        import time
        self.memory = HybridMemory(f"test_session_{int(time.time() * 1000000)}")
    
    def test_conversation_storage_and_retrieval(self):
        """Test storing conversation and retrieving context"""
        user_msg = "What is Adobe's revenue?"
        assistant_msg = "Adobe reported $19.41 billion in revenue for 2023"
        facts = ["User asked about Adobe revenue", "Adobe revenue is $19.41 billion"]
        
        # Store conversation
        self.memory.add_conversation(user_msg, assistant_msg, facts)
        
        # Verify short-term memory (should have at least 2 new messages)
        messages = self.memory.short_term.messages
        assert len(messages) >= 2
        assert messages[-2].content == user_msg
        assert messages[-1].content == assistant_msg
        assert self.memory.short_term.messages[0].content == user_msg
        assert self.memory.short_term.messages[1].content == assistant_msg
        
        # Verify long-term facts
        stored_facts = self.memory.long_term.get_all_facts()
        assert len(stored_facts) == 2
        assert any("Adobe revenue" in fact['fact'] for fact in stored_facts)
    
    def test_context_retrieval(self):
        """Test hybrid context retrieval"""
        # Add some conversation history
        self.memory.add_conversation(
            "Tell me about Adobe",
            "Adobe is a software company specializing in creative tools",
            ["User interested in Adobe", "Adobe makes creative software"]
        )
        
        # Retrieve context for related query
        context = self.memory.retrieve_context("Adobe financial performance")
        
        assert 'short_term' in context
        assert 'long_term_facts' in context
        assert 'semantic_matches' in context
        assert context['retrieval_method'] == 'hybrid'
        
        # Should have context structure (facts may be empty initially)
        assert isinstance(context['long_term_facts'], list)
    
    def test_memory_stats(self):
        """Test memory statistics tracking"""
        # Add some data
        self.memory.add_conversation(
            "Adobe question",
            "Adobe answer",
            ["Adobe fact"]
        )
        
        stats = self.memory.get_memory_stats()
        
        assert 'short_term_messages' in stats
        assert 'long_term_facts' in stats
        assert 'vector_documents' in stats
        assert 'session_id' in stats
        assert stats['session_id'].startswith("test_session_")
        assert stats['short_term_messages'] >= 2
        assert stats['long_term_facts'] == 1
    
    def test_token_management(self):
        """Test short-term memory token limits"""
        # Add many messages to test FIFO behavior
        for i in range(10):
            self.memory.short_term.add_message(
                ChatMessage(role="user", content=f"Long message {i} " * 100)
            )
        
        # Should maintain token limit
        assert self.memory.short_term.current_tokens <= self.memory.short_term.token_limit
        
        # Should maintain token limit
        assert self.memory.short_term.current_tokens <= self.memory.short_term.token_limit
    
    def test_fact_confidence_scoring(self):
        """Test fact storage with confidence scores"""
        facts_with_confidence = [
            "Adobe revenue is $19.41 billion",  # High confidence fact
            "User might be interested in competitors"  # Lower confidence
        ]
        
        self.memory.add_conversation(
            "Adobe revenue?",
            "Adobe reported $19.41 billion",
            facts_with_confidence
        )
        
        stored_facts = self.memory.long_term.get_all_facts()
        assert all('confidence' in fact for fact in stored_facts)
        assert all(0.0 <= fact['confidence'] <= 1.0 for fact in stored_facts)
    
    def test_semantic_search_integration(self):
        """Test vector store integration for semantic search"""
        # Add conversation that should be searchable
        self.memory.add_conversation(
            "Adobe's AI strategy",
            "Adobe is investing heavily in AI with Firefly and Sensei",
            ["Adobe has AI initiatives", "Firefly is Adobe's generative AI"]
        )
        
        # Search for related content
        context = self.memory.retrieve_context("artificial intelligence Adobe")
        
        # Should find semantic matches
        assert len(context['semantic_matches']) > 0
        semantic_match = context['semantic_matches'][0]
        assert 'content' in semantic_match
        assert 'relevance' in semantic_match
        assert 'metadata' in semantic_match