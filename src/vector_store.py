"""Simple vector store simulation for document search"""
import json
from typing import List, Dict, Any
from pathlib import Path

class VectorStore:
    def __init__(self, index_name=None):
        self.index_name = index_name
        self.data_dir = Path("data")
        self.indexed_content = self._load_indexed_content()
        self.documents = []
        self._add_sample_data()
    
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
    
    def add_document(self, content: str, metadata: dict = None):
        """Add document to vector store"""
        doc_id = f"doc_{len(self.documents)}"
        self.documents.append({
            'id': doc_id,
            'content': content,
            'metadata': metadata or {}
        })
        self.indexed_content[doc_id] = content
    
    def index_document(self, file_path: str, filename: str) -> List[str]:
        """Index a PDF document into vector store"""
        try:
            # Simple text extraction simulation
            sections = [
                f"Section 1 from {filename}: Financial highlights and revenue data",
                f"Section 2 from {filename}: Business strategy and market position", 
                f"Section 3 from {filename}: Key metrics and performance indicators",
                f"Section 4 from {filename}: Risk factors and challenges",
                f"Section 5 from {filename}: Future outlook and initiatives"
            ]
            
            # Add each section to vector store
            for i, section in enumerate(sections):
                doc_id = f"{filename}_section_{i+1}"
                self.indexed_content[doc_id] = section
                self.documents.append({
                    'id': doc_id,
                    'content': section,
                    'metadata': {'filename': filename, 'section': i+1}
                })
            
            return sections
            
        except Exception as e:
            raise Exception(f"Failed to index document: {e}")
    
    def _add_sample_data(self):
        """Add sample Adobe data to vector store"""
        sample_docs = [
            {
                "doc_id": "adobe_revenue_2023",
                "content": "Adobe reported total revenue of $19.41 billion for fiscal year 2023, representing 9% year-over-year growth. Digital Media segment generated $14.21 billion (73% of total revenue), Digital Experience contributed $4.89 billion (25% of revenue), and Publishing & Advertising accounted for $0.31 billion (2% of revenue). Creative Cloud subscribers reached 28.1 million globally."
            },
            {
                "doc_id": "adobe_strategy_2023",
                "content": "Adobe's strategic focus centers on AI integration across all product lines with Adobe Firefly generative AI, expansion of Experience Cloud capabilities for enterprise customers, Document Cloud automation and e-signature growth, subscription model optimization, and mobile-first creative tools development. The company is investing heavily in machine learning and cloud infrastructure."
            },
            {
                "doc_id": "adobe_segments_overview",
                "content": "Adobe operates three main business segments: Digital Media includes Creative Cloud (Photoshop, Illustrator, Premiere Pro) and Document Cloud (Acrobat, Sign), Digital Experience provides marketing analytics and commerce solutions (Adobe Experience Manager, Analytics, Commerce), and Publishing & Advertising offers legacy solutions. The company has successfully transitioned to a subscription-based SaaS model."
            },
            {
                "doc_id": "adobe_competitive_position",
                "content": "Adobe maintains market leadership in creative software with strong competitive advantages including integrated ecosystem across creative and marketing workflows, AI-powered innovation with Adobe Sensei and Firefly, enterprise-grade security and compliance, global brand recognition and customer loyalty. Main competitors include Microsoft, Salesforce, and specialized creative software companies."
            },
            {
                "doc_id": "adobe_financial_metrics",
                "content": "Key Adobe financial metrics include Annual Recurring Revenue (ARR) exceeding $15 billion, Creative Cloud subscriber growth of 10% year-over-year, Document Cloud reaching 4.4 million subscribers, gross margin of approximately 85%, and strong cash flow generation. The company trades on NASDAQ under ADBE with market capitalization over $200 billion."
            }
        ]
        
        for doc in sample_docs:
            self.indexed_content[doc["doc_id"]] = doc["content"]
            self.documents.append({
                'id': doc["doc_id"],
                'content': doc["content"],
                'metadata': {'source': 'adobe_data', 'type': 'financial_report'}
            })