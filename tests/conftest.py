"""
Pytest configuration and fixtures for trading-agent-tp tests.
"""

import os
import pytest
import asyncio
import sqlite3
import tempfile
import shutil
from typing import Generator, AsyncGenerator
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Set test environment
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key-placeholder")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file path."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_conversations.db")
    yield db_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_chroma_path() -> Generator[str, None, None]:
    """Create a temporary ChromaDB directory path."""
    temp_dir = tempfile.mkdtemp()
    chroma_path = os.path.join(temp_dir, "test_chroma")
    yield chroma_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sqlite_storage(temp_db_path):
    """Create a SQLiteStorage instance with temporary database."""
    from trading_agent_tp.services.storage_sqlite import SQLiteStorage

    storage = SQLiteStorage(db_path=temp_db_path)
    yield storage
    # Cleanup happens via temp_db_path fixture


@pytest.fixture
def conversation_repository(temp_db_path):
    """Create a ConversationRepository instance with temporary database."""
    from trading_agent_tp.storage.conversation_repository import ConversationRepository

    repo = ConversationRepository(db_path=temp_db_path)
    yield repo
    # Cleanup happens via temp_db_path fixture


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "question": "Phân tích BTC ngắn hạn",
        "answer": "BTC đang trong xu hướng tăng...",
        "trace": '{"events": []}',
        "plan_history": '{"plans": []}',
        "execution_log": '{"logs": []}',
        "status": "success",
        "cycles_used": 2
    }


@pytest.fixture
def sample_plan():
    """Sample plan data for testing."""
    return {
        "plan": [
            {
                "id": 1,
                "description": "Retrieve BTC price data from database",
                "agent": "database",
                "depends_on": [],
                "loop_back": True,
                "required_confidence": 0.8
            },
            {
                "id": 2,
                "description": "Analyze BTC technical indicators",
                "agent": "analysis",
                "depends_on": [1],
                "loop_back": True,
                "required_confidence": 0.7
            },
            {
                "id": 3,
                "description": "Generate Vietnamese report",
                "agent": "report",
                "depends_on": [1, 2],
                "loop_back": False,
                "required_confidence": 0.9
            }
        ],
        "estimated_cycles": 2
    }


@pytest.fixture
def sample_agent_response():
    """Sample agent response for testing."""
    return Mock(
        final_output="Sample agent response content",
        content="Sample agent response content",
        text="Sample agent response content"
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock_client:
        # Mock embeddings
        mock_embeddings = Mock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        mock_client.return_value.embeddings = mock_embeddings

        # Mock chat completions
        mock_chat = Mock()
        mock_chat.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Mocked response"))]
        )
        mock_client.return_value.chat.completions = mock_chat

        yield mock_client.return_value


@pytest.fixture
def mock_runner():
    """Mock Runner for agent execution."""
    async def mock_run(agent, input_text):
        return Mock(
            final_output=f"Mocked response for: {input_text[:50]}",
            content=f"Mocked response for: {input_text[:50]}"
        )

    runner = Mock()
    runner.run = AsyncMock(side_effect=mock_run)
    return runner


@pytest.fixture
def mock_database_tool_response():
    """Mock database tool response."""
    return {
        "status": "success",
        "record_count": 100,
        "data": [
            {
                "symbol": "btc",
                "open": 100000,
                "high": 101000,
                "low": 99000,
                "close": 100500,
                "volume": 1000,
                "close_time": "2025-10-27T10:00:00Z"
            }
        ] * 100
    }


@pytest.fixture
def orchestrator_with_mocks(mock_runner):
    """Create MultiAgentOrchestrator with mocked dependencies."""
    from trading_agent_tp.core.multi_agent_orchestrator import MultiAgentOrchestrator

    orchestrator = MultiAgentOrchestrator()
    orchestrator.runner = mock_runner
    return orchestrator


@pytest.fixture
async def test_client():
    """Create a test client for API endpoints."""
    from fastapi.testclient import TestClient
    from main_multi_agent import app

    client = TestClient(app)
    yield client


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing."""
    return [
        {
            "symbol": "btc",
            "interval": "1h",
            "open_time": "2025-10-27T09:00:00Z",
            "close_time": "2025-10-27T10:00:00Z",
            "open": 100000.0,
            "high": 101000.0,
            "low": 99000.0,
            "close": 100500.0,
            "volume": 1500.5,
            "quote_volume": 150000000.0,
            "trades": 5000,
            "taker_buy_volume": 750.0,
            "taker_buy_quote_volume": 75000000.0
        }
        for i in range(100)
    ]


@pytest.fixture
def cleanup_test_db():
    """Cleanup any test database files after tests."""
    yield
    # Cleanup test databases
    test_files = [
        "test_*.db",
        "test_*.db-shm",
        "test_*.db-wal"
    ]
    for pattern in test_files:
        for file in Path(".").glob(pattern):
            try:
                file.unlink()
            except Exception:
                pass


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for multiple components"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that take more than 5 seconds"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require OpenAI API key"
    )
    config.addinivalue_line(
        "markers", "requires_db: Tests that require database connection"
    )