import unittest
import json

class TestQueryProcessing(unittest.TestCase):
    """Test query processing and planning logic"""
    
    def test_query_decomposition_logic(self):
        """Test logic for breaking down complex queries"""
        def decompose_query(query):
            # Simple decomposition based on conjunctions and question marks
            parts = []
            
            # Split on 'and' and question marks
            segments = query.replace('?', '?|').split('|')
            segments = [s.strip() for s in segments if s.strip()]
            
            for i, segment in enumerate(segments):
                if 'and' in segment.lower():
                    sub_parts = segment.split(' and ')
                    for part in sub_parts:
                        if part.strip():
                            parts.append({
                                'sub_query': part.strip(),
                                'priority': len(sub_parts) - sub_parts.index(part),
                                'type': 'search'
                            })
                else:
                    parts.append({
                        'sub_query': segment,
                        'priority': len(segments) - i,
                        'type': 'search'
                    })
            
            return parts if len(parts) > 1 else [{'sub_query': query, 'priority': 1, 'type': 'search'}]
        
        # Test simple query (no decomposition needed)
        simple_result = decompose_query("What is machine learning?")
        self.assertEqual(len(simple_result), 1)
        self.assertEqual(simple_result[0]['sub_query'], "What is machine learning?")
        
        # Test complex query with multiple parts
        complex_query = "What is AI? How does it work?"
        complex_result = decompose_query(complex_query)
        self.assertGreater(len(complex_result), 1)
    
    def test_tool_selection_logic(self):
        """Test tool selection based on query type"""
        def select_tool(query_type):
            tool_mapping = {
                'search': 'document_retriever',
                'analysis': 'content_analyzer',
                'summary': 'summarizer',
                'keywords': 'keyword_extractor'
            }
            return tool_mapping.get(query_type, 'document_retriever')
        
        test_cases = [
            ('search', 'document_retriever'),
            ('analysis', 'content_analyzer'),
            ('summary', 'summarizer'),
            ('unknown', 'document_retriever')  # default
        ]
        
        for query_type, expected_tool in test_cases:
            result = select_tool(query_type)
            self.assertEqual(result, expected_tool)
    
    def test_execution_order_planning(self):
        """Test execution order based on priority"""
        sub_queries = [
            {'sub_query': 'Low priority task', 'priority': 1},
            {'sub_query': 'High priority task', 'priority': 5},
            {'sub_query': 'Medium priority task', 'priority': 3}
        ]
        
        # Sort by priority (highest first)
        execution_order = sorted(range(len(sub_queries)), 
                               key=lambda i: sub_queries[i]['priority'], 
                               reverse=True)
        
        # Verify correct order: indices should be [1, 2, 0] (high, medium, low)
        self.assertEqual(execution_order, [1, 2, 0])
        
        # Verify the actual queries are in correct order
        ordered_queries = [sub_queries[i]['sub_query'] for i in execution_order]
        self.assertEqual(ordered_queries[0], 'High priority task')
        self.assertEqual(ordered_queries[1], 'Medium priority task')
        self.assertEqual(ordered_queries[2], 'Low priority task')
    
    def test_result_synthesis(self):
        """Test combining multiple query results"""
        results = [
            {'sub_query': 'What is AI?', 'result': 'AI is artificial intelligence'},
            {'sub_query': 'How does ML work?', 'result': 'ML uses algorithms to learn patterns'},
            {'sub_query': 'What are applications?', 'result': 'AI is used in healthcare, finance, etc.'}
        ]
        
        def synthesize_results(results):
            if not results:
                return "No results found"
            
            synthesis_parts = ["Query Results:"]
            for i, result in enumerate(results, 1):
                synthesis_parts.append(f"{i}. {result['sub_query']}")
                synthesis_parts.append(f"   Answer: {result['result']}")
            
            return "\n".join(synthesis_parts)
        
        synthesized = synthesize_results(results)
        
        self.assertIn("Query Results:", synthesized)
        self.assertIn("What is AI?", synthesized)
        self.assertIn("AI is artificial intelligence", synthesized)
        self.assertIn("3.", synthesized)  # Should have 3 numbered results
    
    def test_context_integration(self):
        """Test integrating memory context with query processing"""
        memory_context = {
            'short_term_context': 'user: I am a data scientist\nassistant: Great! How can I help?',
            'relevant_facts': [
                {'fact': 'User is a data scientist', 'confidence_score': 0.9}
            ],
            'memory_summary': 'User background: data science professional'
        }
        
        query = "What programming languages should I learn?"
        
        def integrate_context(query, context):
            # Simple context integration
            context_info = []
            
            if context['relevant_facts']:
                for fact in context['relevant_facts']:
                    if fact['confidence_score'] > 0.8:
                        context_info.append(fact['fact'])
            
            if context_info:
                enhanced_query = f"Context: {'; '.join(context_info)}. Query: {query}"
            else:
                enhanced_query = query
            
            return enhanced_query
        
        enhanced = integrate_context(query, memory_context)
        
        self.assertIn("User is a data scientist", enhanced)
        self.assertIn("What programming languages should I learn?", enhanced)
        self.assertIn("Context:", enhanced)

if __name__ == '__main__':
    unittest.main()