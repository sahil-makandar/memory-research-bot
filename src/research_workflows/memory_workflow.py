from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from llama_index.core.llms import ChatMessage
from typing import Dict, Any, List
import logging
from ..memory import ShortTermMemory, LongTermMemory, MemoryBlockManager

logger = logging.getLogger('workflow_engine')

class MemoryUpdateEvent(Event):
    content: str
    message_type: str = "user"

class MemoryRetrievalEvent(Event):
    query: str

class MemoryWorkflow(Workflow):
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self.short_term = ShortTermMemory(session_id)
        self.long_term = LongTermMemory(session_id)
        self.memory_blocks = MemoryBlockManager()
    
    @step
    async def handle_memory_update(self, ev: MemoryUpdateEvent) -> StopEvent:
        # Add to short-term memory
        message = ChatMessage(role=ev.message_type, content=ev.content)
        self.short_term.add_message(message)
        
        # Extract facts for long-term if significant content
        if len(ev.content) > 100:
            facts = await self.long_term.extract_facts(ev.content)
            if facts:
                self.long_term.store_facts(facts)
        
        logger.info(f"Updated memory with {len(ev.content)} characters")
        return StopEvent(result={"status": "memory_updated"})
    
    @step
    async def handle_memory_retrieval(self, ev: MemoryRetrievalEvent) -> StopEvent:
        # Get short-term context
        context = self.short_term.get_context_string()
        
        # Get relevant long-term facts
        facts = self.long_term.retrieve_relevant_facts(ev.query)
        
        # Combine into memory context
        memory_context = {
            "short_term_context": context,
            "relevant_facts": facts,
            "memory_summary": self.long_term.get_memory_summary()
        }
        
        return StopEvent(result=memory_context)