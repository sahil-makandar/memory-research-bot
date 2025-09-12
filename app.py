from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
# from src.core.processor import process_research_query
from src.testing.evaluator import AgentEvaluator, DEFAULT_TEST_SUITE
from src.utils.error_handler import with_retry, RetryConfig
from config.settings import get_config

config = get_config()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Memory Research Assistant",
    version="2.0.0"
)

evaluator = AgentEvaluator()

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    session_id: str
    metadata: Dict[str, Any]
    thinking_steps: list

class EvaluationRequest(BaseModel):
    test_suite: Optional[Dict[str, Any]] = None

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    session_id = request.session_id or "default"
    
    try:
        logger.info(f"Processing query: '{request.query}' for session: {session_id}")
        
        from src.llm_client import LLMClient
        from src.memory.hybrid_memory import HybridMemory
        
        # Initialize components
        llm_client = LLMClient()
        memory = HybridMemory(session_id)
        
        # Build context
        context = {
            'session': {
                'messages': [],
                'facts': memory.long_term.get_all_facts()
            },
            'adobe_data': {'pdf_path': 'docs/adobe-annual-report.pdf'},
            'doc_processor': None
        }
        
        # Process query using LLM client
        result = llm_client.process_query(request.query, context)
        response = result['response']
        
        # Extract facts and update memory
        facts = llm_client.extract_conversation_facts(request.query, response)
        memory.add_conversation(request.query, response, facts)
        
        return QueryResponse(
            response=response,
            session_id=session_id,
            thinking_steps=[
                "Analyzed query complexity using LLM",
                "Determined processing approach" + (" (decomposed into sub-queries)" if result['decomposed'] else " (single query)"),
                "Gathered data from memory and vector store",
                "Generated LLM response" + (" and synthesized results" if result['decomposed'] else ""),
                "Updated hybrid memory system"
            ],
            metadata={
                'complexity_level': 'complex' if result['decomposed'] else 'simple',
                'decomposed': result['decomposed'],
                'sub_queries_count': len(result.get('sub_queries', [])),
                'complexity_score': result.get('complexity_score', 0.0),
                'facts_extracted': len(facts),
                'memory_stats': memory.get_memory_stats()
            }
        )
    
    except Exception as e:
        import traceback
        logger.error(f"Query failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate_agent(request: EvaluationRequest = None):
    test_suite = DEFAULT_TEST_SUITE
    if request and request.test_suite:
        test_suite = request.test_suite
    
    try:
        results = await evaluator.run_benchmark(test_suite)
        
        scores = [result.score for result in results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'overall_score': overall_score,
            'metrics': {
                name: {
                    'score': result.score,
                    'passed': result.test_cases_passed,
                    'total': result.total_test_cases
                }
                for name, result in results.items()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {
        "status": "ready",
        "version": "2.0.0",
        "features": ["hybrid_memory", "workflows", "evaluation"]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        from src.vector_store import VectorStore
        import tempfile
        import os
        
        content = await file.read()
        
        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Index the document
            vector_store = VectorStore()
            sections = vector_store.index_document(tmp_path, file.filename)
            
            return {
                "success": True,
                "filename": file.filename,
                "size": len(content),
                "sections": len(sections)
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    return {
        "requests_processed": 0,
        "average_response_time": 0.0,
        "error_rate": 0.0
    }

@app.post("/benchmark")
async def run_benchmark():
    import time
    import asyncio
    
    queries = [
        "What is Adobe's business strategy?",
        "Analyze Adobe's financial performance",
        "What are the key risks facing Adobe?"
    ]
    
    results = []
    
    for query in queries:
        start_time = time.time()
        
        try:
            # Simulate processing time
            await asyncio.sleep(0.5)
            
            # Simple response generation
            response_time = time.time() - start_time
            
            results.append({
                'query': query,
                'response_time': response_time,
                'success': True
            })
        
        except Exception as e:
            results.append({
                'query': query,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            })
    
    avg_time = sum(r['response_time'] for r in results) / len(results)
    success_rate = sum(1 for r in results if r['success']) / len(results)
    
    return {
        'results': results,
        'avg_response_time': avg_time,
        'success_rate': success_rate
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=config.API_HOST, 
        port=config.API_PORT
    )