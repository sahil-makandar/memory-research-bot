from typing import List, Dict
import logging
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.tools import FunctionTool
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

logger = logging.getLogger('query_planning')

class DocumentRetriever:
    def __init__(self, vector_store_path: str = "./data/chroma_db"):
        self.vector_store_path = vector_store_path
        self.index = None
        self._setup_vector_store()
    
    def _setup_vector_store(self):
        try:
            client = chromadb.PersistentClient(path=self.vector_store_path)
            collection = client.get_or_create_collection("documents")
            vector_store = ChromaVectorStore(chroma_collection=collection)
            self.index = VectorStoreIndex.from_vector_store(vector_store)
        except Exception as e:
            logger.error(f"Vector store setup error: {e}")
    
    def retrieve_documents(self, query: str, top_k: int = 5) -> List[str]:
        if not self.index:
            return ["Vector store not available"]
        
        try:
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            return [node.text for node in nodes]
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

def create_retrieval_tool() -> FunctionTool:
    retriever = DocumentRetriever()
    
    def retrieve_relevant_content(query: str, num_results: int = 3) -> str:
        """Retrieve relevant document content based on query"""
        results = retriever.retrieve_documents(query, num_results)
        return "\n---\n".join(results) if results else "No relevant content found"
    
    return FunctionTool.from_defaults(
        fn=retrieve_relevant_content,
        name="document_retriever",
        description="Retrieve relevant document content based on search query"
    )