from typing import List, Dict, Any
import logging
from ..utils.azure_client import get_azure_llm
from .complexity_detector import QueryComplexityDetector

logger = logging.getLogger('query_planning')

class QueryDecomposer:
    def __init__(self):
        self.llm = get_azure_llm()
        self.complexity_detector = QueryComplexityDetector()
    
    async def decompose_query(self, query: str) -> List[Dict[str, Any]]:
        # First check if decomposition is needed
        complexity_info = self.complexity_detector.detect_complexity(query)
        
        if not complexity_info['requires_decomposition']:
            # Simple query - return as single sub-query
            return [{
                "sub_query": query,
                "type": self.identify_query_type(query),
                "priority": 1,
                "complexity": complexity_info['complexity_level']
            }]
        prompt = f"""Break down this complex query into 3-5 simpler sub-queries.
Return as JSON: [{{"sub_query": "question", "type": "search|analysis|summary", "priority": 1-5}}]

Query: {query}"""
        
        try:
            response = await self.llm.acomplete(prompt)
            import json
            return json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Query decomposition error: {e}")
            return [{"sub_query": query, "type": "search", "priority": 1}]
    
    def identify_query_type(self, query: str) -> str:
        keywords = {
            'search': ['find', 'search', 'locate', 'what is', 'who is'],
            'analysis': ['analyze', 'compare', 'evaluate', 'assess'],
            'summary': ['summarize', 'overview', 'brief', 'summary']
        }
        
        query_lower = query.lower()
        for qtype, words in keywords.items():
            if any(word in query_lower for word in words):
                return qtype
        return 'search'