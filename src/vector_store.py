"""Simple vector store simulation for document search"""
import json
from typing import List, Dict, Any
from pathlib import Path

class VectorStore:
    def __init__(self):
        self.data_dir = Path("data")
        self.indexed_content = self._load_indexed_content()
    
    def _load_indexed_content(self) -> Dict[str, str]:
        """Load all indexed content"""
        content = {}
        
        # Load Adobe data
        try:
            with open(self.data_dir / "adobe_report_data.json", "r") as f:
                adobe_data = json.load(f)
                content["adobe_financial"] = json.dumps(adobe_data.get("financial_highlights", {}))
                content["adobe_metrics"] = json.dumps(adobe_data.get("key_metrics", {}))
                content["adobe_strategy"] = "; ".join(adobe_data.get("strategic_initiatives", []))
                content["adobe_segments"] = json.dumps(adobe_data.get("business_segments", {}))
        except:
            pass
        
        # Load processed documents
        for file_path in self.data_dir.glob("*_processed.txt"):
            try:
                with open(file_path, "r") as f:
                    content[file_path.stem] = f.read()
            except:
                pass
        
        return content
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search vector store for relevant content"""
        query_lower = query.lower()
        results = []
        
        for doc_id, content in self.indexed_content.items():
            content_lower = content.lower()
            
            # Simple relevance scoring
            score = 0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in content_lower:
                    score += content_lower.count(word)
            
            if score > 0:
                results.append({
                    "doc_id": doc_id,
                    "content": content,
                    "score": score
                })
        
        # Sort by relevance and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]