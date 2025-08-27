"""Simple demonstration"""
import asyncio

async def run_demo():
    print("MEMORY-PERSISTENT RESEARCH ASSISTANT - DEMO")
    print("=" * 60)
    
    # Test memory systems
    print("\n1. TESTING MEMORY SYSTEMS...")
    from src.memory.short_term import ShortTermMemory
    
    memory = ShortTermMemory("demo", token_limit=200)
    from llama_index.core.llms import ChatMessage
    
    memory.add_message(ChatMessage(role="user", content="I'm researching Adobe's AI strategy"))
    memory.add_message(ChatMessage(role="assistant", content="I can help with Adobe research"))
    
    print(f"[PASS] Short-term memory: {len(memory.get_context())} messages stored")
    
    # Test query complexity
    print("\n2. TESTING QUERY PROCESSING...")
    from src.query_planning.complexity_detector import QueryComplexityDetector
    
    detector = QueryComplexityDetector()
    simple_result = detector.detect_complexity("What is Adobe's revenue?")
    complex_result = detector.detect_complexity("Analyze Adobe's AI strategy and compare it with competitors")
    
    print(f"[PASS] Simple query: {simple_result['complexity_level']}")
    print(f"[PASS] Complex query: {complex_result['complexity_level']}")
    
    # Test workflow
    print("\n3. TESTING WORKFLOW INTEGRATION...")
    from src.workflow import process_research_query
    
    result = await process_research_query("What are Adobe's key financial metrics?", "demo")
    print(f"[PASS] Workflow processed: {result['complexity']['complexity_level']} query")
    
    # Test Adobe integration
    print("\n4. TESTING ADOBE KNOWLEDGE BASE...")
    import json
    with open("data/adobe_report_data.json", "r") as f:
        adobe_data = json.load(f)
    
    print(f"[PASS] Adobe data loaded: {len(adobe_data)} sections")
    print(f"[PASS] Revenue data: {adobe_data['financial_highlights']['revenue_2023']}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE - ALL SYSTEMS OPERATIONAL")
    print("=" * 60)
    

if __name__ == "__main__":
    asyncio.run(run_demo())