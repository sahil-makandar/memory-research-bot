# Memory Management & Query Processing Explained

## How Memory Works (Simple Explanation)

### Short-Term Memory (Like Your Working Memory)

**What it does:**
- Keeps track of the current conversation
- Remembers what you just said and what the assistant replied
- Has a limit - like trying to remember a long phone number

**How it works:**
1. **Token Counting**: Every word/message uses "tokens" (think of tokens as memory units)
2. **FIFO Buffer**: "First In, First Out" - oldest messages get removed when memory is full
3. **Token Limit**: Maximum 40,000 tokens (roughly 30,000 words)

**Example:**
```
User: "What is AI?"
Assistant: "AI is artificial intelligence..."
User: "How does machine learning work?"
Assistant: "Machine learning uses data to..."

[If memory gets full, the first conversation about AI gets moved out]
```

**Code Logic:**
```python
def add_message(self, message):
    token_count = len(message) // 4  # Rough estimate: 4 chars = 1 token
    
    # If adding this message exceeds limit, remove old messages
    while self.current_tokens + token_count > 40000:
        self._remove_oldest_message()
    
    # Add new message
    self.messages.append(message)
    self.current_tokens += token_count
```

### Long-Term Memory (Like Your Brain's Knowledge Storage)

**What it does:**
- Extracts important facts from conversations
- Stores them permanently in a database
- Retrieves relevant facts when needed

**How it works:**
1. **Fact Extraction**: AI reads conversation and pulls out key information
2. **Database Storage**: Facts stored in SQLite database with confidence scores
3. **Smart Retrieval**: When you ask something, it finds related stored facts

**Example:**
```
From conversation: "I work at Microsoft as a software engineer"
Extracted fact: "User is a software engineer at Microsoft" (confidence: 0.9)

Later when you ask: "What programming languages should I learn?"
System retrieves: "User is a software engineer" and gives relevant advice
```

## Query Complexity Detection (Simple Explanation)

### How the System Decides if a Query is Simple or Complex

**Simple Query Indicators:**
- Short questions (under 20 words)
- Single topic/concept
- Direct questions like "What is X?"
- Keywords: "define", "what", "who", "when"

**Complex Query Indicators:**
- Long questions (over 20 words)
- Multiple topics mentioned
- Requires analysis/comparison
- Keywords: "analyze", "compare", "evaluate", "explain the relationship"

**Detection Logic:**
```python
def detect_complexity(query):
    # Length check
    word_count = len(query.split())
    if word_count > 20:
        return "complex"
    
    # Keyword analysis
    complex_keywords = ["analyze", "compare", "evaluate", "relationship", "impact"]
    if any(keyword in query.lower() for keyword in complex_keywords):
        return "complex"
    
    # Multiple question marks or "and"
    if query.count("?") > 1 or " and " in query:
        return "complex"
    
    return "simple"
```

### Query Processing Steps

**For Simple Queries:**
1. Use one tool (usually document retriever)
2. Get direct answer
3. Return result

**For Complex Queries:**
1. **Decomposition**: Break into 3-5 smaller questions
2. **Planning**: Decide which tools to use for each part
3. **Execution**: Run each sub-query with appropriate tool
4. **Synthesis**: Combine all results into final answer

**Example Complex Query Breakdown:**
```
Original: "Analyze Adobe's financial performance and compare it to competitors, then summarize key risks"

Decomposed into:
1. "What is Adobe's revenue and profit?" → Document Retriever
2. "Who are Adobe's main competitors?" → Document Retriever  
3. "Compare Adobe vs competitors financially" → Content Analyzer
4. "What are Adobe's business risks?" → Document Retriever
5. "Summarize the financial analysis" → Summarizer

Final answer combines all 5 results
```

## Memory Integration During Query Processing

**Step-by-step Process:**

1. **User asks question** → Stored in short-term memory
2. **Check long-term memory** → Find relevant past facts
3. **Determine complexity** → Simple or complex processing
4. **Execute query** → Use appropriate tools
5. **Store response** → Add to short-term memory
6. **Extract facts** → Important info goes to long-term memory

**Memory Context Example:**
```
User: "What should I know about cloud computing?"

System checks:
- Short-term: Recent conversation about technology
- Long-term: "User is a software engineer" (from previous session)

Response tailored to: Technical person asking about cloud computing
```

This creates a personalized, context-aware research assistant that remembers your background and conversation history!