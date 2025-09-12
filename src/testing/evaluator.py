import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from ..llm_client import LLMClient
from ..memory.hybrid_memory import HybridMemory

@dataclass
class EvaluationResult:
    metric_name: str
    score: float
    details: Dict[str, Any]
    test_cases_passed: int
    total_test_cases: int

class AgentEvaluator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.test_sessions = {}
        
    async def evaluate_memory_retrieval(self, test_cases: List[Dict]) -> EvaluationResult:
        passed = 0
        details = []
        
        for case in test_cases:
            session_id = f"eval_{int(time.time())}"
            memory = HybridMemory(session_id)
            
            # Setup test data
            for fact in case.get('stored_facts', []):
                memory.long_term.store_fact(fact, confidence=0.8)
            
            # Test memory retrieval
            context = memory.retrieve_context(case['query'])
            
            # Check if expected context is retrieved
            retrieved_content = str(context).lower()
            expected_found = sum(1 for expected in case['expected_context'] 
                               if expected.lower() in retrieved_content)
            
            score = expected_found / len(case['expected_context'])
            passed += 1 if score >= 0.6 else 0
            
            details.append({
                'query': case['query'],
                'expected_context': case['expected_context'],
                'retrieved_context': context,
                'score': score,
                'passed': score >= 0.6
            })
        
        return EvaluationResult(
            metric_name="memory_retrieval_accuracy",
            score=passed / len(test_cases),
            details={'test_results': details},
            test_cases_passed=passed,
            total_test_cases=len(test_cases)
        )
    
    async def evaluate_query_decomposition(self, test_cases: List[Dict]) -> EvaluationResult:
        passed = 0
        details = []
        
        for case in test_cases:
            query = case['query']
            expected_decomposition = case['expected_decomposition']
            expected_sub_count = case['expected_sub_queries']
            
            # Test complexity analysis
            complexity = self.llm_client._llm_analyze_complexity(query, {})
            
            # Test sub-query generation if complex
            if complexity.needs_decomposition:
                sub_queries_result = self.llm_client._llm_generate_sub_queries(query, {})
                sub_count = len(sub_queries_result.sub_queries)
                
                decomposition_correct = expected_decomposition == True
                count_match = abs(sub_count - expected_sub_count) <= 1
                quality_score = self._assess_decomposition_quality(query, sub_queries_result.sub_queries)
                
                test_passed = decomposition_correct and count_match and quality_score >= 0.7
                
                details.append({
                    'query': query,
                    'complexity_score': complexity.complexity_score,
                    'needs_decomposition': complexity.needs_decomposition,
                    'sub_queries': sub_queries_result.sub_queries,
                    'sub_count': sub_count,
                    'quality_score': quality_score,
                    'passed': test_passed
                })
            else:
                test_passed = expected_decomposition == False
                details.append({
                    'query': query,
                    'complexity_score': complexity.complexity_score,
                    'needs_decomposition': complexity.needs_decomposition,
                    'passed': test_passed
                })
            
            if test_passed:
                passed += 1
        
        return EvaluationResult(
            metric_name="query_decomposition_quality",
            score=passed / len(test_cases),
            details={'test_results': details},
            test_cases_passed=passed,
            total_test_cases=len(test_cases)
        )
    
    async def evaluate_response_quality(self, test_cases: List[Dict]) -> EvaluationResult:
        passed = 0
        details = []
        
        for case in test_cases:
            query = case['query']
            expected_content = case['expected_content']
            min_confidence = case['min_confidence']
            
            # Process query
            context = {'session': {'messages': [], 'facts': []}}
            result = self.llm_client.process_query(query, context)
            
            # Check response quality
            response = result['response']
            content_score = sum(1 for content in expected_content 
                              if content.lower() in response.lower()) / len(expected_content)
            
            # Check if sources are used (if specified)
            sources_correct = True
            if 'expected_sources' in case:
                # This would need to be implemented based on actual source tracking
                pass
            
            test_passed = content_score >= 0.6 and sources_correct
            
            details.append({
                'query': query,
                'response': response[:200] + '...' if len(response) > 200 else response,
                'expected_content': expected_content,
                'content_score': content_score,
                'complexity_score': result.get('complexity_score', 0),
                'decomposed': result.get('decomposed', False),
                'passed': test_passed
            })
            
            if test_passed:
                passed += 1
        
        return EvaluationResult(
            metric_name="response_quality",
            score=passed / len(test_cases),
            details={'test_results': details},
            test_cases_passed=passed,
            total_test_cases=len(test_cases)
        )
    
    async def evaluate_structured_output(self, test_cases: List[Dict]) -> EvaluationResult:
        passed = 0
        details = []
        
        for case in test_cases:
            query = case['query']
            expected_fields = case['expected_fields']
            expected_types = case.get('expected_types', {})
            
            # Process query
            context = {'session': {'messages': [], 'facts': []}}
            result = self.llm_client.process_query(query, context)
            
            # Check structure
            fields_present = sum(1 for field in expected_fields if field in result)
            field_score = fields_present / len(expected_fields)
            
            # Check types
            type_score = 1.0
            for field, expected_type in expected_types.items():
                if field in result and not isinstance(result[field], expected_type):
                    type_score = 0.0
                    break
            
            test_passed = field_score == 1.0 and type_score == 1.0
            
            details.append({
                'query': query,
                'result_fields': list(result.keys()),
                'expected_fields': expected_fields,
                'field_score': field_score,
                'type_score': type_score,
                'passed': test_passed
            })
            
            if test_passed:
                passed += 1
        
        return EvaluationResult(
            metric_name="structured_output",
            score=passed / len(test_cases),
            details={'test_results': details},
            test_cases_passed=passed,
            total_test_cases=len(test_cases)
        )
    
    async def run_benchmark(self, test_suite: Dict[str, Any]) -> Dict[str, EvaluationResult]:
        results = {}
        
        if 'memory_retrieval' in test_suite:
            results['memory_retrieval'] = await self.evaluate_memory_retrieval(
                test_suite['memory_retrieval']['test_cases']
            )
        
        if 'query_decomposition' in test_suite:
            results['query_decomposition'] = await self.evaluate_query_decomposition(
                test_suite['query_decomposition']['test_cases']
            )
        
        if 'response_quality' in test_suite:
            results['response_quality'] = await self.evaluate_response_quality(
                test_suite['response_quality']['test_cases']
            )
        
        if 'structured_output' in test_suite:
            results['structured_output'] = await self.evaluate_structured_output(
                test_suite['structured_output']['test_cases']
            )
        
        return results
    
    def _assess_decomposition_quality(self, original_query: str, sub_queries: List[str]) -> float:
        if not sub_queries:
            return 0.0
        
        score = 0.0
        
        # Check average length (should be reasonable)
        avg_length = sum(len(q.split()) for q in sub_queries) / len(sub_queries)
        if 5 <= avg_length <= 15:
            score += 0.3
        
        # Check diversity (sub-queries should be different)
        unique_words = set()
        for q in sub_queries:
            unique_words.update(q.lower().split())
        
        if len(unique_words) >= len(sub_queries) * 2:
            score += 0.4
        
        # Check if sub-queries are answerable (contain question words or clear intent)
        answerable_count = sum(1 for q in sub_queries 
                             if any(word in q.lower() for word in ['what', 'how', 'who', 'when', 'where', 'why'])
                             or q.endswith('?'))
        if answerable_count >= len(sub_queries) * 0.6:
            score += 0.3
        
        return min(score, 1.0)

