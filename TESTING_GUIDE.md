# Testing Guide

Comprehensive testing documentation for the trading-agent-tp project.

---

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing Tests](#writing-tests)
6. [Continuous Integration](#continuous-integration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This project uses **pytest** as the testing framework with comprehensive unit and integration tests covering:

- **Storage Services**: SQLite, ChromaDB, conversation repository
- **Core Components**: Multi-agent orchestrator, planner, executor
- **API Endpoints**: FastAPI routes and request/response validation
- **Agents**: Database, analysis, research, and report agents

### Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests for multiple components
- `@pytest.mark.slow`: Tests that take more than 5 seconds
- `@pytest.mark.requires_api`: Tests requiring OpenAI API key
- `@pytest.mark.requires_db`: Tests requiring database connection

---

## Test Structure

```
tests/
├── conftest.py                           # Pytest configuration and fixtures
├── test_storage_sqlite.py                # SQLite storage unit tests
├── test_conversation_repository.py       # Conversation repository unit tests
├── test_orchestrator_helpers.py          # Orchestrator helper methods tests
├── test_api.py                           # Basic API integration tests
├── test_multi_agent.py                   # Multi-agent system tests
├── test_chatgpt_features.py              # ChatGPT-like features tests
├── test_endpoint_direct.py               # Direct endpoint tests
├── test_full_system.py                   # Full system integration tests
├── test_long_term_memory.py              # Long-term memory tests
├── test_structured_planner.py            # Structured planner tests
├── test_agent_router.py                  # Agent routing tests
├── test_new_system.py                    # New system features tests
└── test_planner_agent.py                 # Planner agent tests
```

---

## Running Tests

### Prerequisites

```bash
# Install dependencies with test extras
uv sync --all-extras

# Or install test dependencies explicitly
uv pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with detailed output
uv run pytest -vv

# Run specific test file
uv run pytest tests/test_storage_sqlite.py

# Run specific test class
uv run pytest tests/test_storage_sqlite.py::TestSQLiteStorage

# Run specific test method
uv run pytest tests/test_storage_sqlite.py::TestSQLiteStorage::test_store_message
```

### Running by Marker

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run tests that don't require API
uv run pytest -m "not requires_api"

# Run fast tests only (exclude slow tests)
uv run pytest -m "not slow"
```

### Test Coverage

```bash
# Run tests with coverage report
uv run pytest --cov=trading_agent_tp --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=trading_agent_tp --cov-report=html

# View HTML report (opens in browser)
open htmlcov/index.html

# Generate XML coverage report (for CI/CD)
uv run pytest --cov=trading_agent_tp --cov-report=xml
```

### Parallel Execution

```bash
# Install pytest-xdist for parallel execution
uv pip install pytest-xdist

# Run tests in parallel (4 workers)
uv run pytest -n 4

# Run tests in parallel with auto-detection
uv run pytest -n auto
```

### Debugging Tests

```bash
# Run tests with Python debugger on failure
uv run pytest --pdb

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf

# Run failed tests first, then others
uv run pytest --ff

# Show local variables in tracebacks
uv run pytest -l

# Increase verbosity for debugging
uv run pytest -vv --tb=long
```

---

## Test Coverage

### Current Coverage Status

| Component | Coverage | Tests | Status |
|-----------|----------|-------|--------|
| **Storage Services** | ~85% | 40+ | ✅ Good |
| `storage_sqlite.py` | ~90% | 20 | ✅ Excellent |
| `conversation_repository.py` | ~85% | 30+ | ✅ Good |
| **Core Components** | ~60% | 50+ | ⚠️ Needs Improvement |
| `multi_agent_orchestrator.py` | ~55% | 40 | ⚠️ Needs More Tests |
| `planner_agent_enhanced.py` | ~40% | 10 | ❌ Low Coverage |
| **API Endpoints** | ~70% | 15 | ⚠️ Needs Improvement |
| **Agents** | ~30% | 10 | ❌ Low Coverage |
| `database_agent.py` | ~25% | 5 | ❌ Needs Tests |
| `analysis_agent.py` | ~25% | 3 | ❌ Needs Tests |
| **Overall** | ~55% | 150+ | ⚠️ Target: 80%+ |

### Coverage Goals

- **Unit Tests**: Aim for 80%+ coverage on individual components
- **Integration Tests**: Cover all critical user workflows
- **Edge Cases**: Test error conditions, timeouts, invalid inputs
- **Performance**: Add benchmarks for slow operations

---

## Writing Tests

### Test Structure Guidelines

Follow the **Arrange-Act-Assert** pattern:

```python
def test_example(fixture):
    # Arrange: Set up test data and conditions
    user_id = "test_user"
    session_id = "test_session"

    # Act: Execute the operation being tested
    result = some_function(user_id, session_id)

    # Assert: Verify the expected outcome
    assert result["success"] is True
    assert result["user_id"] == user_id
```

### Using Fixtures

Fixtures are defined in `conftest.py` and automatically available to all tests:

```python
def test_with_temp_db(temp_db_path):
    """Test uses temporary database path fixture."""
    storage = SQLiteStorage(db_path=temp_db_path)
    # temp_db_path is automatically cleaned up after test
    storage.store_message("user1", "session1", "user", "Test")
    assert len(storage.get_messages("user1", "session1")) == 1

def test_with_mock_runner(mock_runner):
    """Test uses mocked runner fixture."""
    orchestrator = MultiAgentOrchestrator()
    orchestrator.runner = mock_runner
    # Runner is automatically mocked
    result = await orchestrator.process_query("Test", "user1", "session1")
```

### Available Fixtures

| Fixture | Description | Scope |
|---------|-------------|-------|
| `temp_db_path` | Temporary database file path | Function |
| `temp_chroma_path` | Temporary ChromaDB directory | Function |
| `sqlite_storage` | SQLiteStorage instance | Function |
| `conversation_repository` | ConversationRepository instance | Function |
| `sample_conversation_data` | Sample conversation dict | Function |
| `sample_plan` | Sample plan dict | Function |
| `sample_agent_response` | Mocked agent response | Function |
| `mock_openai_client` | Mocked OpenAI client | Function |
| `mock_runner` | Mocked agent runner | Function |
| `orchestrator_with_mocks` | Orchestrator with mocked deps | Function |
| `test_client` | FastAPI test client | Function |
| `sample_ohlcv_data` | Sample OHLCV data | Function |

### Testing Async Functions

Use `pytest-asyncio` for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await some_async_function()
    assert result is not None
```

### Mocking External Dependencies

Use `unittest.mock` for mocking:

```python
from unittest.mock import Mock, patch, AsyncMock

def test_with_mock():
    """Test with mocked dependency."""
    with patch('module.function') as mock_func:
        mock_func.return_value = "mocked value"
        result = call_function_that_uses_it()
        assert result == "mocked value"
        mock_func.assert_called_once()

@pytest.mark.asyncio
async def test_async_with_mock():
    """Test async function with mock."""
    with patch('module.async_function') as mock_func:
        mock_func.return_value = AsyncMock(return_value="result")
        result = await call_async_function()
        assert result == "result"
```

### Parametrized Tests

Test multiple scenarios efficiently:

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("short term", "database"),
    ("calculate RSI", "analysis"),
    ("search news", "research"),
    ("generate report", "report"),
])
def test_agent_identification(input, expected):
    """Test agent identification with multiple inputs."""
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator._identify_agent_for_task(input)
    assert result == expected
