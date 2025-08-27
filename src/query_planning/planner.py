from typing import List, Dict, Any
import logging
from .decomposer import QueryDecomposer

logger = logging.getLogger('query_planning')

class QueryPlanner:
    def __init__(self):
        self.decomposer = QueryDecomposer()
    
    async def create_execution_plan(self, query: str) -> Dict[str, Any]:
        sub_queries = await self.decomposer.decompose_query(query)
        
        plan = {
            'original_query': query,
            'sub_queries': sub_queries,
            'execution_order': self._determine_execution_order(sub_queries),
            'tools_needed': self._identify_required_tools(sub_queries)
        }
        
        logger.info(f"Created execution plan with {len(sub_queries)} sub-queries")
        return plan
    
    def _determine_execution_order(self, sub_queries: List[Dict[str, Any]]) -> List[int]:
        # Sort by priority (higher first)
        sorted_queries = sorted(enumerate(sub_queries), 
                              key=lambda x: x[1].get('priority', 1), 
                              reverse=True)
        return [idx for idx, _ in sorted_queries]
    
    def _identify_required_tools(self, sub_queries: List[Dict[str, Any]]) -> List[str]:
        tools = set()
        for sq in sub_queries:
            qtype = sq.get('type', 'search')
            if qtype == 'search':
                tools.add('document_retriever')
            elif qtype == 'analysis':
                tools.add('content_analyzer')
            elif qtype == 'summary':
                tools.add('summarizer')
        
        tools.add('keyword_extractor')  # Always useful
        return list(tools)