from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger('memory_system')

@dataclass
class MemoryBlock:
    """Represents a structured memory block with metadata"""
    content: str
    block_type: str
    priority: int = 1
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class MemoryBlockManager:
    """Manages different types of memory blocks for the research assistant"""
    
    def __init__(self):
        self.static_blocks: List[MemoryBlock] = []
        self.dynamic_blocks: List[MemoryBlock] = []
        self.fact_blocks: List[MemoryBlock] = []
        self.vector_blocks: List[MemoryBlock] = []
    
    def add_static_block(self, content: str, priority: int = 1, metadata: Dict[str, Any] = None):
        """Add static memory block (system instructions, permanent context)"""
        block = MemoryBlock(
            content=content,
            block_type="static",
            priority=priority,
            metadata=metadata or {}
        )
        self.static_blocks.append(block)
        self._sort_blocks_by_priority(self.static_blocks)
        logger.info(f"Added static memory block with priority {priority}")
    
    def add_fact_block(self, content: str, confidence: float = 1.0, source: str = None):
        """Add fact-based memory block"""
        metadata = {
            'confidence': confidence,
            'source': source
        }
        block = MemoryBlock(
            content=content,
            block_type="fact",
            priority=int(confidence * 10),  # Convert confidence to priority
            metadata=metadata
        )
        self.fact_blocks.append(block)
        self._sort_blocks_by_priority(self.fact_blocks)
        logger.info(f"Added fact block with confidence {confidence}")
    
    def add_vector_block(self, content: str, embedding_id: str, similarity_score: float = 0.0):
        """Add vector-based memory block from document retrieval"""
        metadata = {
            'embedding_id': embedding_id,
            'similarity_score': similarity_score
        }
        block = MemoryBlock(
            content=content,
            block_type="vector",
            priority=int(similarity_score * 10),
            metadata=metadata
        )
        self.vector_blocks.append(block)
        self._sort_blocks_by_priority(self.vector_blocks)
        logger.info(f"Added vector block with similarity {similarity_score}")
    
    def add_dynamic_block(self, content: str, priority: int = 5, metadata: Dict[str, Any] = None):
        """Add dynamic memory block (temporary context, query results)"""
        block = MemoryBlock(
            content=content,
            block_type="dynamic",
            priority=priority,
            metadata=metadata or {}
        )
        self.dynamic_blocks.append(block)
        self._sort_blocks_by_priority(self.dynamic_blocks)
        logger.info(f"Added dynamic memory block with priority {priority}")
    
    def _sort_blocks_by_priority(self, blocks: List[MemoryBlock]):
        """Sort blocks by priority (highest first) and timestamp (newest first)"""
        blocks.sort(key=lambda x: (x.priority, x.timestamp), reverse=True)
    
    def get_context_blocks(self, max_blocks: int = 20) -> List[MemoryBlock]:
        """Get prioritized memory blocks for context formation"""
        all_blocks = []
        
        # Add blocks in priority order: static -> facts -> vectors -> dynamic
        all_blocks.extend(self.static_blocks[:5])  # Top 5 static blocks
        all_blocks.extend(self.fact_blocks[:8])    # Top 8 fact blocks
        all_blocks.extend(self.vector_blocks[:5])  # Top 5 vector blocks
        all_blocks.extend(self.dynamic_blocks[:2]) # Top 2 dynamic blocks
        
        # Sort all blocks by priority and return top N
        all_blocks.sort(key=lambda x: (x.priority, x.timestamp), reverse=True)
        return all_blocks[:max_blocks]
    
    def get_blocks_by_type(self, block_type: str) -> List[MemoryBlock]:
        """Retrieve blocks by specific type"""
        type_mapping = {
            'static': self.static_blocks,
            'fact': self.fact_blocks,
            'vector': self.vector_blocks,
            'dynamic': self.dynamic_blocks
        }
        return type_mapping.get(block_type, [])
    
    def clear_dynamic_blocks(self):
        """Clear temporary dynamic blocks"""
        self.dynamic_blocks.clear()
        logger.info("Cleared dynamic memory blocks")
    
    def clear_vector_blocks(self):
        """Clear vector-based blocks (for new document context)"""
        self.vector_blocks.clear()
        logger.info("Cleared vector memory blocks")
    
    def get_memory_summary(self) -> str:
        """Generate summary of current memory state"""
        summary_parts = []
        
        if self.static_blocks:
            summary_parts.append(f"Static blocks: {len(self.static_blocks)}")
        if self.fact_blocks:
            summary_parts.append(f"Fact blocks: {len(self.fact_blocks)}")
        if self.vector_blocks:
            summary_parts.append(f"Vector blocks: {len(self.vector_blocks)}")
        if self.dynamic_blocks:
            summary_parts.append(f"Dynamic blocks: {len(self.dynamic_blocks)}")
        
        return " | ".join(summary_parts) if summary_parts else "No memory blocks"
    
    def format_context_string(self, blocks: List[MemoryBlock] = None) -> str:
        """Format memory blocks into context string"""
        if blocks is None:
            blocks = self.get_context_blocks()
        
        context_parts = []
        for block in blocks:
            header = f"[{block.block_type.upper()}]"
            if block.block_type == "fact" and "confidence" in block.metadata:
                header += f" (confidence: {block.metadata['confidence']})"
            elif block.block_type == "vector" and "similarity_score" in block.metadata:
                header += f" (similarity: {block.metadata['similarity_score']:.2f})"
            
            context_parts.append(f"{header} {block.content}")
        
        return "\n".join(context_parts)