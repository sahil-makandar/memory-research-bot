import asyncio
import time
import json
from typing import Dict, List, Any
from src.testing.evaluator import AgentEvaluator, DEFAULT_TEST_SUITE
from src.core.processor import process_research_query

class PerformanceBenchmark:
    def __init__(self):
        self.evaluator = AgentEvaluator()
        self.results = []
    
    async def run_response_time_benchmark(self) -> Dict[str, Any]:
        test_queries = [
            {"query": "What is Adobe's revenue?", "type": "simple"},
            {"query": "Analyze Adobe's financial performance", "type": "complex"},
            {"query": "What are Adobe's key products?", "type": "simple"},
            {"query": "Evaluate Adobe's market position", "type": "complex"}
        ]
        
        results = []
        
        for test_case in test_queries:
            times = []
            
            for i in range(3):
                start_time = time.time()
                
                try:
                    result = await process_research_query(
                        test_case["query"], 
                        f"bench_{int(time.time())}_{i}"
                    )
                    response_time = time.time() - start_time
                    times.append(response_time)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    times.append(float('inf'))
            
            valid_times = [t for t in times if t != float('inf')]
            avg_time = sum(valid_times) / len(valid_times) if valid_times else 0
            
            results.append({
                'query': test_case["query"],
                'type': test_case["type"],
                'avg_response_time': avg_time,
                'min_time': min(times),
                'max_time': max(times),
                'success_rate': len(valid_times) / len(times)
            })
        
        simple_avg = sum(r['avg_response_time'] for r in results if r['type'] == 'simple') / 2
        complex_avg = sum(r['avg_response_time'] for r in results if r['type'] == 'complex') / 2
        
        return {
            'response_time_benchmark': results,
            'summary': {
                'simple_queries_avg': simple_avg,
                'complex_queries_avg': complex_avg,
                'overall_success_rate': sum(r['success_rate'] for r in results) / len(results)
            }
        }
    
    async def run_accuracy_benchmark(self) -> Dict[str, Any]:
        return await self.evaluator.run_benchmark(DEFAULT_TEST_SUITE)
    
    async def run_memory_efficiency_benchmark(self) -> Dict[str, Any]:
        memory_tests = []
        
        for fact_count in [10, 50, 100]:
            facts = [f"Test fact {i}" for i in range(fact_count)]
            
            start_time = time.time()
            
            test_case = {
                'stored_facts': facts,
                'query': 'What do you know about the user?',
                'expected_facts': facts[:5]
            }
            
            result = self.evaluator.evaluate_memory_retrieval([test_case])
            retrieval_time = time.time() - start_time
            
            memory_tests.append({
                'fact_count': fact_count,
                'retrieval_time': retrieval_time,
                'accuracy': result.score
            })
        
        return {
            'memory_efficiency_benchmark': memory_tests,
            'summary': {
                'avg_retrieval_time': sum(t['retrieval_time'] for t in memory_tests) / len(memory_tests),
                'avg_accuracy': sum(t['accuracy'] for t in memory_tests) / len(memory_tests)
            }
        }
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        print("Starting benchmark...")
        
        print("Response time benchmark...")
        response_time_results = await self.run_response_time_benchmark()
        
        print("Accuracy benchmark...")
        accuracy_results = await self.run_accuracy_benchmark()
        
        print("Memory efficiency benchmark...")
        memory_results = await self.run_memory_efficiency_benchmark()
        
        response_score = 1.0 / response_time_results['summary']['complex_queries_avg'] if response_time_results['summary']['complex_queries_avg'] > 0 else 0
        accuracy_score = sum(result.score for result in accuracy_results.values()) / len(accuracy_results)
        memory_score = memory_results['summary']['avg_accuracy']
        
        overall_score = (response_score * 0.3 + accuracy_score * 0.5 + memory_score * 0.2)
        
        return {
            'timestamp': time.time(),
            'overall_performance_score': overall_score,
            'response_time_benchmark': response_time_results,
            'accuracy_benchmark': {
                name: {
                    'score': result.score,
                    'passed': result.test_cases_passed,
                    'total': result.total_test_cases
                }
                for name, result in accuracy_results.items()
            },
            'memory_efficiency_benchmark': memory_results,
            'recommendations': self._generate_recommendations(
                response_time_results, accuracy_results, memory_results
            )
        }
    
    def _generate_recommendations(self, response_results, accuracy_results, memory_results) -> List[str]:
        recommendations = []
        
        if response_results['summary']['complex_queries_avg'] > 5.0:
            recommendations.append("Complex query processing slow - optimize decomposition")
        
        accuracy_scores = [result.score for result in accuracy_results.values()]
        if any(score < 0.8 for score in accuracy_scores):
            recommendations.append("Low accuracy metrics - review prompts and data sources")
        
        if memory_results['summary']['avg_retrieval_time'] > 1.0:
            recommendations.append("Memory retrieval slow - optimize indexing")
        
        if not recommendations:
            recommendations.append("Performance within acceptable ranges")
        
        return recommendations

async def main():
    benchmark = PerformanceBenchmark()
    
    try:
        results = await benchmark.run_comprehensive_benchmark()
        
        with open('benchmark_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\n" + "="*50)
        print("BENCHMARK RESULTS")
        print("="*50)
        print(f"Overall Score: {results['overall_performance_score']:.2f}")
        print(f"Complex Queries Avg: {results['response_time_benchmark']['summary']['complex_queries_avg']:.2f}s")
        print(f"Simple Queries Avg: {results['response_time_benchmark']['summary']['simple_queries_avg']:.2f}s")
        print(f"Success Rate: {results['response_time_benchmark']['summary']['overall_success_rate']:.2%}")
        
        print("\nAccuracy:")
        for name, metrics in results['accuracy_benchmark'].items():
            print(f"  {name}: {metrics['score']:.2%} ({metrics['passed']}/{metrics['total']})")
        
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  • {rec}")
        
        print(f"\nResults saved to: benchmark_results.json")
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())