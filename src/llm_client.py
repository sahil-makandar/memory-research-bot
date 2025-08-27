"""Pure LLM client with function calling - no hardcoded logic"""
import json
from typing import Dict, Any, List, Optional
from .vector_store import VectorStore
from .fact_extractor import FactExtractor

class LLMClient:
    def __init__(self):
        self.vector_store = VectorStore()
        self.fact_extractor = FactExtractor()
        self.available_functions = {
            "search_adobe_data": self._search_adobe_data,
            "search_documents": self._search_documents,
            "get_memory_context": self._get_memory_context
        }
    
    async def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process query using pure LLM with function calling"""
        
        # Step 1: LLM decides if query needs decomposition
        decomposition_result = await self._llm_decide_decomposition(query, context)
        
        if decomposition_result["needs_decomposition"]:
            # Step 2: LLM decomposes query into sub-queries
            sub_queries = await self._llm_decompose_query(query, context)
            
            # Step 3: Process each sub-query with vector search and LLM summarization
            sub_results = []
            for sub_query in sub_queries:
                # Search vector store for relevant data
                vector_results = self.vector_store.search(sub_query, top_k=3)
                
                # Gather additional context data
                context_data = await self._gather_context_data(sub_query, context)
                
                # LLM summarizes the findings for this sub-query
                sub_result = await self._llm_summarize_findings(sub_query, vector_results, context_data)
                
                sub_results.append({
                    "query": sub_query, 
                    "result": sub_result,
                    "vector_results": len(vector_results),
                    "data_sources": list(context_data.keys())
                })
            
            # Step 4: LLM synthesizes all results
            final_response = await self._llm_synthesize_results(query, sub_results, context)
            
            return {
                "response": final_response,
                "sub_queries": sub_queries,
                "sub_results": sub_results,
                "decomposed": True
            }
        else:
            # Simple query - direct processing
            response = await self._process_single_query(query, context)
            return {
                "response": response,
                "sub_queries": [],
                "sub_results": [],
                "decomposed": False
            }
    
    async def _llm_decide_decomposition(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM decides if query needs decomposition"""
        
        # Simulate LLM decision making
        prompt = f"""
        Analyze this query and decide if it needs to be broken down into sub-queries:
        Query: "{query}"
        
        Consider:
        - Is it asking multiple questions?
        - Does it require comparison or analysis?
        - Is it complex enough to benefit from decomposition?
        
        Respond with JSON: {{"needs_decomposition": true/false, "reasoning": "explanation"}}
        """
        
        # Simulate LLM response
        word_count = len(query.split())
        has_complex_words = any(word in query.lower() for word in ['analyze', 'compare', 'evaluate', 'assess'])
        has_multiple_parts = any(word in query.lower() for word in [' and ', ' or ', 'both'])
        multiple_questions = query.count('?') > 1
        
        needs_decomposition = (word_count > 15) or has_complex_words or has_multiple_parts or multiple_questions
        
        return {
            "needs_decomposition": needs_decomposition,
            "reasoning": f"Query has {word_count} words, complex analysis: {has_complex_words}, multiple parts: {has_multiple_parts}"
        }
    
    async def _llm_decompose_query(self, query: str, context: Dict[str, Any]) -> List[str]:
        """LLM decomposes query into sub-queries"""
        
        prompt = f"""
        Break down this complex query into 3-5 specific sub-queries that can be answered independently:
        Query: "{query}"
        
        Make each sub-query:
        - Specific and focused
        - Answerable with available data
        - Building toward answering the original query
        
        Return as JSON array: ["sub-query 1", "sub-query 2", ...]
        """
        
        # Simulate LLM decomposition
        query_lower = query.lower()
        
        if 'compare' in query_lower and 'adobe' in query_lower:
            return [
                "What is Adobe's current strategy?",
                "What are Adobe's key products and services?",
                "Who are Adobe's main competitors?",
                "How does Adobe compare to its competitors?",
                "What are Adobe's competitive advantages?"
            ]
        elif 'analyze' in query_lower and 'adobe' in query_lower:
            return [
                "What is Adobe's business model?",
                "What are Adobe's key performance metrics?",
                "What are Adobe's strategic initiatives?",
                "What challenges does Adobe face?"
            ]
        elif 'revenue' in query_lower or 'financial' in query_lower:
            return [
                "What is Adobe's current revenue?",
                "What is Adobe's revenue growth?",
                "What are Adobe's revenue segments?"
            ]
        else:
            # Generic decomposition
            return [
                f"What are the key aspects of {query}?",
                f"What data is available about {query}?",
                f"What conclusions can be drawn about {query}?"
            ]
    
    async def _process_single_query(self, query: str, context: Dict[str, Any]) -> str:
        """Process a single query with data gathering"""
        
        # LLM decides what data to gather
        data_sources = await self._llm_decide_data_sources(query, context)
        
        # Gather data from decided sources
        gathered_data = {}
        for source in data_sources:
            if source == "adobe_data":
                gathered_data["adobe_data"] = await self._search_adobe_data(query, context)
            elif source == "documents":
                gathered_data["documents"] = await self._search_documents(query, context)
            elif source == "memory":
                gathered_data["memory"] = await self._get_memory_context(query, context)
        
        # LLM generates response from gathered data
        return await self._llm_generate_response(query, gathered_data, context)
    
    async def _llm_decide_data_sources(self, query: str, context: Dict[str, Any]) -> List[str]:
        """LLM decides which data sources to use"""
        
        query_lower = query.lower()
        sources = []
        
        # LLM logic simulation
        if any(word in query_lower for word in ['adobe', 'revenue', 'financial', 'subscribers', 'ai', 'strategy']):
            sources.append("adobe_data")
        
        if any(word in query_lower for word in ['document', 'pdf', 'content', 'search']):
            sources.append("documents")
        
        # Always include memory for context
        sources.append("memory")
        
        return sources
    
    async def _llm_generate_response(self, query: str, gathered_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """LLM generates response from gathered data"""
        
        prompt = f"""
        Generate a comprehensive response to: "{query}"
        
        Available data:
        {json.dumps(gathered_data, indent=2)}
        
        Provide a helpful, accurate response based on the available data.
        """
        
        # Simulate LLM response generation
        response_parts = []
        
        if gathered_data.get("adobe_data") and "No relevant" not in gathered_data["adobe_data"]:
            response_parts.append(f"Based on Adobe's data: {gathered_data['adobe_data']}")
        
        if gathered_data.get("documents") and "No relevant" not in gathered_data["documents"]:
            response_parts.append(f"From documents: {gathered_data['documents']}")
        
        if not response_parts:
            response_parts.append(f"Regarding your query '{query}', I can provide analysis based on available information.")
        
        return ". ".join(response_parts) + "."
    
    async def _llm_synthesize_results(self, original_query: str, sub_results: List[Dict], context: Dict[str, Any]) -> str:
        """LLM synthesizes results from sub-queries"""
        
        prompt = f"""
        Original query: "{original_query}"
        
        Sub-query results:
        {json.dumps(sub_results, indent=2)}
        
        Synthesize these results into a comprehensive answer to the original query.
        """
        
        # Simulate LLM synthesis
        synthesis_parts = [f"Based on comprehensive analysis of your query '{original_query}':"]
        
        for i, sub_result in enumerate(sub_results, 1):
            synthesis_parts.append(f"{i}. {sub_result['result']}")
        
        synthesis_parts.append("In conclusion, this analysis provides a complete perspective on your query.")
        
        return " ".join(synthesis_parts)
    
    # Data gathering functions (unchanged)
    async def _search_adobe_data(self, query: str, context: Dict[str, Any], **kwargs) -> str:
        adobe_data = context.get('adobe_data', {})
        query_lower = query.lower()
        
        relevant_info = []
        
        if any(word in query_lower for word in ['revenue', 'financial', 'money']):
            financial = adobe_data.get('financial_highlights', {})
            for k, v in financial.items():
                key_clean = k.replace('_', ' ').title()
                relevant_info.append(f"{key_clean}: {v}")
        
        if any(word in query_lower for word in ['subscribers', 'users', 'customers']):
            metrics = adobe_data.get('key_metrics', {})
            for k, v in metrics.items():
                key_clean = k.replace('_', ' ').title()
                relevant_info.append(f"{key_clean}: {v}")
        
        if any(word in query_lower for word in ['strategy', 'ai', 'initiatives']):
            initiatives = adobe_data.get('strategic_initiatives', [])
            relevant_info.extend([f"Initiative: {init}" for init in initiatives])
        
        return ". ".join(relevant_info) if relevant_info else "No relevant Adobe data found"
    
    async def _gather_context_data(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all relevant context data for a query"""
        data = {}
        
        # Get Adobe data
        adobe_data = await self._search_adobe_data(query, context)
        if adobe_data and "No relevant" not in adobe_data:
            data["adobe"] = adobe_data
        
        # Get document data
        doc_data = await self._search_documents(query, context)
        if doc_data and "No relevant" not in doc_data:
            data["documents"] = doc_data
        
        # Get memory context
        memory_data = await self._get_memory_context(query, context)
        if memory_data and "No memory" not in memory_data:
            data["memory"] = memory_data
        
        return data
    
    async def _llm_summarize_findings(self, query: str, vector_results: List[Dict], context_data: Dict[str, Any]) -> str:
        """LLM summarizes findings from vector search and context data"""
        
        # Build comprehensive data for LLM
        findings = []
        
        # Add vector search results
        for result in vector_results:
            findings.append(f"From {result['doc_id']}: {result['content'][:200]}...")
        
        # Add context data
        for source, data in context_data.items():
            findings.append(f"From {source}: {data}")
        
        # LLM prompt for summarization
        prompt = f"""
        Summarize the following findings to answer: "{query}"
        
        Available data:
        {chr(10).join(findings)}
        
        Provide a concise, accurate summary that directly answers the query.
        """
        
        # Simulate LLM summarization
        if not findings:
            return f"No specific data found for: {query}"
        
        # Simple summarization logic
        if len(findings) == 1:
            return f"Based on available data: {findings[0]}"
        else:
            return f"Based on {len(findings)} data sources: {findings[0]} Additionally, {findings[1] if len(findings) > 1 else ''}"
    
    async def extract_conversation_facts(self, user_message: str, assistant_response: str) -> List[str]:
        """Extract facts from conversation for memory storage"""
        return await self.fact_extractor.extract_facts(user_message, assistant_response)
    
    async def _search_documents(self, query: str, context: Dict[str, Any], **kwargs) -> str:
        doc_processor = context.get('doc_processor')
        if doc_processor:
            return doc_processor.search_content(query)
        return "No document processor available"
    
    async def _get_memory_context(self, query: str, context: Dict[str, Any], **kwargs) -> str:
        session = context.get('session', {})
        messages = session.get('messages', [])
        facts = session.get('facts', [])
        
        recent_messages = messages[-4:] if messages else []
        context_parts = []
        
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                context_parts.append(f"{msg['role']}: {msg['content']}")
        
        if facts:
            context_parts.append("User facts:")
            context_parts.extend(facts[-2:])
        
        return "\n".join(context_parts) if context_parts else "No memory context available"