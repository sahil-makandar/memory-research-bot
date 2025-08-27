from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from src.llm_client import LLMClient
from src.document_processor import DocumentProcessor

app = FastAPI(title="Memory-Persistent Research Assistant")

# Initialize components
llm_client = LLMClient()
doc_processor = DocumentProcessor()
sessions = {}

# Load Adobe data
try:
    with open("data/adobe_report_data.json", "r") as f:
        adobe_data = json.load(f)
except:
    adobe_data = {}

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    session_id: str
    metadata: Dict[str, Any]
    thinking_steps: list

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index document"""
    content = await file.read()
    result = doc_processor.process_pdf(content, file.filename)
    return result

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    session_id = request.session_id or "default"
    
    # Initialize session
    if session_id not in sessions:
        sessions[session_id] = {'messages': [], 'facts': []}
    
    session = sessions[session_id]
    thinking_steps = []
    
    # Step 1: LLM analyzes query and decides functions to call
    thinking_steps.append("LLM analyzing query and determining required data sources")
    
    # Step 2: Prepare context for LLM
    thinking_steps.append("Preparing context with session data and available resources")
    context = {
        'session': session,
        'adobe_data': adobe_data,
        'doc_processor': doc_processor
    }
    
    # Step 3: LLM processes query (with potential decomposition)
    thinking_steps.append("LLM analyzing query complexity and deciding processing approach")
    llm_result = await llm_client.process_query(request.query, context)
    
    # Step 4: Handle decomposed vs simple queries
    if llm_result['decomposed']:
        thinking_steps.append(f"LLM decomposed query into {len(llm_result['sub_queries'])} sub-queries")
        thinking_steps.append("Processing each sub-query with data gathering")
        thinking_steps.append("LLM synthesizing results from all sub-queries")
    else:
        thinking_steps.append("LLM processing as simple query with direct data gathering")
    
    response = llm_result['response']
    sub_queries = llm_result.get('sub_queries', [])
    sub_results = llm_result.get('sub_results', [])
    
    # Step 5: Extract facts using LLM
    thinking_steps.append("LLM extracting facts from conversation for memory storage")
    extracted_facts = await llm_client.extract_conversation_facts(request.query, response)
    
    # Step 6: Update session memory
    thinking_steps.append("Updating session memory with conversation and facts")
    session['messages'].append({'role': 'user', 'content': request.query})
    session['messages'].append({'role': 'assistant', 'content': response})
    
    # Store extracted facts
    session['facts'].extend(extracted_facts)
    
    # Determine complexity from decomposition
    complexity_level = 'complex' if llm_result['decomposed'] else 'simple'
    
    return QueryResponse(
        response=response,
        session_id=session_id,
        thinking_steps=thinking_steps,
        metadata={
            'complexity_level': complexity_level,
            'word_count': len(request.query.split()),
            'decomposed': llm_result['decomposed'],
            'sub_queries_count': len(sub_queries),
            'session_messages': len(session['messages']),
            'session_facts': len(session['facts']),
            'facts_extracted': len(extracted_facts),
            'llm_generated': True,
            'vector_search_used': llm_result['decomposed'],
            'sub_queries': sub_queries
        }
    )

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        'session_id': session_id,
        'message_count': len(session['messages']),
        'facts_count': len(session['facts']),
        'facts': session['facts']
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/health")
async def health():
    return {
        "status": "ready", 
        "features": ["llm_function_calling", "memory_persistence", "document_indexing"],
        "llm_functions": list(llm_client.available_functions.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)