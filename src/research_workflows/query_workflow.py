from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from typing import Dict, Any, List
import logging
from ..query_planning import QueryPlanner
from ..tools import (
    create_keyword_extraction_tool,
    create_summarization_tool,
    create_content_analysis_tool,
    create_retrieval_tool
)

logger = logging.getLogger('workflow_engine')

class QueryProcessingEvent(Event):
    query: str
    context: Dict[str, Any] = {}

class QueryWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        self.planner = QueryPlanner()
        self.tools = {
            'keyword_extractor': create_keyword_extraction_tool(),
            'summarizer': create_summarization_tool(),
            'content_analyzer': create_content_analysis_tool(),
            'document_retriever': create_retrieval_tool()
        }
    
    @step
    async def process_query(self, ev: QueryProcessingEvent) -> StopEvent:
        # Create execution plan
        plan = await self.planner.create_execution_plan(ev.query)
        
        results = []
        
        # Execute sub-queries using appropriate tools
        for i in plan['execution_order']:
            sub_query = plan['sub_queries'][i]
            tool_name = self._select_tool_for_query(sub_query)
            
            if tool_name in self.tools:
                try:
                    result = await self.tools[tool_name].acall(sub_query['sub_query'])
                    results.append({
                        'sub_query': sub_query['sub_query'],
                        'result': result,
                        'tool_used': tool_name
                    })
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    results.append({
                        'sub_query': sub_query['sub_query'],
                        'result': f"Error: {str(e)}",
                        'tool_used': tool_name
                    })
        
        return StopEvent(result={
            'plan': plan,
            'results': results,
            'final_answer': self._synthesize_results(results)
        })
    
    def _select_tool_for_query(self, sub_query: Dict[str, Any]) -> str:
        qtype = sub_query.get('type', 'search')
        mapping = {
            'search': 'document_retriever',
            'analysis': 'content_analyzer',
            'summary': 'summarizer'
        }
        return mapping.get(qtype, 'document_retriever')
    
    def _synthesize_results(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No results found"
        
        synthesis = ["Query Results:"]
        for i, result in enumerate(results, 1):
            synthesis.append(f"{i}. {result['sub_query']}")
            synthesis.append(f"   Result: {result['result'][:200]}...")
        
        return "\n".join(synthesis)