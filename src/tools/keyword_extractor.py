from typing import List, Dict, Any
import re
from collections import Counter
import logging
from llama_index.core.tools import FunctionTool
from ..utils.azure_client import get_azure_llm

logger = logging.getLogger('query_planning')

class KeywordExtractor:
    """Extracts keywords and key phrases from text using multiple methods"""
    
    def __init__(self):
        self.llm = get_azure_llm()
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
    
    def extract_statistical_keywords(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Extract keywords using statistical frequency analysis"""
        # Clean and tokenize text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out stop words
        filtered_words = [word for word in words if word not in self.stop_words]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        # Extract top keywords
        keywords = []
        for word, count in word_counts.most_common(top_k):
            keywords.append({
                'keyword': word,
                'frequency': count,
                'score': count / len(filtered_words),
                'method': 'statistical'
            })
        
        return keywords
    
    async def extract_semantic_keywords(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Extract keywords using LLM semantic understanding"""
        extraction_prompt = f"""
        Extract the most important keywords and key phrases from the following text.
        Focus on:
        - Main topics and concepts
        - Technical terms
        - Important entities (people, places, organizations)
        - Key actions or processes
        
        Return as JSON list: [{{"keyword": "term", "importance": 0.9, "category": "concept"}}]
        
        Text: {text[:2000]}
        """
        
        try:
            response = await self.llm.acomplete(extraction_prompt)
            import json
            keywords_data = json.loads(response.text.strip())
            
            keywords = []
            for item in keywords_data[:top_k]:
                keywords.append({
                    'keyword': item['keyword'],
                    'importance': item['importance'],
                    'category': item.get('category', 'general'),
                    'method': 'semantic'
                })
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error in semantic keyword extraction: {e}")
            return []
    
    def extract_phrases(self, text: str, min_length: int = 2, max_length: int = 4) -> List[Dict[str, Any]]:
        """Extract key phrases using n-gram analysis"""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        phrases = []
        
        for n in range(min_length, max_length + 1):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                
                # Skip phrases with only stop words
                phrase_words = phrase.split()
                if all(word in self.stop_words for word in phrase_words):
                    continue
                
                phrases.append(phrase)
        
        # Count phrase frequencies
        phrase_counts = Counter(phrases)
        
        # Return top phrases
        key_phrases = []
        for phrase, count in phrase_counts.most_common(10):
            if count > 1:  # Only include phrases that appear multiple times
                key_phrases.append({
                    'phrase': phrase,
                    'frequency': count,
                    'length': len(phrase.split()),
                    'method': 'n-gram'
                })
        
        return key_phrases
    
    async def extract_comprehensive_keywords(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract keywords using all methods and combine results"""
        results = {
            'statistical_keywords': self.extract_statistical_keywords(text),
            'semantic_keywords': await self.extract_semantic_keywords(text),
            'key_phrases': self.extract_phrases(text)
        }
        
        logger.info(f"Extracted keywords: {len(results['statistical_keywords'])} statistical, "
                   f"{len(results['semantic_keywords'])} semantic, {len(results['key_phrases'])} phrases")
        
        return results

def create_keyword_extraction_tool() -> FunctionTool:
    """Create a LlamaIndex tool for keyword extraction"""
    
    extractor = KeywordExtractor()
    
    async def extract_keywords_from_text(text: str) -> str:
        """Extract keywords and key phrases from the given text"""
        results = await extractor.extract_comprehensive_keywords(text)
        
        # Format results for output
        output_parts = []
        
        if results['statistical_keywords']:
            output_parts.append("Statistical Keywords:")
            for kw in results['statistical_keywords'][:5]:
                output_parts.append(f"- {kw['keyword']} (freq: {kw['frequency']})")
        
        if results['semantic_keywords']:
            output_parts.append("\nSemantic Keywords:")
            for kw in results['semantic_keywords'][:5]:
                output_parts.append(f"- {kw['keyword']} (importance: {kw['importance']:.2f})")
        
        if results['key_phrases']:
            output_parts.append("\nKey Phrases:")
            for phrase in results['key_phrases'][:5]:
                output_parts.append(f"- {phrase['phrase']} (freq: {phrase['frequency']})")
        
        return "\n".join(output_parts)
    
    return FunctionTool.from_defaults(
        fn=extract_keywords_from_text,
        name="keyword_extractor",
        description="Extract important keywords and key phrases from text content"
    )