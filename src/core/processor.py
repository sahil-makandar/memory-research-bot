from typing import Dict, Any, List
from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step
from ..memory.hybrid_memory import HybridMemory
from ..llm_client import LLMClient
import os
from pathlib import Path

class QueryEvent(Event):
    query: str
    session_id: str

class ComplexityAnalyzedEvent(Event):
    query: str
    session_id: str
    is_complex: bool
    reasoning: str

class SubQueriesGeneratedEvent(Event):
    original_query: str
    sub_queries: List[str]
    session_id: str

class DataGatheredEvent(Event):
    query: str
    session_id: str
    gathered_data: Dict[str, Any]
    sub_results: List[Dict] = None

class ResponseGeneratedEvent(Event):
    query: str
    session_id: str
    response: str
    metadata: Dict[str, Any]

class QueryProcessor(Workflow):
    def __init__(self):
        super().__init__()
        self.llm_client = LLMClient()
        self.memory_sessions = {}
        self.docs_path = Path(__file__).parent.parent.parent / "docs"
    
    def _get_document_context(self):
        return {"pdf_path": str(self.docs_path / "adobe-annual-report.pdf")}
    
    @step
    async def analyze_complexity(self, ev: StartEvent) -> ComplexityAnalyzedEvent:
        query = ev.get("query")
        session_id = ev.get("session_id", "default")
        
        if session_id not in self.memory_sessions:
            self.memory_sessions[session_id] = HybridMemory(session_id)
        
        complexity_result = await self.llm_client._llm_decide_decomposition(query, {})
        
        return ComplexityAnalyzedEvent(
            query=query,
            session_id=session_id,
            is_complex=complexity_result["needs_decomposition"],
            reasoning=complexity_result["reasoning"]
        )
    
    @step
    async def generate_sub_queries(self, ev: ComplexityAnalyzedEvent) -> SubQueriesGeneratedEvent | DataGatheredEvent:
        if ev.is_complex:
            sub_queries = await self.llm_client._llm_decompose_query(ev.query, {})
            
            return SubQueriesGeneratedEvent(
                original_query=ev.query,
                sub_queries=sub_queries,
                session_id=ev.session_id
            )
        else:
            memory = self.memory_sessions[ev.session_id]
            context = {
                'session': {
                    'messages': [],
                    'facts': memory.long_term.get_all_facts()
                },
                'adobe_data': self._get_document_context(),
                'doc_processor': None
            }
            
            data_sources = await self.llm_client._llm_decide_data_sources(ev.query, context)
            gathered_data = {}
            
            for source in data_sources:
                if source == "adobe_data":
                    gathered_data["adobe_data"] = await self.llm_client._search_adobe_data(ev.query, context)
                elif source == "memory":
                    memory_context = memory.retrieve_context(ev.query)
                    gathered_data["memory"] = memory_context
            
            return DataGatheredEvent(
                query=ev.query,
                session_id=ev.session_id,
                gathered_data=gathered_data
            )
    
    @step
    async def process_sub_queries(self, ev: SubQueriesGeneratedEvent) -> DataGatheredEvent:
        memory = self.memory_sessions[ev.session_id]
        sub_results = []
        
        for sub_query in ev.sub_queries:
            context = {
                'session': {
                    'messages': [],
                    'facts': memory.long_term.get_all_facts()
                },
                'adobe_data': self._get_document_context(),
                'doc_processor': None
            }
            
            data_sources = await self.llm_client._llm_decide_data_sources(sub_query, context)
            sub_data = {}
            
            for source in data_sources:
                if source == "adobe_data":
                    sub_data["adobe_data"] = await self.llm_client._search_adobe_data(sub_query, context)
                elif source == "memory":
                    memory_context = memory.retrieve_context(sub_query)
                    sub_data["memory"] = memory_context
            
            sub_response = await self.llm_client._llm_generate_response(sub_query, sub_data, context)
            
            sub_results.append({
                'query': sub_query,
                'result': sub_response,
                'data_sources': list(sub_data.keys())
            })
        
        return DataGatheredEvent(
            query=ev.original_query,
            session_id=ev.session_id,
            gathered_data={'sub_query_results': sub_results},
            sub_results=sub_results
        )
    
    @step
    async def generate_response(self, ev: DataGatheredEvent) -> ResponseGeneratedEvent:
        memory = self.memory_sessions[ev.session_id]
        
        if ev.sub_results:
            response = await self.llm_client._llm_synthesize_results(
                ev.query, ev.sub_results, {}
            )
            complexity_level = 'complex'
        else:
            context = {
                'session': {
                    'messages': [],
                    'facts': memory.long_term.get_all_facts()
                },
                'adobe_data': self._get_document_context()
            }
            response = await self.llm_client._llm_generate_response(
                ev.query, ev.gathered_data, context
            )
            complexity_level = 'simple'
        
        extracted_facts = await self.llm_client.extract_conversation_facts(ev.query, response)
        
        memory.add_conversation(ev.query, response, extracted_facts)
        
        metadata = {
            'complexity_level': complexity_level,
            'decomposed': bool(ev.sub_results),
            'sub_queries_count': len(ev.sub_results) if ev.sub_results else 0,
            'facts_extracted': len(extracted_facts),
            'memory_stats': memory.get_memory_stats()
        }
        
        return ResponseGeneratedEvent(
            query=ev.query,
            session_id=ev.session_id,
            response=response,
            metadata=metadata
        )
    
    @step
    async def finalize_response(self, ev: ResponseGeneratedEvent) -> StopEvent:
        return StopEvent(result={
            'response': ev.response,
            'session_id': ev.session_id,
            'metadata': ev.metadata,
            'thinking_steps': [
                "Analyzed query complexity",
                "Determined processing approach",
                "Gathered relevant data",
                "Generated response",
                "Updated memory"
            ]
        })

processor = QueryProcessor()

async def process_research_query(query: str, session_id: str = "default") -> Dict[str, Any]:
    result = await processor.run(query=query, session_id=session_id)
    return result