```

### Testing Exceptions

```python
import pytest

def test_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="invalid input"):
        function_that_raises("bad input")

def test_does_not_raise():
    """Test that function doesn't raise exception."""
    try:
        function_that_might_raise("good input")
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")
```

### Testing Database Operations

```python
def test_database_transaction(conversation_repository):
    """Test database transaction rollback."""
    # Start with clean state
    initial_count, _ = conversation_repository.get_history(
        user_id="user1",
        session_id="session1",
        page=1,
        page_size=10
    )

    try:
        # Attempt operation that should fail
        conversation_repository.add_interaction(
            user_id=None,  # Invalid
            session_id="session1",
            question="Test",
            answer="Test",
            status="success",
            cycles_used=1
        )
        pytest.fail("Should have raised exception")
    except Exception:
        pass

    # Verify database state unchanged
    final_count, _ = conversation_repository.get_history(
        user_id="user1",
        session_id="session1",
        page=1,
        page_size=10
    )
    assert final_count == initial_count
```

---

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
# Good: Test creates its own data
def test_isolated(sqlite_storage):
    sqlite_storage.store_message("user1", "session1", "user", "Test")
    messages = sqlite_storage.get_messages("user1", "session1")
    assert len(messages) == 1

# Bad: Test depends on data from previous test
def test_depends_on_previous(sqlite_storage):
    # Assumes data from previous test exists
    messages = sqlite_storage.get_messages("user1", "session1")
    assert len(messages) > 0  # Fragile!
```

