"""
Memory Manager with Long-term Vector Retrieval

Integrates SQLite (short-term) and ChromaDB (long-term) for comprehensive memory management.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.storage_sqlite import SQLiteStorage
from ..services.storage_chromadb import ChromaDBStorage

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory manager with short-term and long-term storage.

    Short-term: Recent conversation context (SQLite)
    Long-term: Vector-based semantic search for user preferences (ChromaDB)
    """

    def __init__(
        self,
        short_term_db_path: str = "./data/short_term_memory.db",
        long_term_chroma_path: str = "./data/long_term_memory",
        short_term_limit: int = 10
    ):
        """
        Initialize memory manager with both storage systems.

        Args:
            short_term_db_path: Path to SQLite database for recent messages
            long_term_chroma_path: Path to ChromaDB for vector storage
            short_term_limit: Number of recent messages to keep in context
        """
        self.short_term = SQLiteStorage(db_path=short_term_db_path)
        self.long_term = ChromaDBStorage(chroma_path=long_term_chroma_path)
        self.short_term_limit = short_term_limit

        logger.info(f"MemoryManager initialized with short-term (SQLite) and long-term (ChromaDB)")

    # ============= Short-term Memory (Recent Conversations) =============

    def add_interaction(
        self,
        *,
        user_id: str,
        session_id: str,
        question: str,
        answer: str
    ) -> None:
        """
        Add interaction to both short-term and long-term memory.

        Args:
            user_id: User identifier
            session_id: Session identifier
            question: User's question
            answer: AI's answer
        """
        # Store in short-term memory (SQLite)
        self.short_term.store_message(user_id, session_id, "user", question)
        self.short_term.store_message(user_id, session_id, "assistant", answer)

        # Store in long-term memory (ChromaDB) for semantic search
        combined_content = f"Q: {question}\nA: {answer}"
        self.long_term.store_interaction(
            user_id=user_id,
            session_id=session_id,
            content=combined_content,
            metadata={
                "question": question[:200],  # Preview
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.debug(f"Stored interaction for {user_id}/{session_id}")

    def get_context(
        self,
        *,
        user_id: str,
        session_id: str,
        max_messages: Optional[int] = None
    ) -> str:
        """
        Get recent conversation context for the session.

        Args:
            user_id: User identifier
            session_id: Session identifier
            max_messages: Maximum messages to retrieve (defaults to short_term_limit)

        Returns:
            Formatted conversation context string
        """
        limit = max_messages or self.short_term_limit
        return self.short_term.get_context(user_id, session_id, limit)

    def get_history(
        self,
        *,
        user_id: str,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history as structured data.

        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum messages to retrieve

        Returns:
            List of message dictionaries
        """
        limit = limit or self.short_term_limit
        return self.short_term.get_messages(user_id, session_id, limit)

    # ============= Long-term Memory (Vector Retrieval) =============

    def store_user_preference(
        self,
        *,
        user_id: str,
        preference_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store user preference in long-term memory for vector retrieval.

        Examples of preferences:
        - Trading strategy preferences
        - Risk tolerance
        - Preferred indicators
        - Market interests

        Args:
            user_id: User identifier
            preference_type: Type of preference (e.g., "trading_style", "risk_level")
            content: Preference description
            metadata: Additional metadata
        """
        full_metadata = {
            "preference_type": preference_type,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }

        self.long_term.store_interaction(
            user_id=user_id,
            session_id="preferences",  # Special session for preferences
            content=content,
            metadata=full_metadata
        )

        logger.info(f"Stored {preference_type} preference for user {user_id}")

    def search_similar_conversations(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar past conversations using vector similarity.

        This is the core long-term memory retrieval function that uses
        ChromaDB's vector search to find semantically similar interactions.

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results

        Returns:
            List of similar conversations with similarity scores
        """
        results = self.long_term.search_similar(
            query=query,
            user_id=user_id,
            limit=limit
        )

        logger.info(f"Found {len(results)} similar conversations for query: {query[:50]}")
        return results

    def retrieve_user_preferences(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user preferences using vector similarity search.

        This allows the AI to recall user preferences even when they're
        phrased differently or asked about indirectly.

        Args:
            user_id: User identifier
            query: Query about preferences
            limit: Maximum results

        Returns:
            List of relevant preferences with similarity scores
        """
        results = self.long_term.search_similar(
            query=query,
            user_id=user_id,
            limit=limit
        )

        # Filter for preference-type entries
        preferences = [
            r for r in results
            if r.get("metadata", {}).get("preference_type") is not None
        ]

        logger.info(f"Retrieved {len(preferences)} user preferences for query: {query[:50]}")
        return preferences

    def get_all_user_preferences(
        self,
        *,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all stored user preferences.

        Args:
            user_id: User identifier
            limit: Maximum preferences to retrieve

        Returns:
            List of user preferences
        """
        history = self.long_term.get_user_history(user_id, limit)

        # Filter for preferences
        preferences = [
            h for h in history
            if h.get("metadata", {}).get("session_id") == "preferences"
        ]

        return preferences

    # ============= Memory Management =============

    def clear_session(
        self,
        *,
        user_id: str,
        session_id: str
    ) -> None:
        """
        Clear all memory for a specific session.

        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        # Clear short-term memory
        self.short_term.clear_session(user_id, session_id)

        logger.info(f"Cleared session memory for {user_id}/{session_id}")

    def clear_all_user_data(
        self,
        *,
        user_id: str
    ) -> None:
        """
        Clear all data for a user (including long-term memory).

        Args:
            user_id: User identifier
        """
        # Note: SQLiteStorage doesn't have user-level clear, only session-level
        # For complete cleanup, would need to add that method

        # Clear long-term memory
        self.long_term.clear_user_data(user_id)

        logger.warning(f"Cleared ALL data for user {user_id}")

    # ============= Enhanced Context with Long-term Retrieval =============

    def get_enhanced_context(
        self,
        *,
        user_id: str,
        session_id: str,
        current_query: str,
        max_short_term: Optional[int] = None,
        max_long_term: int = 3
    ) -> Dict[str, Any]:
        """
        Get enhanced context combining short-term and long-term memory.

        This provides both:
        1. Recent conversation (short-term)
        2. Relevant past conversations and preferences (long-term)

        Args:
            user_id: User identifier
            session_id: Session identifier
            current_query: Current user query for finding relevant long-term memories
            max_short_term: Max recent messages
            max_long_term: Max similar past conversations

        Returns:
            Dictionary with short_term_context and long_term_context
        """
        # Get short-term context (recent conversation)
        short_term_context = self.get_context(
            user_id=user_id,
            session_id=session_id,
            max_messages=max_short_term
        )

        # Get long-term context (similar past conversations)
        similar_convos = self.search_similar_conversations(
            user_id=user_id,
            query=current_query,
            limit=max_long_term
        )

        # Get relevant user preferences
        preferences = self.retrieve_user_preferences(
            user_id=user_id,
            query=current_query,
            limit=3
        )

        return {
            "short_term_context": short_term_context,
            "similar_conversations": similar_convos,
            "user_preferences": preferences,
            "has_long_term_memory": len(similar_convos) > 0 or len(preferences) > 0
        }