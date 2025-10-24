#!/usr/bin/env python3
"""
Simple test script to verify the API imports and basic functionality
"""

import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all imports work correctly"""
    try:
        print("Testing imports...")

        # Test API schemas
        from trading_agent_tp.api.api_schemas import trading_agent_request
        print("✓ API schemas imported successfully")

        # Test agent
        from trading_agent_tp.core.conversational_agent import agent
        print("✓ Conversational agent imported successfully")

        # Test AI Memory
        from trading_agent_tp.services.ai_memory import AIMemory
        print("✓ AI Memory imported successfully")

        # Test storage adapters
        from trading_agent_tp.services.storage_sqlite import SQLiteStorage
        from trading_agent_tp.services.storage_chromadb import ChromaDBStorage
        from trading_agent_tp.services.storage_openai import OpenAIServices
        print("✓ Storage adapters imported successfully")

        # Test FastAPI app
        from main import app
        print("✓ FastAPI app imported successfully")

        print("\n✓ All imports successful!")
        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_api_schema():
    """Test API schema validation"""
    try:
        print("\nTesting API schema...")
        from trading_agent_tp.api.api_schemas import trading_agent_request

        # Create a valid request
        request = trading_agent_request(
            question="What is Bitcoin's price?",
            user_id="test_user"
        )

        print(f"✓ Created request: {request.question}")
        print(f"  User ID: {request.user_id}")
        print(f"  Session ID: {request.session_id}")

        return True

    except Exception as e:
        print(f"✗ Schema test error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Trading Agent API - Test Suite")
    print("=" * 60)

    all_passed = True

    # Run tests
    all_passed = test_imports() and all_passed
    all_passed = test_api_schema() and all_passed

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)