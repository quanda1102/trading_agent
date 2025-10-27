"""
SQLite Storage Adapter - Optimized Version

Provides SQLite-based storage for short-term memory with:
- Connection pooling and reuse
- Retry logic for transient failures
- Input validation
- Comprehensive error handling
- Structured logging
"""

import sqlite3
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class ValidationError(StorageError):
    """Raised when input validation fails."""
    pass


class ConnectionError(StorageError):
    """Raised when database connection fails."""
    pass


class SQLiteStorage:
    """SQLite storage adapter for short-term memory with connection pooling."""

    # Valid roles for message storage
    VALID_ROLES = {"user", "assistant", "system"}

    def __init__(
        self,
        db_path: str = "memory.db",
        max_retries: int = 3,
        timeout: float = 10.0,
        check_same_thread: bool = False
    ):
        """
        Initialize SQLite storage with connection pooling.

        Args:
            db_path: Path to SQLite database file
            max_retries: Maximum number of retry attempts for transient failures
            timeout: Database connection timeout in seconds
            check_same_thread: Whether to check thread safety (False for multi-threaded)
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self.timeout = timeout
        self.check_same_thread = check_same_thread

        # Ensure parent directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        try:
            self._init_db()
            logger.info(f"SQLiteStorage initialized with database: {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise ConnectionError(f"Failed to initialize database: {e}")

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with retry logic.

        Yields:
            sqlite3.Connection: Database connection with row_factory set

        Raises:
            ConnectionError: If connection fails after max retries
        """
        conn = None
        last_error = None

        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=self.timeout,
                    check_same_thread=self.check_same_thread
                )
                conn.row_factory = sqlite3.Row

                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys=ON")

                yield conn

                conn.commit()
                conn.close()
                return

            except sqlite3.OperationalError as e:
                last_error = e
                if conn:
                    conn.close()

                if attempt < self.max_retries - 1:
                    backoff_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Database connection attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Database connection failed after {self.max_retries} attempts")
                    raise ConnectionError(f"Database connection failed: {e}")

            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                    conn.close()
                logger.error(f"Database operation failed: {e}")
                raise StorageError(f"Database operation failed: {e}")

    def _init_db(self):
        """Initialize database tables and indexes."""
        with self._get_connection() as conn:
            # Create memories table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_session
                ON memories(user_id, session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON memories(timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_session_timestamp
                ON memories(user_id, session_id, timestamp DESC)
            """)

            # Analyze for query optimization
            conn.execute("ANALYZE")

            logger.debug("Database schema initialized successfully")

    def _validate_inputs(self, user_id: str, session_id: str, role: str = None):
        """
        Validate input parameters.

        Args:
            user_id: User identifier
            session_id: Session identifier
            role: Message role (optional)

        Raises:
            ValidationError: If any parameter is invalid
        """
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("user_id must be a non-empty string")

        if not session_id or not isinstance(session_id, str):
            raise ValidationError("session_id must be a non-empty string")

        if len(user_id) > 255:
            raise ValidationError("user_id must be 255 characters or less")

        if len(session_id) > 255:
            raise ValidationError("session_id must be 255 characters or less")

        if role is not None and role not in self.VALID_ROLES:
            raise ValidationError(
                f"role must be one of {self.VALID_ROLES}, got: {role}"
            )

    def store_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str
    ) -> int:
        """
        Store a message in the database.

        Args:
            user_id: User identifier
            session_id: Session identifier
            role: Message role (user, assistant, or system)
            content: Message content

        Returns:
            int: ID of the inserted message

        Raises:
            ValidationError: If inputs are invalid
            StorageError: If storage operation fails
        """
        # Validate inputs
        self._validate_inputs(user_id, session_id, role)

        if not isinstance(content, str):
            raise ValidationError("content must be a string")

        timestamp = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO memories (user_id, session_id, role, content, timestamp, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, session_id, role, content, timestamp, timestamp))

                message_id = cursor.lastrowid

            logger.debug(
                f"Stored message {message_id} for {user_id}/{session_id} "
                f"(role={role}, content_len={len(content)})"
            )

            return message_id

        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            raise StorageError(f"Failed to store message: {e}")

    def get_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages for a session.

        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries in chronological order

        Raises:
            ValidationError: If inputs are invalid
            StorageError: If retrieval fails
        """
        # Validate inputs
        self._validate_inputs(user_id, session_id)

        if not isinstance(limit, int) or limit < 1:
            raise ValidationError("limit must be a positive integer")

        if limit > 1000:
            raise ValidationError("limit must be 1000 or less")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT role, content, timestamp
                    FROM memories
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, session_id, limit))

                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"]
                    })

            # Return in chronological order (oldest first)
            result = list(reversed(messages))

            logger.debug(
                f"Retrieved {len(result)} messages for {user_id}/{session_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            raise StorageError(f"Failed to retrieve messages: {e}")

    def clear_session(self, user_id: str, session_id: str) -> int:
        """
        Clear all messages for a session.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            int: Number of messages deleted

        Raises:
            ValidationError: If inputs are invalid
            StorageError: If deletion fails
        """
        # Validate inputs
        self._validate_inputs(user_id, session_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM memories
                    WHERE user_id = ? AND session_id = ?
                """, (user_id, session_id))

                deleted_count = cursor.rowcount

            logger.info(
                f"Cleared {deleted_count} messages for {user_id}/{session_id}"
            )

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            raise StorageError(f"Failed to clear session: {e}")

    def get_context(
        self,
        user_id: str,
        session_id: str,
        max_messages: int = 10
    ) -> str:
        """
        Get conversation context as a formatted string.

        Args:
            user_id: User identifier
            session_id: Session identifier
            max_messages: Maximum number of messages to include

        Returns:
            Formatted conversation context string

        Raises:
            ValidationError: If inputs are invalid
            StorageError: If retrieval fails
        """
        messages = self.get_messages(user_id, session_id, max_messages)

        if not messages:
            return ""

        context_parts = []
        for msg in messages:
            context_parts.append(f"{msg['role']}: {msg['content']}")

        context = "\n".join(context_parts)

        logger.debug(
            f"Generated context for {user_id}/{session_id}: "
            f"{len(messages)} messages, {len(context)} chars"
        )

        return context

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            with self._get_connection() as conn:
                # Total messages
                total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

                # Unique users
                users = conn.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM memories"
                ).fetchone()[0]

                # Unique sessions
                sessions = conn.execute(
                    "SELECT COUNT(DISTINCT user_id || ':' || session_id) FROM memories"
                ).fetchone()[0]

                # Database size
                db_size = Path(self.db_path).stat().st_size / 1024  # KB

            stats = {
                "total_messages": total,
                "unique_users": users,
                "unique_sessions": sessions,
                "database_size_kb": round(db_size, 2)
            }

            logger.debug(f"Database stats: {stats}")

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self):
        """
        Close the storage adapter.

        Note: With context manager approach, connections are already closed.
        This method is kept for API compatibility.
        """
        logger.info(f"SQLiteStorage closed for {self.db_path}")