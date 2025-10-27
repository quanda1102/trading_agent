"""
Unit tests for SQLite storage adapter.
"""

import pytest
import sqlite3
from datetime import datetime
from trading_agent_tp.services.storage_sqlite import SQLiteStorage


@pytest.mark.unit
class TestSQLiteStorage:
    """Test suite for SQLiteStorage class."""

    def test_init_creates_database(self, temp_db_path):
        """Test that initialization creates database and tables."""
        storage = SQLiteStorage(db_path=temp_db_path)

        # Check that database file was created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check that memories table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"
        )
        assert cursor.fetchone() is not None

        # Check that index exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_session'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_store_message(self, sqlite_storage):
        """Test storing a message."""
        user_id = "user123"
        session_id = "session456"
        role = "user"
        content = "Test message"

        sqlite_storage.store_message(user_id, session_id, role, content)

        # Verify message was stored
        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 1
        assert messages[0]["role"] == role
        assert messages[0]["content"] == content

    def test_get_messages_returns_chronological_order(self, sqlite_storage):
        """Test that get_messages returns messages in chronological order."""
        user_id = "user123"
        session_id = "session456"

        # Store multiple messages
        for i in range(5):
            sqlite_storage.store_message(
                user_id, session_id, "user", f"Message {i}"
            )

        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)

        # Verify order
        assert len(messages) == 5
        assert messages[0]["content"] == "Message 0"
        assert messages[4]["content"] == "Message 4"

    def test_get_messages_respects_limit(self, sqlite_storage):
        """Test that get_messages respects the limit parameter."""
        user_id = "user123"
        session_id = "session456"

        # Store 10 messages
        for i in range(10):
            sqlite_storage.store_message(
                user_id, session_id, "user", f"Message {i}"
            )

        # Get only 5 messages
        messages = sqlite_storage.get_messages(user_id, session_id, limit=5)

        # Should return the 5 most recent messages
        assert len(messages) == 5
        # Most recent messages are returned (reversed, so we get 5-9)
        assert messages[0]["content"] == "Message 5"
        assert messages[4]["content"] == "Message 9"

    def test_get_messages_filters_by_user_and_session(self, sqlite_storage):
        """Test that get_messages filters by user_id and session_id."""
        # Store messages for different users and sessions
        sqlite_storage.store_message("user1", "session1", "user", "User1 Session1")
        sqlite_storage.store_message("user1", "session2", "user", "User1 Session2")
        sqlite_storage.store_message("user2", "session1", "user", "User2 Session1")

        # Get messages for user1, session1
        messages = sqlite_storage.get_messages("user1", "session1", limit=10)

        assert len(messages) == 1
        assert messages[0]["content"] == "User1 Session1"

    def test_clear_session(self, sqlite_storage):
        """Test clearing messages for a session."""
        user_id = "user123"
        session_id = "session456"

        # Store messages
        for i in range(5):
            sqlite_storage.store_message(
                user_id, session_id, "user", f"Message {i}"
            )

        # Verify messages exist
        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 5

        # Clear session
        sqlite_storage.clear_session(user_id, session_id)

        # Verify messages were deleted
        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 0

    def test_clear_session_only_affects_specified_session(self, sqlite_storage):
        """Test that clear_session only deletes messages for the specified session."""
        # Store messages for two sessions
        sqlite_storage.store_message("user1", "session1", "user", "Session1 Message")
        sqlite_storage.store_message("user1", "session2", "user", "Session2 Message")

        # Clear session1
        sqlite_storage.clear_session("user1", "session1")

        # Verify session1 is cleared but session2 is not
        messages1 = sqlite_storage.get_messages("user1", "session1", limit=10)
        messages2 = sqlite_storage.get_messages("user1", "session2", limit=10)

        assert len(messages1) == 0
        assert len(messages2) == 1

    def test_get_context(self, sqlite_storage):
        """Test getting conversation context as string."""
        user_id = "user123"
        session_id = "session456"

        # Store conversation
        sqlite_storage.store_message(user_id, session_id, "user", "Hello")
        sqlite_storage.store_message(user_id, session_id, "assistant", "Hi there!")
        sqlite_storage.store_message(user_id, session_id, "user", "How are you?")

        # Get context
        context = sqlite_storage.get_context(user_id, session_id, max_messages=10)

        # Verify format
        assert "user: Hello" in context
        assert "assistant: Hi there!" in context
        assert "user: How are you?" in context

        # Verify order (chronological)
        lines = context.split("\n")
        assert len(lines) == 3
        assert lines[0] == "user: Hello"
        assert lines[1] == "assistant: Hi there!"
        assert lines[2] == "user: How are you?"

    def test_get_context_respects_max_messages(self, sqlite_storage):
        """Test that get_context respects max_messages parameter."""
        user_id = "user123"
        session_id = "session456"

        # Store 10 messages
        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            sqlite_storage.store_message(user_id, session_id, role, f"Message {i}")

        # Get context with max_messages=5
        context = sqlite_storage.get_context(user_id, session_id, max_messages=5)

        lines = context.split("\n")
        assert len(lines) == 5

    def test_get_context_empty_session(self, sqlite_storage):
        """Test get_context with no messages."""
        context = sqlite_storage.get_context("user123", "session456", max_messages=10)
        assert context == ""

    def test_store_message_with_timestamps(self, sqlite_storage, temp_db_path):
        """Test that messages are stored with correct timestamps."""
        user_id = "user123"
        session_id = "session456"

        before = datetime.now().isoformat()
        sqlite_storage.store_message(user_id, session_id, "user", "Test")
        after = datetime.now().isoformat()

        # Query database directly to check timestamps
        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, created_at FROM memories WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert before <= row["timestamp"] <= after
        assert before <= row["created_at"] <= after

    def test_concurrent_sessions(self, sqlite_storage):
        """Test handling multiple concurrent sessions."""
        # Store messages for multiple users and sessions simultaneously
        for user_id in ["user1", "user2", "user3"]:
            for session_id in ["session1", "session2"]:
                for i in range(3):
                    sqlite_storage.store_message(
                        user_id,
                        session_id,
                        "user",
                        f"{user_id}-{session_id}-{i}"
                    )

        # Verify each session has correct messages
        for user_id in ["user1", "user2", "user3"]:
            for session_id in ["session1", "session2"]:
                messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
                assert len(messages) == 3
                assert all(f"{user_id}-{session_id}" in msg["content"] for msg in messages)

    def test_special_characters_in_content(self, sqlite_storage):
        """Test storing and retrieving messages with special characters."""
        user_id = "user123"
        session_id = "session456"
        special_content = "Test with 'quotes', \"double quotes\", and special chars: çñ€¥"

        sqlite_storage.store_message(user_id, session_id, "user", special_content)

        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 1
        assert messages[0]["content"] == special_content

    def test_unicode_vietnamese_content(self, sqlite_storage):
        """Test storing and retrieving Vietnamese unicode content."""
        user_id = "user123"
        session_id = "session456"
        vietnamese_content = "Phân tích kỹ thuật BTC với RSI và MACD"

        sqlite_storage.store_message(user_id, session_id, "user", vietnamese_content)

        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 1
        assert messages[0]["content"] == vietnamese_content

    def test_large_content(self, sqlite_storage):
        """Test storing large content."""
        user_id = "user123"
        session_id = "session456"
        large_content = "A" * 100000  # 100KB of text

        sqlite_storage.store_message(user_id, session_id, "user", large_content)

        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 1
        assert len(messages[0]["content"]) == 100000

    def test_empty_content(self, sqlite_storage):
        """Test storing empty content."""
        user_id = "user123"
        session_id = "session456"

        sqlite_storage.store_message(user_id, session_id, "user", "")

        messages = sqlite_storage.get_messages(user_id, session_id, limit=10)
        assert len(messages) == 1
        assert messages[0]["content"] == ""