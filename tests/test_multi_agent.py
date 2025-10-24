"""
Quick test script for multi-agent system
"""

import asyncio
import sys
from trading_agent_tp.core.multi_agent_orchestrator import MultiAgentOrchestrator


async def test_system():
    """Test the multi-agent orchestration system."""

    print("="*80)
    print("TESTING MULTI-AGENT SYSTEM")
    print("="*80)

    orchestrator = MultiAgentOrchestrator()

    # Test query
    test_query = "Phân tích kỹ thuật BTC hiện tại"

    print(f"\n📝 Test Query: {test_query}")
    print("\n" + "="*80)

    try:
        result = await orchestrator.process_query(
            query=test_query,
            user_id="test_user",
            session_id="test_session",
            memory_context=None
        )

        print("\n" + "="*80)
        print("RESULT SUMMARY")
        print("="*80)
        print(f"Success: {result['success']}")
        print(f"Cycles Used: {result['cycles_used']}")
        print(f"Error: {result.get('error', 'None')}")
        print(f"Timeout: {result.get('timeout', False)}")

        if result['plan_history']:
            print(f"\nPlans Created: {len(result['plan_history'])}")
            for i, plan in enumerate(result['plan_history'], 1):
                print(f"  Cycle {plan['cycle']}: {len(plan['plan'])} tasks")

        if result['execution_log']:
            print(f"\nTasks Executed: {len(result['execution_log'])}")
            successful = sum(1 for log in result['execution_log'] if log['success'])
            print(f"  Successful: {successful}/{len(result['execution_log'])}")

        print("\n" + "="*80)
        print("FINAL ANSWER")
        print("="*80)
        print(result['final_answer'][:500])
        if len(result['final_answer']) > 500:
            print("... (truncated)")

        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)

        return result['success']

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)
