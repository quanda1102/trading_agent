"""
Chat Search Service using ChromaDB for semantic search.

Allows users to search their chat history by semantic similarity.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)


class ChatSearchService:
    """Semantic search service for chat history using ChromaDB."""

    def __init__(self, chroma_path: str = "./data/chroma_chat_search"):
        """
        Initialize ChatSearchService with ChromaDB.

        Args:
            chroma_path: Path to ChromaDB persistent storage
        """
        self.chroma_path = chroma_path
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="chat_search",
            metadata={"description": "Semantic search for chat conversations"}
        )
        logger.info(f"ChatSearchService initialized with ChromaDB at {chroma_path}")

    def index_conversation(
        self,
        *,
        interaction_id: int,
        user_id: str,
        session_id: str,
        question: str,
        answer: str,
        created_at: str
    ) -> None:
        """
        Index a conversation for semantic search.

        Args:
            interaction_id: Database interaction ID
            user_id: User identifier
            session_id: Session identifier
            question: User's question
            answer: AI's answer
            created_at: Timestamp of the interaction
        """
        try:
            # Combine question and answer for better search context
            combined_text = f"Q: {question}\nA: {answer}"

            doc_id = f"{user_id}_{session_id}_{interaction_id}"

            self.collection.add(
                documents=[combined_text],
                ids=[doc_id],
                metadatas=[{
                    "interaction_id": interaction_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "question": question[:200],  # Store preview
                    "created_at": created_at
                }]
            )

            logger.debug(f"Indexed conversation {doc_id}")

        except Exception as e:
            logger.error(f"Error indexing conversation: {e}", exc_info=True)

    def search_conversations(
        self,
        *,
        query: str,
        user_id: str,
        limit: int = 10,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by semantic similarity.

        Args:
            query: Search query
            user_id: User identifier (filters to user's conversations only)
            limit: Maximum number of results
            session_id: Optional session filter

        Returns:
            List of matching conversations with metadata and similarity scores
        """
        try:
            # Build where clause for filtering
            where_clause: Dict[str, Any] = {"user_id": user_id}
            if session_id:
                where_clause["session_id"] = session_id

            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )

            conversations = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    conversations.append({
                        "interaction_id": results['metadatas'][0][i].get("interaction_id"),
                        "session_id": results['metadatas'][0][i].get("session_id"),
                        "question": results['metadatas'][0][i].get("question"),
                        "created_at": results['metadatas'][0][i].get("created_at"),
                        "similarity_score": 1 - results['distances'][0][i] if results['distances'] else 0,
                        "document_preview": results['documents'][0][i][:200] + "..."
                    })

            logger.info(f"Found {len(conversations)} results for query: {query[:50]}")
            return conversations

        except Exception as e:
            logger.error(f"Error searching conversations: {e}", exc_info=True)
            return []

    def delete_conversation_index(
        self,
        *,
        user_id: str,
        session_id: str
    ) -> None:
        """
        Delete all indexed conversations for a session.

        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        try:
            # Get all documents for this session
            results = self.collection.get(
                where={"user_id": user_id, "session_id": session_id}
            )

            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} indexed conversations for {user_id}/{session_id}")

        except Exception as e:
            logger.error(f"Error deleting conversation index: {e}", exc_info=True)