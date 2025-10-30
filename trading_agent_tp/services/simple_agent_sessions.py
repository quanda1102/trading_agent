"""
Simple Agent Session Manager

Manages conversation sessions for the simple agent using AdvancedSQLiteSession
from the agents library for persistent memory.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from agents.extensions.memory.advanced_sqlite_session import AdvancedSQLiteSession

logger = logging.getLogger(__name__)


class SimpleAgentSessionManager:
    """
    Manages conversation sessions for the simple agent.

    Sessions are stored per user_id:session_id combination and persist
    conversation history using SQLite storage.
    """

    def __init__(self, db_dir: str = "./data/simple_agent_sessions"):
        """
        Initialize the session manager.

        Args:
            db_dir: Directory to store session databases
        """
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache of active sessions
        self._sessions: Dict[str, AdvancedSQLiteSession] = {}

        logger.info(f"SimpleAgentSessionManager initialized with db_dir: {self.db_dir}")

    def _get_session_key(self, user_id: str, session_id: str) -> str:
        """Generate unique key for user+session combination."""
        return f"{user_id}:{session_id}"

    def _get_db_path(self, user_id: str, session_id: str) -> Path:
        """Generate database file path for a session."""
        # Sanitize user_id and session_id for filesystem
        safe_user = user_id.replace("/", "_").replace("\\", "_")
        safe_session = session_id.replace("/", "_").replace("\\", "_")
        return self.db_dir / f"{safe_user}_{safe_session}.db"

    def get_session(self, user_id: str, session_id: str) -> AdvancedSQLiteSession:
        """
        Get or create a session for the given user_id and session_id.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            AdvancedSQLiteSession instance
        """
        session_key = self._get_session_key(user_id, session_id)

        # Return cached session if available
        if session_key in self._sessions:
            logger.debug(f"Retrieved cached session: {session_key}")
            return self._sessions[session_key]

        # Create new session
        db_path = self._get_db_path(user_id, session_id)
        session = AdvancedSQLiteSession(
            session_id=session_key,
            db_path=str(db_path),
            create_tables=True,
            logger=logger
        )

        # Cache the session
        self._sessions[session_key] = session

        logger.info(f"Created new session: {session_key} at {db_path}")
        return session

    def clear_session(self, user_id: str, session_id: str) -> None:
        """
        Clear a specific session from cache and optionally delete its database.

        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        session_key = self._get_session_key(user_id, session_id)

        # Remove from cache
        if session_key in self._sessions:
            del self._sessions[session_key]
            logger.info(f"Cleared session from cache: {session_key}")

        # Optionally delete database file
        db_path = self._get_db_path(user_id, session_id)
        if db_path.exists():
            db_path.unlink()
            logger.info(f"Deleted session database: {db_path}")

    def get_session_info(self, user_id: str, session_id: str) -> Dict:
        """
        Get information about a session.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Dictionary with session information
        """
        session_key = self._get_session_key(user_id, session_id)
        db_path = self._get_db_path(user_id, session_id)

        return {
            "session_key": session_key,
            "user_id": user_id,
            "session_id": session_id,
            "db_path": str(db_path),
            "exists": db_path.exists(),
            "cached": session_key in self._sessions
        }


# Global session manager instance
_session_manager: Optional[SimpleAgentSessionManager] = None


def get_session_manager() -> SimpleAgentSessionManager:
    """
    Get the global session manager instance (singleton pattern).

    Returns:
        SimpleAgentSessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SimpleAgentSessionManager()
    return _session_manager