### 2. Clear Test Names

Use descriptive test names:

```python
# Good: Describes what is being tested
def test_store_message_with_empty_content():
    """Test that storing message with empty content succeeds."""
    ...

# Bad: Unclear what is being tested
def test_store():
    ...
```

### 3. Test One Thing

Each test should verify one behavior:

```python
# Good: Tests one specific behavior
def test_clear_session_removes_all_messages(conversation_repository):
    """Test that clear_session removes all messages for the session."""
    # Add messages
    # Clear session
    # Verify all removed

# Bad: Tests multiple behaviors
def test_session_operations(conversation_repository):
    # Creates session
    # Adds messages
    # Lists sessions
    # Clears session
    # Updates title
    # Too much in one test!
```

### 4. Use Fixtures Wisely

```python
# Good: Fixture provides reusable test data
@pytest.fixture
def sample_user():
    return {
        "user_id": "test_user",
        "session_id": "test_session"
    }

def test_with_fixture(sample_user):
    result = process_user(sample_user)
    assert result["user_id"] == sample_user["user_id"]

# Bad: Duplicating test data in every test
def test_without_fixture():
    user = {"user_id": "test_user", "session_id": "test_session"}
    result = process_user(user)
    ...
```

### 5. Cleanup After Tests

```python
# Good: Cleanup is automatic with fixture
@pytest.fixture
def temp_file():
    file_path = create_temp_file()
    yield file_path
    cleanup_temp_file(file_path)  # Always runs

# Good: Use context managers
def test_with_context():
    with temporary_database() as db:
        # Test code
        pass
    # Database is automatically cleaned up
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync --all-extras

    - name: Run tests with coverage
      run: uv run pytest --cov=trading_agent_tp --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'trading_agent_tp'
# Solution: Install package in development mode
uv pip install -e .
```

#### 2. Fixture Not Found

```bash
# Error: fixture 'temp_db_path' not found
# Solution: Ensure conftest.py is in tests directory
# Check that pytest is finding conftest.py:
pytest --fixtures
```

#### 3. Async Tests Failing

```bash
# Error: RuntimeError: Event loop is closed
# Solution: Use pytest-asyncio
uv pip install pytest-asyncio

# Add to pyproject.toml:
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

#### 4. Database Locked Errors

```bash
# Error: database is locked
# Solution: Ensure each test uses unique database path
# Use temp_db_path fixture instead of shared database
```

#### 5. Tests Passing Locally but Failing in CI

```bash
# Common causes:
# - Different Python versions
# - Missing environment variables
# - File system differences
# - Timezone differences

# Solutions:
# - Use datetime.now(timezone.utc) instead of datetime.now()
# - Mock external dependencies
# - Use Path objects instead of string paths
```

### Debug Mode

```bash
# Run with maximum verbosity
uv run pytest -vv --tb=long --log-cli-level=DEBUG

# Run single test in debug mode
uv run pytest tests/test_storage_sqlite.py::TestSQLiteStorage::test_store_message -vv --pdb
```

---

## Performance Testing

### Benchmarking Example

```python
import pytest
import time

def test_performance_benchmark(benchmark):
    """Benchmark a function."""
    result = benchmark(expensive_function, arg1, arg2)
    assert result is not None

@pytest.mark.slow
def test_concurrent_requests():
    """Test system under load."""
    import concurrent.futures

    def make_request():
        # Simulate request
        return api_call()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]

    assert len(results) == 100
    assert all(r["success"] for r in results)
```

---

## Next Steps

1. **Increase Coverage**: Target 80%+ coverage
   ```bash
   # Identify untested code
   uv run pytest --cov=trading_agent_tp --cov-report=term-missing
   ```

2. **Add Integration Tests**: Test complete workflows
3. **Add Performance Tests**: Benchmark critical operations
4. **Add Load Tests**: Test system under concurrent load
5. **Document Test Cases**: Add docstrings to all tests

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Last Updated**: 2025-10-27