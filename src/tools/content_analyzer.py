from typing import Dict, List
import logging
from llama_index.core.tools import FunctionTool
from ..utils.azure_client import get_azure_llm

logger = logging.getLogger('query_planning')

class ContentAnalyzer:
    def __init__(self):
        self.llm = get_azure_llm()
    
    async def analyze_content(self, text: str) -> Dict[str, str]:
        prompt = f"""Analyze this content and provide:
1. Main topic
2. Key insights (3-5 bullet points)
3. Content type (report, article, etc.)

Text: {text[:2000]}"""
        
        try:
            response = await self.llm.acomplete(prompt)
            return {"analysis": response.text.strip()}
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"analysis": "Analysis failed"}

def create_content_analysis_tool() -> FunctionTool:
    analyzer = ContentAnalyzer()
    
    async def analyze_text_content(text: str) -> str:
        """Analyze text content for main topics and insights"""
        result = await analyzer.analyze_content(text)
        return result["analysis"]
    
    return FunctionTool.from_defaults(
        fn=analyze_text_content,
        name="content_analyzer",
        description="Analyze text content for topics, insights, and structure"
    )