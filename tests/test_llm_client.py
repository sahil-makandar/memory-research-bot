import pytest
from src.llm_client import LLMClient, QueryComplexity, SubQueries, LLMResponse

class TestLLMClient:
    def setup_method(self):
        self.llm_client = LLMClient()
        self.context = {
            'session': {
                'messages': [],
                'facts': [{'fact': 'User interested in Adobe research', 'confidence': 0.8}]
            }
        }
    
    def test_simple_query_processing(self):
        """Test simple query is processed without decomposition"""
        result = self.llm_client.process_query("What is Adobe revenue?", self.context)
        
        assert result['decomposed'] == False
        assert result['complexity_score'] < 0.5
        assert len(result['sub_queries']) == 0
        assert 'response' in result
        assert result['response'] != ""
    
    def test_complex_query_decomposition(self):
        """Test complex query gets decomposed into sub-queries"""
        complex_query = "Analyze Adobe's comprehensive business performance and compare with competitors"
        result = self.llm_client.process_query(complex_query, self.context)
        
        assert result['decomposed'] == True
        assert result['complexity_score'] > 0.5
        assert len(result['sub_queries']) > 0
        assert len(result['sub_results']) > 0
        assert 'Comprehensive analysis' in result['response']
    
    def test_complexity_analysis(self):
        """Test LLM complexity analysis with different query types"""
        # Simple query
        simple_complexity = self.llm_client._llm_analyze_complexity("Adobe revenue", self.context)
        assert simple_complexity.needs_decomposition == False
        assert simple_complexity.complexity_score < 0.5
        
        # Complex query
        complex_complexity = self.llm_client._llm_analyze_complexity(
            "Analyze and compare Adobe's financial performance with detailed breakdown", 
            self.context
        )
        assert complex_complexity.needs_decomposition == True
        assert complex_complexity.complexity_score > 0.5
    
    def test_sub_query_generation(self):
        """Test LLM generates relevant sub-queries"""
        # Adobe analysis query
        sub_queries = self.llm_client._llm_generate_sub_queries(
            "Analyze Adobe comprehensive performance", 
            self.context
        )
        
        assert len(sub_queries.sub_queries) == 4
        assert any("financial" in sq.lower() for sq in sub_queries.sub_queries)
        assert any("segments" in sq.lower() for sq in sub_queries.sub_queries)
        
        # Comparison query
        compare_queries = self.llm_client._llm_generate_sub_queries(
            "Compare Adobe with competitors", 
            self.context
        )
        
        assert len(compare_queries.sub_queries) == 4
        assert any("competitors" in sq.lower() for sq in compare_queries.sub_queries)
    
    def test_data_gathering(self):
        """Test data gathering from memory and vector store"""
        data = self.llm_client._gather_data_for_query("Adobe revenue", self.context)
        
        assert 'memory' in data
        assert 'vector_search' in data
        assert isinstance(data['vector_search'], list)
        
        # Should find relevant Adobe data in vector store
        vector_results = data['vector_search']
        assert len(vector_results) > 0
        assert any('adobe' in result['content'].lower() for result in vector_results)
    
    def test_response_generation_with_data(self):
        """Test LLM generates response using gathered data"""
        data = {
            'memory': {'long_term_facts': [{'fact': 'User researching Adobe'}]},
            'vector_search': [
                {'doc_id': 'adobe_revenue', 'content': 'Adobe revenue $19.41 billion', 'score': 0.9}
            ]
        }
        
        response = self.llm_client._llm_generate_response("Adobe revenue", data, self.context)
        
        assert isinstance(response, LLMResponse)
        assert response.confidence > 0.5
        assert 'adobe_revenue' in response.sources_used
        assert '19.41 billion' in response.response
    
    def test_response_synthesis(self):
        """Test LLM synthesizes sub-query results"""
        sub_results = [
            {
                'query': 'Adobe revenue',
                'response': 'Adobe reported $19.41 billion revenue',
                'confidence': 0.8,
                'sources': ['adobe_revenue']
            },
            {
                'query': 'Adobe segments',
                'response': 'Adobe has three main segments',
                'confidence': 0.9,
                'sources': ['adobe_segments']
            }
        ]
        
        synthesis = self.llm_client._llm_synthesize_results(
            "Analyze Adobe performance", 
            sub_results, 
            self.context
        )
        
        assert isinstance(synthesis, LLMResponse)
        assert synthesis.confidence == 0.9
        assert 'Comprehensive analysis' in synthesis.response
        assert '1.' in synthesis.response and '2.' in synthesis.response
    
    def test_fact_extraction(self):
        """Test conversation fact extraction"""
        user_msg = "I'm researching Adobe for my investment thesis"
        assistant_msg = "Adobe reported strong revenue growth of 9% year-over-year"
        
        facts = self.llm_client.extract_conversation_facts(user_msg, assistant_msg)
        
        assert isinstance(facts, list)
        assert len(facts) > 0
        assert any('adobe' in fact.lower() for fact in facts)
    
    def test_vector_store_integration(self):
        """Test vector store has sample Adobe data"""
        results = self.llm_client.vector_store.search("Adobe revenue", top_k=3)
        
        assert len(results) > 0
        assert any('19.41 billion' in result['content'] for result in results)
        assert any('revenue' in result['content'].lower() for result in results)
    
    def test_memory_context_usage(self):
        """Test memory context is used in response generation"""
        context_with_facts = {
            'session': {
                'messages': [],
                'facts': [
                    {'fact': 'User is an investment analyst', 'confidence': 0.9},
                    {'fact': 'User focuses on tech companies', 'confidence': 0.8}
                ]
            }
        }
        
        result = self.llm_client.process_query("Adobe strategy", context_with_facts)
        
        # Should use memory context in response
        assert 'response' in result
        assert result['response'] != ""