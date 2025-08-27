# Test Guide for Memory-Persistent Research Assistant

## Test Structure

### Test Categories

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **Performance Tests** - Test system performance and scalability
4. **Error Handling Tests** - Test edge cases and error scenarios

### Test Files

- `test_memory.py` - Memory system tests (short-term, long-term, blocks)
- `test_query_planning.py` - Query complexity detection and planning tests
- `test_tools.py` - Tool functionality tests (keyword extraction, summarization, etc.)
- `test_workflows.py` - Workflow orchestration tests
- `test_integration.py` - End-to-end integration and performance tests

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Suite
```bash
python run_tests.py memory      # Memory tests only
python run_tests.py query       # Query planning tests only
python run_tests.py tools       # Tools tests only
python run_tests.py workflows   # Workflow tests only
python run_tests.py integration # Integration tests only
```

### Using pytest (alternative)
```bash
pip install pytest
pytest tests/                   # All tests
pytest tests/test_memory.py     # Specific file
pytest -k "test_complexity"     # Tests matching pattern
```

## Test Coverage

### Memory System Tests
-  Short-term memory FIFO buffer functionality
-  Token limit enforcement and message flushing
-  Long-term fact extraction and storage
-  Memory block management and prioritization
-  Database persistence across sessions

### Query Planning Tests
-  Query complexity detection (simple/moderate/complex)
-  Query decomposition for complex queries
-  Tool selection based on query type
-  Execution order planning by priority

### Tool Tests
-  Keyword extraction (statistical and semantic)
-  Text summarization functionality
-  Content analysis capabilities
-  Document retrieval system
-  Error handling for external dependencies

### Workflow Tests
-  Memory workflow operations
-  Query processing workflow
-  Main research workflow orchestration
-  Event handling and data flow

### Integration Tests
-  End-to-end query processing
-  Memory persistence across sessions
-  Component interaction validation
-  Performance benchmarks
-  Error handling and edge cases

## Mock Strategy

Tests use mocking for:
- **Azure OpenAI API calls** - Prevents actual API usage during testing
- **Database operations** - Uses temporary databases for isolation
- **Vector store operations** - Mocks ChromaDB interactions
- **File system operations** - Uses temporary files

## Test Data

Tests use:
- **Temporary databases** - Created/destroyed per test
- **Mock responses** - Predefined LLM responses for consistency
- **Sample queries** - Range from simple to complex for comprehensive testing
- **Edge cases** - Empty queries, very long queries, invalid inputs

## Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `test_<component>.py`
3. Use appropriate mocking for external dependencies
4. Include both positive and negative test cases
5. Add performance tests for critical operations