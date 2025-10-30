"""
Test script for simple agent memory functionality.

This script tests the newly implemented memory support for the simple agent.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_agent_tp.services.simple_agent_sessions import get_session_manager
from trading_agent_tp.agents.simple_agent import simple_agent
from agents import Runner


async def test_memory():
    """Test memory functionality for simple agent."""

    print("="*80)
    print("Testing Simple Agent Memory Functionality")
    print("="*80)

    # Initialize
    session_manager = get_session_manager()
    runner = Runner()

    user_id = "test_user"
    session_id = "test_session_001"

    print(f"\n1. Creating session for {user_id}/{session_id}")
    session = session_manager.get_session(user_id, session_id)
    print(f"   ✓ Session created: {session.session_id}")

    # First interaction
    print("\n2. First interaction (with memory):")
    question1 = "My name is John and I like Bitcoin"
    print(f"   User: {question1}")

    result1 = await runner.run(simple_agent, question1, session=session)
    answer1 = str(result1.final_output if hasattr(result1, 'final_output') else result1)
    print(f"   Agent: {answer1[:200]}...")

    # Second interaction - test if agent remembers
    print("\n3. Second interaction (testing memory recall):")
    question2 = "What is my name?"
    print(f"   User: {question2}")

    result2 = await runner.run(simple_agent, question2, session=session)
    answer2 = str(result2.final_output if hasattr(result2, 'final_output') else result2)
    print(f"   Agent: {answer2[:200]}...")

    # Check if memory works
    if "john" in answer2.lower():
        print("\n   ✅ SUCCESS: Agent remembered the user's name!")
    else:
        print("\n   ⚠️  WARNING: Agent might not have remembered (check full response)")

    # Test without memory
    print("\n4. Test without session (no memory):")
    question3 = "What is my name?"
    print(f"   User: {question3}")

    result3 = await runner.run(simple_agent, question3)  # No session
    answer3 = str(result3.final_output if hasattr(result3, 'final_output') else result3)
    print(f"   Agent: {answer3[:200]}...")

    if "john" not in answer3.lower():
        print("\n   ✅ SUCCESS: Without session, agent doesn't have access to previous context")
    else:
        print("\n   ⚠️  Note: Agent response without session")

    # Get session info
    print("\n5. Session information:")
    info = session_manager.get_session_info(user_id, session_id)
    print(f"   Session key: {info['session_key']}")
    print(f"   Database exists: {info['exists']}")
    print(f"   Database path: {info['db_path']}")
    print(f"   Cached in memory: {info['cached']}")

    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_memory())