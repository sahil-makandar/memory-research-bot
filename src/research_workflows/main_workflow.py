from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from typing import Dict, Any
import logging
from .memory_workflow import MemoryWorkflow, MemoryUpdateEvent, MemoryRetrievalEvent
from .query_workflow import QueryWorkflow, QueryProcessingEvent

logger = logging.getLogger('workflow_engine')

class ResearchQueryEvent(Event):
    query: str
    session_id: str

class MainResearchWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        self.memory_workflows = {}
        self.query_workflow = QueryWorkflow()
    
    def _get_memory_workflow(self, session_id: str) -> MemoryWorkflow:
        if session_id not in self.memory_workflows:
            self.memory_workflows[session_id] = MemoryWorkflow(session_id)
        return self.memory_workflows[session_id]
    
    @step
    async def handle_research_query(self, ev: ResearchQueryEvent) -> StopEvent:
        memory_workflow = self._get_memory_workflow(ev.session_id)
        
        # Update memory with user query
        await memory_workflow.run(MemoryUpdateEvent(content=ev.query, message_type="user"))
        
        # Retrieve relevant memory context
        memory_result = await memory_workflow.run(MemoryRetrievalEvent(query=ev.query))
        memory_context = memory_result.result
        
        # Process query with context
        query_result = await self.query_workflow.run(
            QueryProcessingEvent(query=ev.query, context=memory_context)
        )
        
        # Update memory with assistant response
        response = query_result.result['final_answer']
        await memory_workflow.run(MemoryUpdateEvent(content=response, message_type="assistant"))
        
        return StopEvent(result={
            'query': ev.query,
            'response': response,
            'memory_context': memory_context,
            'query_plan': query_result.result['plan']
        })

# Main interface function
async def process_research_query(query: str, session_id: str = "default") -> Dict[str, Any]:
    """Main entry point for processing research queries"""
    workflow = MainResearchWorkflow()
    result = await workflow.run(ResearchQueryEvent(query=query, session_id=session_id))
    return result.result