# Memory Research Assistant

Advanced LLM-powered research assistant with hybrid memory system, intelligent query processing, and comprehensive evaluation framework.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python app.py

# Start UI (new terminal)
streamlit run ui.py
```

Access the application at `http://localhost:8501`

## 🏗️ Architecture

### Core Components

- **LLM-Driven Query Processing**: Intelligent complexity analysis and query decomposition
- **Hybrid Memory System**: Three-tier memory combining short-term, long-term, and vector search
- **Structured Output Generation**: Pydantic models for consistent LLM responses
- **Vector Store Integration**: Semantic search across indexed documents
- **Comprehensive Evaluation**: Automated testing and benchmarking framework

### Query Processing Pipeline

1. **Complexity Analysis**: LLM analyzes query complexity using structured output
2. **Query Decomposition**: Complex queries are broken into focused sub-queries
3. **Data Gathering**: Retrieves context from memory and searches vector store
4. **Response Generation**: LLM synthesizes responses using gathered data
5. **Memory Update**: Extracts and stores conversation facts for future context

## 🧠 Memory System

### Three-Tier Architecture

- **Short-Term Memory**: FIFO conversation buffer (40k tokens)
  - Maintains recent conversation context
  - Automatic token management with oldest message eviction
  - Persistent storage with SQLite

- **Long-Term Memory**: Fact extraction with confidence scores
  - Extracts key facts from conversations
  - Confidence-based fact scoring
  - Searchable fact database

- **Vector Memory**: Semantic similarity search
  - Indexes conversations and documents
  - Semantic search for context retrieval
  - Hybrid retrieval combining facts and similarity

### Memory Integration

```python
# Memory retrieval combines all three tiers
context = memory.retrieve_context(query)
# Returns: {
#   'short_term': recent_messages,
#   'long_term_facts': relevant_facts,
#   'semantic_matches': similar_content,
#   'retrieval_method': 'hybrid'
# }
```

## 🤖 LLM Integration

### Structured Output Models

```python
class QueryComplexity(BaseModel):
    needs_decomposition: bool
    reasoning: str
    complexity_score: float

class LLMResponse(BaseModel):
    response: str
    confidence: float
    sources_used: List[str]
```

### Query Processing Flow

- **Simple Queries**: Direct processing with memory context
- **Complex Queries**: Decomposition → Sub-query processing → Synthesis
- **Data Sources**: Memory + Vector store + Indexed documents
- **Response Quality**: Confidence scoring and source attribution

## 📊 Features

### Intelligence Features
- **Adaptive Complexity Analysis**: LLM determines optimal processing approach
- **Dynamic Sub-Query Generation**: Context-aware query decomposition
- **Multi-Source Data Fusion**: Combines memory, documents, and vector search
- **Confidence-Based Responses**: Quality scoring for all generated content

### Memory Features
- **Conversation Continuity**: Maintains context across sessions
- **Fact Extraction**: Automatic knowledge extraction and storage
- **Semantic Search**: Find relevant information by meaning, not just keywords
- **Token Management**: Efficient memory usage with automatic cleanup

### Production Features
- **Error Handling**: Comprehensive error recovery and logging
- **Performance Monitoring**: Response time and accuracy metrics
- **Evaluation Framework**: Automated testing of memory and response quality
- **API Documentation**: OpenAPI/Swagger integration

## 🧪 Testing & Evaluation

### Test Suite
```bash
# Run all tests
python -m pytest tests/

# Test specific components
python -m pytest tests/test_llm_client.py
python -m pytest tests/test_memory_system.py
```

### Evaluation Metrics
```bash
# Run evaluation via API
curl -X POST http://localhost:8000/evaluate

# Run benchmarks
curl -X POST http://localhost:8000/benchmark
```

### Evaluation Categories
- **Memory Retrieval Accuracy**: Tests hybrid memory system effectiveness
- **Query Decomposition Quality**: Evaluates sub-query generation
- **Response Coherence**: Measures response quality and relevance
- **Source Attribution**: Validates proper source citation

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=localhost
API_PORT=8000
LOG_LEVEL=INFO

# Memory Configuration
MEMORY_TOKEN_LIMIT=40000
FACT_CONFIDENCE_THRESHOLD=0.5

# Vector Store Configuration
VECTOR_STORE_TOP_K=5
SIMILARITY_THRESHOLD=0.7
```

### Memory Settings
- **Short-term**: 40k token limit with FIFO eviction
- **Long-term**: Unlimited fact storage with confidence filtering
- **Vector**: Top-5 semantic matches with 0.7 similarity threshold

## 📈 Performance

### Benchmarks
- **Simple Queries**: ~200ms average response time
- **Complex Queries**: ~800ms with 4 sub-queries
- **Memory Retrieval**: ~50ms for hybrid context
- **Vector Search**: ~30ms for top-5 results

### Scalability
- **Concurrent Sessions**: Supports multiple user sessions
- **Memory Efficiency**: Automatic token management
- **Database Performance**: SQLite with indexed queries
- **Vector Store**: In-memory with persistent storage option

## 🚀 Deployment

### Docker
```bash
docker-compose up
```

### Production Considerations
- **Database**: Configure persistent SQLite or PostgreSQL
- **Vector Store**: Consider Pinecone/Weaviate for scale
- **Monitoring**: Integrate with logging and metrics systems
- **Security**: Add authentication and rate limiting

## 📚 Documentation

- **Memory System**: See `MEMORY_EXPLANATION.md` for detailed examples
- **Implementation**: See `IMPLEMENTATION_GUIDE.md` for technical details
- **API Reference**: Available at `/docs` when server is running

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Run evaluation suite
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details