import os

def get_azure_llm():
    """Get configured Azure OpenAI LLM instance"""
    # Simple mock for testing
    class MockLLM:
        async def acomplete(self, prompt):
            class MockResponse:
                text = '[{"fact": "test fact", "confidence": 0.8}]'
            return MockResponse()
    
    return MockLLM()