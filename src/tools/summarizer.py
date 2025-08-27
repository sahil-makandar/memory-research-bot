from typing import Dict, Any
import logging
from llama_index.core.tools import FunctionTool
from ..utils.azure_client import get_azure_llm

logger = logging.getLogger('query_planning')

class Summarizer:
    def __init__(self):
        self.llm = get_azure_llm()
    
    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        prompt = f"""Summarize the following text in {max_length} words or less:

{text[:3000]}"""
        
        try:
            response = await self.llm.acomplete(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return text[:max_length] + "..."

def create_summarization_tool() -> FunctionTool:
    summarizer = Summarizer()
    
    async def summarize_content(text: str, max_words: int = 200) -> str:
        """Summarize text content to specified length"""
        return await summarizer.summarize_text(text, max_words)
    
    return FunctionTool.from_defaults(
        fn=summarize_content,
        name="summarizer",
        description="Summarize long text content into concise summaries"
    )