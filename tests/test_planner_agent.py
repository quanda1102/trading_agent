"""Test script for the planner-executor agent.

This script demonstrates how to use the planner-executor agent through the API.
"""

import requests
import json
from datetime import datetime

# API configuration
API_URL = "http://localhost:8888/api/v1/chat"
USER_ID = "test_user"


def test_planner_agent(question: str, session_id: str = None):
    """Test the planner-executor agent with a given question."""

    if session_id is None:
        session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    payload = {
        "user_id": USER_ID,
        "session_id": session_id,
        "question": question
    }

    print(f"\n{'='*80}")
    print(f"Testing Planner Agent")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print(f"Session ID: {session_id}")
    print(f"\nSending request...")

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()

        result = response.json()

        print(f"\n{'='*80}")
        print(f"Response:")
        print(f"{'='*80}")
        print(f"Status: {result.get('status')}")
        print(f"Agent Used: {result.get('agent_used')}")
        print(f"Agent Type: {result.get('agent_type')}")
        print(f"\nResponse Content:\n{result.get('response')}")

        # Print metadata if planner agent was used
        metadata = result.get('metadata', {})
        if metadata:
            print(f"\n{'='*80}")
            print(f"Execution Metadata:")
            print(f"{'='*80}")
            print(f"Cycles Used: {metadata.get('cycles_used')}")
            print(f"Timeout: {metadata.get('timeout')}")
            print(f"Error: {metadata.get('error')}")

            plan_history = metadata.get('plan_history', [])
            if plan_history:
                print(f"\nPlan History:")
                for i, plan_cycle in enumerate(plan_history, 1):
                    print(f"\n  Cycle {plan_cycle.get('cycle')}:")
                    for task in plan_cycle.get('plan', []):
                        print(f"    Task {task['id']}: {task['description']}")

            execution_log = metadata.get('execution_log', [])
            if execution_log:
                print(f"\nExecution Log:")
                for i, exec_item in enumerate(execution_log, 1):
                    status_icon = "✓" if exec_item.get('success') else "✗"
                    print(f"\n  {status_icon} Task {exec_item.get('task_id')} (Cycle {exec_item.get('cycle')}):")
                    print(f"    Description: {exec_item.get('task')}")
                    result_preview = exec_item.get('result', '')[:150]
                    print(f"    Result: {result_preview}...")

        print(f"\n{'='*80}\n")

        return result

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def test_routing():
    """Test that queries are correctly routed to different agents."""

    test_cases = [
        {
            "question": "Lập kế hoạch đầu tư BTC cho tháng tới",
            "expected_agent": "planner",
            "description": "Planning query (Vietnamese)"
        },
        {
            "question": "Create a trading strategy for ETH",
            "expected_agent": "planner",
            "description": "Planning query (English)"
        },
        {
            "question": "Phân tích kỹ thuật BTC",
            "expected_agent": "trading",
            "description": "Analysis query"
        },
        {
            "question": "What is Bitcoin?",
            "expected_agent": "conversational",
            "description": "General query"
        }
    ]

    print(f"\n{'#'*80}")
    print(f"# ROUTING TESTS")
    print(f"{'#'*80}\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        print(f"Expected: {test_case['expected_agent']}")

        result = test_planner_agent(
            test_case['question'],
            session_id=f"routing_test_{i}"
        )

        if result:
            actual_agent = result.get('agent_type')
            if actual_agent == test_case['expected_agent']:
                print(f"✓ PASS: Routed to {actual_agent}")
            else:
                print(f"✗ FAIL: Expected {test_case['expected_agent']}, got {actual_agent}")

        # Small delay between tests
        import time
        time.sleep(1)


def test_complex_planning():
    """Test complex multi-step planning."""

    complex_queries = [
        {
            "question": "Lập kế hoạch phân tích và giao dịch ETH trong 2 tuần, bao gồm phân tích kỹ thuật, quản lý vốn và lịch trình theo dõi",
            "description": "Complex multi-step plan"
        },
        {
            "question": "Tạo chiến lược đầu tư dài hạn cho BTC với các bước: phân tích xu hướng, xác định điểm vào, thiết lập stop-loss và take-profit",
            "description": "Long-term investment strategy"
        }
    ]

    print(f"\n{'#'*80}")
    print(f"# COMPLEX PLANNING TESTS")
    print(f"{'#'*80}\n")

    for i, test_case in enumerate(complex_queries, 1):
        print(f"\n{'='*80}")
        print(f"Complex Test {i}: {test_case['description']}")
        print(f"{'='*80}")

        result = test_planner_agent(
            test_case['question'],
            session_id=f"complex_test_{i}"
        )

        # Small delay between tests
        import time
        time.sleep(2)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PLANNER-EXECUTOR AGENT TEST SUITE")
    print("="*80)
    print("\nMake sure the API server is running: python trading_agent_tp/main.py")
    print("\nStarting tests in 3 seconds...")

    import time
    time.sleep(3)

    # Run tests
    test_routing()

    print("\n\nWaiting 5 seconds before complex tests...")
    time.sleep(5)

    test_complex_planning()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")