import unittest

class TestCoreLogic(unittest.TestCase):
    """Test core system logic without external dependencies"""
    
    def test_token_estimation(self):
        """Test token counting approximation"""
        test_cases = [
            ("Hello world", 2),
            ("", 0),
            ("A" * 20, 5),  # 20 chars / 4 = 5 tokens
            ("This is a longer message for testing", 9)
        ]
        
        for text, expected in test_cases:
            tokens = len(text) // 4
            self.assertEqual(tokens, expected)
    
    def test_query_complexity_scoring(self):
        """Test query complexity detection logic"""
        def score_complexity(query):
            words = len(query.split())
            score = 0
            
            # Length scoring
            if words > 10: score += 3
            elif words > 6: score += 1
            
            # Keyword scoring
            complex_keywords = ['analyze', 'compare', 'evaluate', 'assess']
            if any(kw in query.lower() for kw in complex_keywords):
                score += 2
            
            # Multiple questions
            if query.count('?') > 1:
                score += 1
            
            return 'complex' if score >= 3 else 'simple'
        
        # Test cases
        simple_queries = [
            "What is AI?",
            "Define machine learning",
            "Who invented Python?"
        ]
        
        complex_queries = [
            "Analyze the impact of AI on healthcare systems",
            "Compare supervised and unsupervised learning methods and evaluate their effectiveness",
            "What is AI? How does it work? What are the implications?"
        ]
        
        for query in simple_queries:
            self.assertEqual(score_complexity(query), 'simple')
        
        for query in complex_queries:
            self.assertEqual(score_complexity(query), 'complex')
    
    def test_query_type_detection(self):
        """Test query type classification"""
        def classify_query(query):
            q = query.lower()
            
            if any(word in q for word in ['what', 'who', 'when', 'where', 'define']):
                return 'search'
            elif any(word in q for word in ['analyze', 'compare', 'evaluate']):
                return 'analysis'
            elif any(word in q for word in ['summarize', 'summary', 'brief']):
                return 'summary'
            else:
                return 'search'  # default
        
        test_cases = [
            ("What is machine learning?", "search"),
            ("Analyze the data trends", "analysis"),
            ("Summarize the document", "summary"),
            ("Compare AI models", "analysis"),
            ("Random query text", "search")
        ]
        
        for query, expected_type in test_cases:
            result = classify_query(query)
            self.assertEqual(result, expected_type)
    
    def test_priority_sorting(self):
        """Test priority-based sorting logic"""
        items = [
            {'content': 'Low priority', 'priority': 1},
            {'content': 'High priority', 'priority': 5},
            {'content': 'Medium priority', 'priority': 3}
        ]
        
        # Sort by priority (highest first)
        sorted_items = sorted(items, key=lambda x: x['priority'], reverse=True)
        
        self.assertEqual(sorted_items[0]['content'], 'High priority')
        self.assertEqual(sorted_items[1]['content'], 'Medium priority')
        self.assertEqual(sorted_items[2]['content'], 'Low priority')

if __name__ == '__main__':
    unittest.main()