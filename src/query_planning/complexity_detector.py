import re
from typing import Dict, Any
import logging

logger = logging.getLogger('query_planning')

class QueryComplexityDetector:
    """Determines if a query is simple or complex based on multiple factors"""
    
    def __init__(self):
        self.simple_keywords = [
            'what', 'who', 'when', 'where', 'define', 'meaning', 'is'
        ]
        
        self.complex_keywords = [
            'analyze', 'compare', 'evaluate', 'assess', 'relationship', 
            'impact', 'implications', 'pros and cons', 'advantages', 
            'disadvantages', 'explain how', 'why does'
        ]
    
    def detect_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze query complexity using multiple indicators
        
        Returns:
            Dict with complexity level and reasoning
        """
        query_lower = query.lower().strip()
        word_count = len(query.split())
        
        complexity_score = 0
        reasons = []
        
        # Length-based scoring
        if word_count > 25:
            complexity_score += 3
            reasons.append(f"Long query ({word_count} words)")
        elif word_count > 15:
            complexity_score += 2
            reasons.append(f"Medium length ({word_count} words)")
        elif word_count < 8:
            complexity_score -= 1
            reasons.append(f"Short query ({word_count} words)")
        
        # Keyword analysis
        simple_found = sum(1 for kw in self.simple_keywords if kw in query_lower)
        complex_found = sum(1 for kw in self.complex_keywords if kw in query_lower)
        
        if complex_found > 0:
            complexity_score += complex_found * 2
            reasons.append(f"Complex keywords found: {complex_found}")
        
        if simple_found > 0 and complex_found == 0:
            complexity_score -= 1
            reasons.append(f"Simple keywords found: {simple_found}")
        
        # Multiple questions or topics
        question_marks = query.count('?')
        if question_marks > 1:
            complexity_score += 2
            reasons.append(f"Multiple questions ({question_marks})")
        
        # Conjunctions indicating multiple parts
        conjunctions = ['and', 'but', 'however', 'also', 'additionally']
        conjunction_count = sum(1 for conj in conjunctions if conj in query_lower)
        if conjunction_count > 1:
            complexity_score += conjunction_count
            reasons.append(f"Multiple topics connected ({conjunction_count} conjunctions)")
        
        # Determine final complexity
        if complexity_score >= 4:
            complexity_level = "complex"
        elif complexity_score >= 2:
            complexity_level = "moderate"
        else:
            complexity_level = "simple"
        
        logger.info(f"Query complexity: {complexity_level} (score: {complexity_score})")
        
        return {
            'complexity_level': complexity_level,
            'complexity_score': complexity_score,
            'word_count': word_count,
            'reasons': reasons,
            'requires_decomposition': complexity_level in ['complex', 'moderate']
        }
    
    def should_decompose(self, query: str) -> bool:
        """Simple boolean check if query needs decomposition"""
        result = self.detect_complexity(query)
        return result['requires_decomposition']