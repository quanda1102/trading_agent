"""
ChromaDB Storage Adapter

Provides ChromaDB-based storage for long-term memory and embeddings.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import json


class ChromaDBStorage:
    """ChromaDB storage adapter for long-term memory."""
    
    def __init__(self, chroma_path: str = "./chroma_db"):
        self.chroma_path = chroma_path
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="trading_memory",
            metadata={"description": "Trading conversation memory"}
        )
    
    def store_interaction(self, user_id: str, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Store an interaction in ChromaDB."""
        doc_id = f"{user_id}_{session_id}_{len(self.collection.get()['ids'])}"
        
        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[{
                "user_id": user_id,
                "session_id": session_id,
                "content_type": "interaction",
                **(metadata or {})
            }]
        )
    
    def search_similar(self, query: str, user_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar interactions."""
        where_clause = {}
        if user_id:
            where_clause["user_id"] = user_id
        
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause if where_clause else None
        )
        
        interactions = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                interactions.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return interactions
    
    def get_user_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's interaction history."""
        results = self.collection.get(
            where={"user_id": user_id},
            limit=limit
        )
        
        interactions = []
        if results['documents']:
            for i, doc in enumerate(results['documents']):
                interactions.append({
                    "content": doc,
                    "metadata": results['metadatas'][i] if results['metadatas'] else {},
                    "id": results['ids'][i] if results['ids'] else None
                })
        
        return interactions
    
    def clear_user_data(self, user_id: str):
        """Clear all data for a user."""
        # ChromaDB doesn't have a direct delete by metadata, so we get and delete
        results = self.collection.get(where={"user_id": user_id})
        if results['ids']:
            self.collection.delete(ids=results['ids'])
