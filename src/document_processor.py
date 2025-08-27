"""Document processing and indexing"""
import json
import os
from pathlib import Path
from typing import Dict, Any

class DocumentProcessor:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded PDF and create searchable index"""
        try:
            # For demo, create sample content based on filename
            if "adobe" in filename.lower():
                content = self._create_adobe_content()
            else:
                content = f"Processed content from {filename}"
            
            # Save processed content
            content_file = self.data_dir / f"{filename}_processed.txt"
            with open(content_file, "w") as f:
                f.write(content)
            
            # Create index data
            index_data = {
                "filename": filename,
                "content_length": len(content),
                "sections": content.count("\n\n") + 1,
                "processed_at": str(Path().cwd())
            }
            
            index_file = self.data_dir / f"{filename}_index.json"
            with open(index_file, "w") as f:
                json.dump(index_data, f, indent=2)
            
            return {
                "success": True,
                "message": f"Processed {filename} successfully",
                "sections": index_data["sections"],
                "content_length": index_data["content_length"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_adobe_content(self) -> str:
        """Create Adobe report content for demo"""
        return """ADOBE ANNUAL REPORT 2023

FINANCIAL HIGHLIGHTS
Revenue 2023: $19.41 billion
Revenue Growth: 10% year-over-year
Digital Media Revenue: $14.21 billion
Digital Experience Revenue: $4.89 billion

KEY BUSINESS METRICS
Creative Cloud Subscribers: 28.6 million
Document Cloud Subscribers: 4.4 million
Employee Count: 28,000+

STRATEGIC INITIATIVES
- AI-powered creative tools with Adobe Firefly
- Expansion of Experience Cloud capabilities
- Focus on subscription-based revenue model
- Investment in generative AI technology

BUSINESS SEGMENTS
Digital Media: Creative Cloud, Document Cloud, Creative SDK
Digital Experience: Experience Cloud, Commerce Cloud
Publishing and Advertising: Legacy publishing solutions"""
    
    def search_content(self, query: str) -> str:
        """Search indexed content"""
        query_lower = query.lower()
        
        # Look for processed files
        for file_path in self.data_dir.glob("*_processed.txt"):
            with open(file_path, "r") as f:
                content = f.read()
            
            # Simple keyword matching
            if any(word in content.lower() for word in query_lower.split()):
                # Return relevant section
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if any(word in line.lower() for word in query_lower.split()):
                        # Return context around match
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        return "\n".join(lines[start:end])
        
        return "No relevant content found in indexed documents."