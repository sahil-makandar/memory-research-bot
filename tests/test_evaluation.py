import pytest
import asyncio
from src.testing.evaluator import AgentEvaluator, DEFAULT_TEST_SUITE

class TestAgentEvaluator:
    def setup_method(self):
        self.evaluator = AgentEvaluator()
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_evaluation(self):
        test_cases = [
            {
                'stored_facts': ['User works at Microsoft', 'User is interested in AI'],
                'query': 'What programming languages should I learn?',
                'expected_context': ['Microsoft', 'AI']
            }
        ]
        
        result = await self.evaluator.evaluate_memory_retrieval(test_cases)
        
        assert result.metric_name == "memory_retrieval_accuracy"
        assert 0 <= result.score <= 1
        assert result.total_test_cases == 1
        assert 'test_results' in result.details
    
    @pytest.mark.asyncio
    async def test_query_decomposition_evaluation(self):
        test_cases = [
            {
                'query': 'Analyze Adobe\'s financial performance and compare it to competitors',
                'expected_sub_queries': 4,
                'expected_decomposition': True
            }
        ]
        
        result = await self.evaluator.evaluate_query_decomposition(test_cases)
        
        assert result.metric_name == "query_decomposition_quality"
        assert 0 <= result.score <= 1
        assert result.total_test_cases == 1
    
    @pytest.mark.asyncio
    async def test_response_quality_evaluation(self):
        test_cases = [
            {
                'query': 'What is Adobe\'s revenue?',
                'expected_content': ['revenue', 'Adobe'],
                'min_confidence': 0.6
            }
        ]
        
        result = await self.evaluator.evaluate_response_quality(test_cases)
        
        assert result.metric_name == "response_quality"
        assert 0 <= result.score <= 1
        assert result.total_test_cases == 1
    
    @pytest.mark.asyncio
    async def test_end_to_end_benchmark(self):
        result = await self.evaluator.run_benchmark(DEFAULT_TEST_SUITE)
        
        assert isinstance(result, dict)
        assert 'memory_retrieval' in result
        assert 'query_decomposition' in result
        assert 'response_quality' in result
        
        for metric_result in result.values():
            assert hasattr(metric_result, 'score')
            assert hasattr(metric_result, 'metric_name')
    
    def test_decomposition_quality_assessment(self):
        """Test decomposition quality assessment"""
        # Good decomposition
        good_sub_queries = [
            "What is Adobe's revenue?",
            "Who are Adobe's competitors?",
            "How does Adobe compare financially?"
        ]
        
        score = self.evaluator._assess_decomposition_quality(
            "Analyze Adobe's financial performance", 
            good_sub_queries
        )
        
        assert score > 0.5
        
        # Poor decomposition
        poor_sub_queries = ["What?", "How?"]
        
        score = self.evaluator._assess_decomposition_quality(
            "Analyze Adobe's financial performance", 
            poor_sub_queries
        )
        
        assert score < 0.8