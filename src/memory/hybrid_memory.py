from typing import List, Dict, Any
from .long_term import LongTermMemory
from .short_term import ShortTermMemory
from ..vector_store import VectorStore

class HybridMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.short_term = ShortTermMemory(session_id)
        self.long_term = LongTermMemory(session_id)
        self.vector_memory = VectorStore(f"memory_{session_id}")
        
    def add_conversation(self, user_message: str, assistant_response: str, extracted_facts: List[str]):
        from llama_index.core.llms import ChatMessage
        self.short_term.add_message(ChatMessage(role="user", content=user_message))
        self.short_term.add_message(ChatMessage(role="assistant", content=assistant_response))
        
        for fact in extracted_facts:
            self.long_term.store_fact(fact, confidence=0.8)
        
        conversation_text = f"User: {user_message}\nAssistant: {assistant_response}"
        self.vector_memory.add_document(conversation_text, {
            'type': 'conversation',
            'session_id': self.session_id,
            'user_message': user_message,
            'assistant_response': assistant_response
        })
    
    def retrieve_context(self, query: str, max_facts: int = 5) -> Dict[str, Any]:
        context = {
            'short_term': self.short_term.get_context_string(),
            'long_term_facts': [],
            'semantic_matches': [],
            'retrieval_method': 'hybrid'
        }
        
        facts = self.long_term.get_relevant_facts(query, limit=max_facts)
        context['long_term_facts'] = [f['fact'] for f in facts]
        
        semantic_results = self.vector_memory.search(query, top_k=3)
        context['semantic_matches'] = [
            {
                'content': result['content'][:200] + '...',
                'relevance': result['score'],
                'metadata': result.get('metadata', {})
            }
            for result in semantic_results
        ]
        
        return context
    
    def get_memory_stats(self) -> Dict[str, Any]:
        return {
            'short_term_messages': len(self.short_term.messages),
            'short_term_tokens': self.short_term.current_tokens,
            'long_term_facts': self.long_term.get_fact_count(),
            'vector_documents': len(self.vector_memory.documents),
            'session_id': self.session_id
        }