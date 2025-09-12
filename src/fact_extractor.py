"""Fact extraction from conversations"""
from typing import List, Dict, Any

class FactExtractor:
    def __init__(self):
        pass
    
    def extract_facts(self, user_message: str, assistant_response: str) -> List[str]:
        """Extract facts from conversation using LLM"""
        
        # LLM prompt for fact extraction
        prompt = f"""
        Extract important facts from this conversation that should be remembered:
        
        User: {user_message}
        Assistant: {assistant_response}
        
        Extract facts about:
        - User's research interests
        - User's background/context
        - Important information discussed
        - User preferences or needs
        
        Return facts as simple statements.
        """
        
        # Simulate LLM fact extraction
        facts = []
        user_lower = user_message.lower()
        
        # Extract user context facts
        if any(phrase in user_lower for phrase in ['i am', 'i work', 'my research', 'studying']):
            facts.append(f"User context: {user_message[:100]}...")
        
        if any(phrase in user_lower for phrase in ['interested in', 'working on', 'need to know']):
            facts.append(f"User interest: {user_message[:100]}...")
        
        # Extract topic facts from assistant response
        if 'adobe' in assistant_response.lower():
            facts.append("User asked about Adobe-related information")
        
        if any(word in user_lower for word in ['revenue', 'financial', 'strategy', 'ai']):
            topic = next((word for word in ['revenue', 'financial', 'strategy', 'ai'] if word in user_lower), 'general')
            facts.append(f"User interested in Adobe's {topic}")
        
        return facts
    
    def llm_extract_facts(self, conversation_text: str) -> List[str]:
        """Use LLM to extract facts from conversation"""
        
        # Simulate advanced LLM fact extraction
        facts = []
        
        if 'research' in conversation_text.lower():
            facts.append("User is conducting research")
        
        if 'thesis' in conversation_text.lower():
            facts.append("User is working on a thesis")
        
        if 'compare' in conversation_text.lower():
            facts.append("User needs comparative analysis")
        
        return facts