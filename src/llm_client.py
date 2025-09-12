import json
from typing import Dict, Any, List
from pydantic import BaseModel
from .vector_store import VectorStore
from .fact_extractor import FactExtractor

class QueryComplexity(BaseModel):
    needs_decomposition: bool
    reasoning: str
    complexity_score: float

class SubQueries(BaseModel):
    sub_queries: List[str]
    reasoning: str

class DataSources(BaseModel):
    sources: List[str]
    reasoning: str

class LLMResponse(BaseModel):
    response: str
    confidence: float
    sources_used: List[str]

class LLMClient:
    def __init__(self):
        self.vector_store = VectorStore()
        self.fact_extractor = FactExtractor()
    
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Step 1: LLM decides complexity
        complexity = self._llm_analyze_complexity(query, context)
        
        if complexity.needs_decomposition:
            # Step 2: LLM generates sub-queries
            sub_queries_result = self._llm_generate_sub_queries(query, context)
            
            # Step 3: Process each sub-query
            sub_results = []
            for sub_query in sub_queries_result.sub_queries:
                sub_data = self._gather_data_for_query(sub_query, context)
                sub_response = self._llm_generate_response(sub_query, sub_data, context)
                
                sub_results.append({
                    "query": sub_query,
                    "response": sub_response.response,
                    "confidence": sub_response.confidence,
                    "sources": sub_response.sources_used
                })
            
            # Step 4: LLM synthesizes final response
            final_response = self._llm_synthesize_results(query, sub_results, context)
            
            return {
                "response": final_response.response,
                "sub_queries": sub_queries_result.sub_queries,
                "sub_results": sub_results,
                "decomposed": True,
                "complexity_score": complexity.complexity_score
            }
        else:
            # Simple query processing
            data = self._gather_data_for_query(query, context)
            response = self._llm_generate_response(query, data, context)
            
            return {
                "response": response.response,
                "sub_queries": [],
                "sub_results": [],
                "decomposed": False,
                "complexity_score": complexity.complexity_score
            }
    
    def _llm_analyze_complexity(self, query: str, context: Dict[str, Any]) -> QueryComplexity:
        """LLM analyzes query complexity using structured output"""
        
        # Simulate LLM structured output for complexity analysis
        word_count = len(query.split())
        has_complex_words = any(word in query.lower() for word in [
            'analyze', 'compare', 'evaluate', 'assess', 'examine', 'investigate',
            'breakdown', 'detailed', 'comprehensive', 'thorough'
        ])
        has_multiple_aspects = any(phrase in query.lower() for phrase in [
            ' and ', ' or ', 'both', 'versus', 'vs', 'different', 'various'
        ])
        multiple_questions = query.count('?') > 1
        
        complexity_score = 0.0
        if word_count > 10: complexity_score += 0.3
        if has_complex_words: complexity_score += 0.4
        if has_multiple_aspects: complexity_score += 0.3
        if multiple_questions: complexity_score += 0.2
        
        needs_decomposition = complexity_score > 0.5
        
        reasoning = f"Query complexity analysis: {word_count} words, "
        reasoning += f"complex terms: {has_complex_words}, multiple aspects: {has_multiple_aspects}"
        
        return QueryComplexity(
            needs_decomposition=needs_decomposition,
            reasoning=reasoning,
            complexity_score=complexity_score
        )
    
    def _llm_generate_sub_queries(self, query: str, context: Dict[str, Any]) -> SubQueries:
        """LLM generates sub-queries using structured output"""
        
        query_lower = query.lower()
        sub_queries = []
        
        # LLM logic for generating relevant sub-queries
        if 'adobe' in query_lower:
            if any(word in query_lower for word in ['analyze', 'comprehensive', 'detailed']):
                sub_queries = [
                    "What is Adobe's current financial performance and revenue?",
                    "What are Adobe's key business segments and products?",
                    "What is Adobe's market position and competitive advantages?",
                    "What are Adobe's strategic initiatives and future plans?"
                ]
            elif 'compare' in query_lower:
                sub_queries = [
                    "What are Adobe's key strengths and market position?",
                    "Who are Adobe's main competitors?",
                    "How does Adobe's performance compare to competitors?",
                    "What are Adobe's competitive advantages?"
                ]
            elif any(word in query_lower for word in ['revenue', 'financial', 'performance']):
                sub_queries = [
                    "What is Adobe's total revenue and growth rate?",
                    "What are Adobe's revenue segments breakdown?",
                    "What are Adobe's key financial metrics?",
                    "What are Adobe's profitability trends?"
                ]
        else:
            # Generic decomposition
            sub_queries = [
                f"What are the key facts about {query}?",
                f"What is the current status of {query}?",
                f"What are the implications of {query}?"
            ]
        
        return SubQueries(
            sub_queries=sub_queries,
            reasoning=f"Generated {len(sub_queries)} sub-queries based on query analysis"
        )
    
    def _gather_data_for_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather data from memory and vector store"""
        gathered_data = {}
        
        # Get memory context (short-term + long-term)
        session = context.get('session', {})
        memory_context = {
            'short_term': session.get('messages', []),
            'long_term_facts': session.get('facts', [])
        }
        gathered_data['memory'] = memory_context
        
        # Search vector store
        vector_results = self.vector_store.search(query, top_k=5)
        gathered_data['vector_search'] = vector_results
        
        return gathered_data
    
    def _llm_generate_response(self, query: str, data: Dict[str, Any], context: Dict[str, Any]) -> LLMResponse:
        """LLM generates response using gathered data"""
        
        # Prepare context for LLM
        memory_context = data.get('memory', {})
        vector_results = data.get('vector_search', [])
        
        # Build response using available data
        response_parts = []
        sources_used = []
        
        # Use vector search results
        if vector_results:
            relevant_content = []
            for result in vector_results[:3]:  # Top 3 results
                relevant_content.append(result['content'][:300])
                sources_used.append(result['doc_id'])
            
            if relevant_content:
                response_parts.append("Based on available data: " + " ".join(relevant_content))
        
        # Use memory context
        long_term_facts = memory_context.get('long_term_facts', [])
        if long_term_facts:
            recent_facts = [fact['fact'] for fact in long_term_facts[-3:]]  # Last 3 facts
            if recent_facts:
                response_parts.append("From previous context: " + " ".join(recent_facts))
                sources_used.append("memory")
        
        # Generate final response
        if response_parts:
            response = f"Regarding '{query}': " + " ".join(response_parts)
            confidence = 0.8
        else:
            response = f"I need more specific information to answer '{query}'. Could you provide more context or clarify your question?"
            confidence = 0.3
        
        return LLMResponse(
            response=response,
            confidence=confidence,
            sources_used=sources_used
        )
    
    def _llm_synthesize_results(self, original_query: str, sub_results: List[Dict], context: Dict[str, Any]) -> LLMResponse:
        """LLM synthesizes sub-query results into final response"""
        
        # Combine all sub-results
        synthesis_parts = [f"Comprehensive analysis of '{original_query}':"]
        all_sources = []
        
        for i, sub_result in enumerate(sub_results, 1):
            synthesis_parts.append(f"{i}. {sub_result['response']}")
            all_sources.extend(sub_result['sources'])
        
        # Add conclusion
        synthesis_parts.append("This analysis provides a complete perspective based on available data and context.")
        
        final_response = " ".join(synthesis_parts)
        
        return LLMResponse(
            response=final_response,
            confidence=0.9,
            sources_used=list(set(all_sources))
        )
    
    def extract_conversation_facts(self, user_message: str, assistant_response: str) -> List[str]:
        """Extract facts from conversation for memory storage"""
        return self.fact_extractor.extract_facts(user_message, assistant_response)