"""
Unit tests for ConversationRepository.
"""

import pytest
import json
from trading_agent_tp.storage.conversation_repository import ConversationRepository


@pytest.mark.unit
class TestConversationRepository:
    """Test suite for ConversationRepository class."""

    def test_init_creates_database_tables(self, conversation_repository, temp_db_path):
        """Test that initialization creates required tables and indexes."""
        import sqlite3

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check conversations table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
        )
        assert cursor.fetchone() is not None

        # Check sessions table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        assert cursor.fetchone() is not None

        # Check indexes
        indexes = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        index_names = [row[0] for row in indexes]

        assert "idx_conversations_user_session" in index_names
        assert "idx_sessions_user" in index_names

        conn.close()

    def test_add_interaction(self, conversation_repository, sample_conversation_data):
        """Test adding a new interaction."""
        result = conversation_repository.add_interaction(**sample_conversation_data)

        assert result["id"] is not None
        assert result["user_id"] == sample_conversation_data["user_id"]
        assert result["session_id"] == sample_conversation_data["session_id"]
        assert result["question"] == sample_conversation_data["question"]
        assert result["answer"] == sample_conversation_data["answer"]
        assert result["status"] == "success"
        assert result["success"] is True
        assert result["cycles_used"] == 2

    def test_add_interaction_with_trace(self, conversation_repository):
        """Test adding interaction with trace data."""
        trace = [{"event": "test", "data": "value"}]
        plan_history = [{"cycle": 1, "plan": []}]
        execution_log = [{"task_id": 1, "result": "success"}]

        result = conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question="Test question",
            answer="Test answer",
            trace=trace,
            plan_history=plan_history,
            execution_log=execution_log,
            status="success",
            cycles_used=1
        )

        assert result["trace"] == trace
        assert result["plan_history"] == plan_history
        assert result["execution_log"] == execution_log

    def test_get_interaction(self, conversation_repository, sample_conversation_data):
        """Test retrieving a single interaction by ID."""
        # Add interaction
        added = conversation_repository.add_interaction(**sample_conversation_data)
        interaction_id = added["id"]

        # Get interaction
        result = conversation_repository.get_interaction(interaction_id)

        assert result["id"] == interaction_id
        assert result["user_id"] == sample_conversation_data["user_id"]
        assert result["question"] == sample_conversation_data["question"]

    def test_get_interaction_not_found(self, conversation_repository):
        """Test getting non-existent interaction raises error."""
        with pytest.raises(ValueError, match="Interaction .* not found"):
            conversation_repository.get_interaction(99999)

    def test_get_history(self, conversation_repository):
        """Test getting paginated conversation history."""
        user_id = "user123"
        session_id = "session456"

        # Add multiple interactions
        for i in range(5):
            conversation_repository.add_interaction(
                user_id=user_id,
                session_id=session_id,
                question=f"Question {i}",
                answer=f"Answer {i}",
                status="success",
                cycles_used=1
            )

        # Get history
        items, total = conversation_repository.get_history(
            user_id=user_id,
            session_id=session_id,
            page=1,
            page_size=10
        )

        assert len(items) == 5
        assert total == 5
        # Should be ordered by created_at DESC (most recent first)
        assert items[0]["question"] == "Question 4"
        assert items[4]["question"] == "Question 0"

    def test_get_history_pagination(self, conversation_repository):
        """Test history pagination works correctly."""
        user_id = "user123"
        session_id = "session456"

        # Add 25 interactions
        for i in range(25):
            conversation_repository.add_interaction(
                user_id=user_id,
                session_id=session_id,
                question=f"Question {i}",
                answer=f"Answer {i}",
                status="success",
                cycles_used=1
            )

        # Get page 1 (20 items)
        page1, total = conversation_repository.get_history(
            user_id=user_id,
            session_id=session_id,
            page=1,
            page_size=20
        )

        # Get page 2 (5 items)
        page2, total2 = conversation_repository.get_history(
            user_id=user_id,
            session_id=session_id,
            page=2,
            page_size=20
        )

        assert len(page1) == 20
        assert len(page2) == 5
        assert total == total2 == 25
        # Check no duplicates between pages
        page1_ids = {item["id"] for item in page1}
        page2_ids = {item["id"] for item in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_history_invalid_page(self, conversation_repository):
        """Test validation of page parameter."""
        with pytest.raises(ValueError, match="page must be >= 1"):
            conversation_repository.get_history(
                user_id="user123",
                session_id="session456",
                page=0,
                page_size=10
            )

    def test_get_history_invalid_page_size(self, conversation_repository):
        """Test validation of page_size parameter."""
        with pytest.raises(ValueError, match="page_size must be between 1 and 100"):
            conversation_repository.get_history(
                user_id="user123",
                session_id="session456",
                page=1,
                page_size=0
            )

        with pytest.raises(ValueError, match="page_size must be between 1 and 100"):
            conversation_repository.get_history(
                user_id="user123",
                session_id="session456",
                page=1,
                page_size=101
            )

    def test_clear_session(self, conversation_repository):
        """Test clearing all interactions for a session."""
        user_id = "user123"
        session_id = "session456"

        # Add interactions
        for i in range(5):
            conversation_repository.add_interaction(
                user_id=user_id,
                session_id=session_id,
                question=f"Question {i}",
                answer=f"Answer {i}",
                status="success",
                cycles_used=1
            )

        # Clear session
        conversation_repository.clear_session(user_id=user_id, session_id=session_id)

        # Verify cleared
        items, total = conversation_repository.get_history(
            user_id=user_id,
            session_id=session_id,
            page=1,
            page_size=10
        )

        assert len(items) == 0
        assert total == 0

    def test_clear_session_only_affects_target(self, conversation_repository):
        """Test that clearing a session doesn't affect other sessions."""
        # Add to session1
        conversation_repository.add_interaction(
            user_id="user1",
            session_id="session1",
            question="Q1",
            answer="A1",
            status="success",
            cycles_used=1
        )

        # Add to session2
        conversation_repository.add_interaction(
            user_id="user1",
            session_id="session2",
            question="Q2",
            answer="A2",
            status="success",
            cycles_used=1
        )

        # Clear session1
        conversation_repository.clear_session(user_id="user1", session_id="session1")

        # Check session1 is cleared
        items1, total1 = conversation_repository.get_history(
            user_id="user1",
            session_id="session1",
            page=1,
            page_size=10
        )
        assert total1 == 0

        # Check session2 is intact
        items2, total2 = conversation_repository.get_history(
            user_id="user1",
            session_id="session2",
            page=1,
            page_size=10
        )
        assert total2 == 1

    # Session Management Tests

    def test_upsert_session_creates_new(self, conversation_repository):
        """Test creating a new session."""
        result = conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456",
            title="Test Session"
        )

        assert result["user_id"] == "user123"
        assert result["session_id"] == "session456"
        assert result["title"] == "Test Session"
        assert result["message_count"] == 1
        assert result["created_at"] is not None

    def test_upsert_session_updates_existing(self, conversation_repository):
        """Test updating an existing session."""
        # Create session
        conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456",
            title="Original Title"
        )

        # Update session
        result = conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456"
        )

        # Message count should increment
        assert result["message_count"] == 2
        # Title should remain the same when not specified
        assert result["title"] == "Original Title"

    def test_upsert_session_auto_generates_title(self, conversation_repository):
        """Test that session title is auto-generated from first question."""
        # Add a conversation first
        conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question="What is the Bitcoin price today?",
            answer="BTC is $100,000",
            status="success",
            cycles_used=1
        )

        # Upsert session without title
        result = conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456"
        )

        # Should use first 50 chars of question
        assert result["title"] == "What is the Bitcoin price today?"

    def test_upsert_session_truncates_long_title(self, conversation_repository):
        """Test that auto-generated title is truncated at 50 chars."""
        long_question = "A" * 100

        conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question=long_question,
            answer="Answer",
            status="success",
            cycles_used=1
        )

        result = conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456"
        )

        assert len(result["title"]) == 53  # 50 + "..."
        assert result["title"].endswith("...")

    def test_get_session(self, conversation_repository):
        """Test retrieving session details."""
        # Create session
        conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456",
            title="Test Session"
        )

        # Get session
        result = conversation_repository.get_session(
            user_id="user123",
            session_id="session456"
        )

        assert result["user_id"] == "user123"
        assert result["session_id"] == "session456"
        assert result["title"] == "Test Session"

    def test_get_session_not_found(self, conversation_repository):
        """Test getting non-existent session raises error."""
        with pytest.raises(ValueError, match="Session not found"):
            conversation_repository.get_session(
                user_id="user123",
                session_id="nonexistent"
            )

    def test_list_sessions(self, conversation_repository):
        """Test listing all sessions for a user."""
        # Create multiple sessions
        for i in range(5):
            conversation_repository.upsert_session(
                user_id="user123",
                session_id=f"session{i}",
                title=f"Session {i}"
            )

        # List sessions
        sessions, total = conversation_repository.list_sessions(
            user_id="user123",
            page=1,
            page_size=10
        )

        assert len(sessions) == 5
        assert total == 5
        # Should be ordered by updated_at DESC
        assert sessions[0]["session_id"] == "session4"

    def test_list_sessions_pagination(self, conversation_repository):
        """Test session list pagination."""
        # Create 15 sessions
        for i in range(15):
            conversation_repository.upsert_session(
                user_id="user123",
                session_id=f"session{i}",
                title=f"Session {i}"
            )

        # Get page 1
        page1, total = conversation_repository.list_sessions(
            user_id="user123",
            page=1,
            page_size=10
        )

        # Get page 2
        page2, _ = conversation_repository.list_sessions(
            user_id="user123",
            page=2,
            page_size=10
        )

        assert len(page1) == 10
        assert len(page2) == 5
        assert total == 15

    def test_update_session_title(self, conversation_repository):
        """Test renaming a session."""
        # Create session
        conversation_repository.upsert_session(
            user_id="user123",
            session_id="session456",
            title="Original Title"
        )

        # Update title
        result = conversation_repository.update_session_title(
            user_id="user123",
            session_id="session456",
            title="New Title"
        )

        assert result["title"] == "New Title"

    def test_delete_session(self, conversation_repository):
        """Test deleting a session and all its conversations."""
        user_id = "user123"
        session_id = "session456"

        # Create session and add conversations
        conversation_repository.upsert_session(
            user_id=user_id,
            session_id=session_id,
            title="Test"
        )

        for i in range(3):
            conversation_repository.add_interaction(
                user_id=user_id,
                session_id=session_id,
                question=f"Q{i}",
                answer=f"A{i}",
                status="success",
                cycles_used=1
            )

        # Delete session
        conversation_repository.delete_session(user_id=user_id, session_id=session_id)

        # Verify session is deleted
        with pytest.raises(ValueError, match="Session not found"):
            conversation_repository.get_session(user_id=user_id, session_id=session_id)

        # Verify conversations are deleted
        items, total = conversation_repository.get_history(
            user_id=user_id,
            session_id=session_id,
            page=1,
            page_size=10
        )
        assert total == 0

    def test_row_to_dict_with_null_json(self, conversation_repository):
        """Test that _row_to_dict handles null/empty JSON fields correctly."""
        # Add interaction with minimal data
        result = conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question="Test",
            answer="Answer",
            status="success",
            cycles_used=1
            # No trace, plan_history, or execution_log
        )

        # Should have empty lists for JSON fields
        assert result["trace"] == []
        assert result["plan_history"] == []
        assert result["execution_log"] == []

    def test_multiple_users_isolation(self, conversation_repository):
        """Test that data for different users is properly isolated."""
        # Add data for user1
        conversation_repository.add_interaction(
            user_id="user1",
            session_id="session1",
            question="User1 Question",
            answer="User1 Answer",
            status="success",
            cycles_used=1
        )

        # Add data for user2
        conversation_repository.add_interaction(
            user_id="user2",
            session_id="session1",
            question="User2 Question",
            answer="User2 Answer",
            status="success",
            cycles_used=1
        )

        # Get history for user1
        items1, total1 = conversation_repository.get_history(
            user_id="user1",
            session_id="session1",
            page=1,
            page_size=10
        )

        # Get history for user2
        items2, total2 = conversation_repository.get_history(
            user_id="user2",
            session_id="session1",
            page=1,
            page_size=10
        )

        # Each user should only see their own data
        assert total1 == 1
        assert total2 == 1
        assert items1[0]["question"] == "User1 Question"
        assert items2[0]["question"] == "User2 Question"

    def test_status_field_mapping(self, conversation_repository):
        """Test that status field correctly maps to success/timeout flags."""
        # Add success interaction
        success_result = conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question="Q1",
            answer="A1",
            status="success",
            cycles_used=1
        )

        assert success_result["success"] is True
        assert success_result["timeout"] is False

        # Add timeout interaction
        timeout_result = conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question="Q2",
            answer="A2",
            status="timeout",
            cycles_used=3
        )

        assert timeout_result["success"] is False
        assert timeout_result["timeout"] is True

    def test_vietnamese_content_support(self, conversation_repository):
        """Test that Vietnamese text is properly stored and retrieved."""
        vietnamese_question = "Phân tích kỹ thuật BTC với các chỉ báo RSI và MACD"
        vietnamese_answer = "Giá BTC đang trong xu hướng tăng mạnh..."

        result = conversation_repository.add_interaction(
            user_id="user123",
            session_id="session456",
            question=vietnamese_question,
            answer=vietnamese_answer,
            status="success",
            cycles_used=1
        )

        assert result["question"] == vietnamese_question
        assert result["answer"] == vietnamese_answer

        # Retrieve and verify
        retrieved = conversation_repository.get_interaction(result["id"])
        assert retrieved["question"] == vietnamese_question
        assert retrieved["answer"] == vietnamese_answer