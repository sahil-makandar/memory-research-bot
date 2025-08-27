"""Pure LLM-driven workflow without hardcoded responses"""
import asyncio
from typing import Dict, Any
from src.memory.short_term import ShortTermMemory
from src.query_planning.complexity_detector import QueryComplexityDetector
from src.llm_client import LLMClient

class ResearchWorkflow:
    def __init__(self):
        self.llm_client = LLMClient()
        self.sessions = {}
    
    async def process_query(self, query: str, session_id: str) -> Dict[str, Any]:
        # Get or create session
        if session_id not in self.sessions:
            self.sessions[session_id] = ShortTermMemory(session_id, token_limit=2000)
        
        memory = self.sessions[session_id]
        
        # Add user message to memory
        from llama_index.core.llms import ChatMessage
        user_msg = ChatMessage(role="user", content=query)
        memory.add_message(user_msg)
        
        # Prepare context for LLM
        context = {
            'session': {'messages': [], 'facts': []},  # Simplified for workflow
            'adobe_data': {},
            'doc_processor': None
        }
        
        # Let LLM process the query completely
        llm_result = await self.llm_client.process_query(query, context)
        response = llm_result['response']
        
        # Add response to memory
        assistant_msg = ChatMessage(role="assistant", content=response)
        memory.add_message(assistant_msg)
        
        # Get complexity from decomposition result
        complexity_data = {
            'complexity_level': 'complex' if llm_result['decomposed'] else 'simple',
            'decomposed': llm_result['decomposed']
        }
        
        return {
            'response': response,
            'complexity': complexity_data,
            'memory_context': memory.get_context_string(),
            'session_id': session_id,
            'sub_queries': llm_result.get('sub_queries', []),
            'decomposed': llm_result['decomposed']
        }

# Global workflow instance
workflow = ResearchWorkflow()

async def process_research_query(query: str, session_id: str = "default"):
    return await workflow.process_query(query, session_id)