DEFAULT_TEST_SUITE = {
    "memory_retrieval": {
        "test_cases": [
            {
                "query": "What did we discuss about Adobe?",
                "expected_context": ["adobe", "revenue", "strategy"],
                "memory_types": ["short_term", "long_term", "vector_search"],
                "stored_facts": ["User asked about Adobe revenue", "Adobe revenue is $19.41 billion"]
            },
            {
                "query": "Continue our previous analysis",
                "expected_context": ["analysis", "previous"],
                "memory_types": ["short_term", "vector_search"],
                "stored_facts": ["User conducting financial analysis", "Previous discussion about market analysis"]
            },
            {
                "query": "Adobe financial performance",
                "expected_context": ["financial", "revenue", "performance"],
                "memory_types": ["vector_search", "long_term"],
                "stored_facts": ["Adobe financial data discussed", "User interested in financial metrics"]
            }
        ]
    },
    "query_decomposition": {
        "test_cases": [
            {
                "query": "Analyze Adobe's comprehensive business performance and compare with competitors",
                "expected_sub_queries": 4,
                "complexity_threshold": 0.8,
                "expected_decomposition": True
            },
            {
                "query": "What is Adobe's revenue?",
                "expected_sub_queries": 0,
                "complexity_threshold": 0.3,
                "expected_decomposition": False
            },
            {
                "query": "Compare Adobe and Salesforce market positions and strategic advantages",
                "expected_sub_queries": 4,
                "complexity_threshold": 0.7,
                "expected_decomposition": True
            }
        ]
    },
    "response_quality": {
        "test_cases": [
            {
                "query": "Adobe revenue 2023",
                "expected_content": ["19.41 billion", "revenue", "2023"],
                "min_confidence": 0.7,
                "expected_sources": ["adobe_revenue_2023"]
            },
            {
                "query": "Adobe AI strategy",
                "expected_content": ["AI", "Firefly", "strategy"],
                "min_confidence": 0.6,
                "expected_sources": ["adobe_strategy_2023"]
            },
            {
                "query": "Adobe business segments",
                "expected_content": ["Digital Media", "Digital Experience", "segments"],
                "min_confidence": 0.7,
                "expected_sources": ["adobe_segments_overview"]
            }
        ]
    },
    "structured_output": {
        "test_cases": [
            {
                "query": "Analyze Adobe comprehensive performance",
                "expected_fields": ["response", "sub_queries", "decomposed", "complexity_score"],
                "expected_types": {"decomposed": bool, "complexity_score": float}
            },
            {
                "query": "Simple Adobe query",
                "expected_fields": ["response", "sub_queries", "decomposed", "complexity_score"],
                "expected_types": {"decomposed": bool, "complexity_score": float}
            }
        ]
    }
}