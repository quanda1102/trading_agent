"""
Test Suite for Pure Planner-Executor System

Tests the new architecture with database queries, code execution, and web search.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# API configuration
API_URL = "http://localhost:8888/api/v1/chat"
USER_ID = "test_user"


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}\n")


def print_result(result: Dict[str, Any]):
    """Print formatted test result."""
    print(f"Status: {result.get('status')}")
    print(f"\nResponse:\n{'-'*80}")
    print(result.get('response', 'No response'))
    print(f"{'-'*80}")

    metadata = result.get('metadata', {})
    if metadata:
        print(f"\nMetadata:")
        print(f"  Cycles Used: {metadata.get('cycles_used')}")
        print(f"  Tasks Completed: {metadata.get('tasks_completed')}")
        print(f"  Tasks Failed: {metadata.get('tasks_failed')}")
        print(f"  Timeout: {metadata.get('timeout')}")

        if metadata.get('error'):
            print(f"  Error: {metadata.get('error')}")

        # Show plan history
        plan_history = metadata.get('plan_history', [])
        if plan_history:
            print(f"\n  Plan History:")
            for cycle_plan in plan_history:
                print(f"\n    Cycle {cycle_plan.get('cycle')}:")
                for task in cycle_plan.get('plan', []):
                    print(f"      Task {task['id']}: {task['description']}")

        # Show execution log
        execution_log = metadata.get('execution_log', [])
        if execution_log:
            print(f"\n  Execution Log:")
            for log_entry in execution_log:
                status_icon = "✅" if log_entry.get('success') else "❌"
                print(f"    {status_icon} Task {log_entry.get('task_id')}: {log_entry.get('task')[:60]}...")
                if not log_entry.get('success'):
                    print(f"       Error: {log_entry.get('result')[:100]}")


def test_query(
    question: str,
    description: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a test query."""
    if session_id is None:
        session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print_section(description)
    print(f"Question: {question}")
    print(f"Session ID: {session_id}\n")

    payload = {
        "user_id": USER_ID,
        "session_id": session_id,
        "question": question
    }

    try:
        print("Sending request...")
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print_result(result)

        return result

    except requests.exceptions.Timeout:
        print("❌ Request timeout (>120s)")
        return {"status": "error", "error": "timeout"}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        return {"status": "error", "error": str(e)}

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return {"status": "error", "error": str(e)}


def test_database_queries():
    """Test database query functionality."""
    print_section("DATABASE QUERY TESTS")

    tests = [
        {
            "question": "Get latest 50 BTC prices from database",
            "description": "Test 1: Simple database query"
        },
        {
            "question": "Retrieve ETH volume data for last 100 records",
            "description": "Test 2: Volume data query"
        },
        {
            "question": "Show me all SOL trading data",
            "description": "Test 3: Comprehensive data query"
        }
    ]

    for i, test in enumerate(tests, 1):
        result = test_query(
            test["question"],
            test["description"],
            session_id=f"db_test_{i}"
        )
        time.sleep(2)


def test_technical_analysis():
    """Test technical analysis with code execution."""
    print_section("TECHNICAL ANALYSIS TESTS")

    tests = [
        {
            "question": "Phân tích kỹ thuật BTC: tính RSI, MACD và xác định xu hướng",
            "description": "Test 1: Vietnamese - Complete technical analysis"
        },
        {
            "question": "Calculate RSI(14) and MACD(12,26,9) for ETH and identify overbought/oversold conditions",
            "description": "Test 2: English - Indicator calculation"
        },
        {
            "question": "Analyze BTC price action, identify support/resistance levels, and predict short-term trend",
            "description": "Test 3: Price action analysis with prediction"
        }
    ]

    for i, test in enumerate(tests, 1):
        result = test_query(
            test["question"],
            test["description"],
            session_id=f"ta_test_{i}"
        )
        time.sleep(3)


def test_market_research():
    """Test web search for market research."""
    print_section("MARKET RESEARCH TESTS")

    tests = [
        {
            "question": "What are the latest Bitcoin news and market sentiment today?",
            "description": "Test 1: Latest news and sentiment"
        },
        {
            "question": "Search for Ethereum price predictions and analyst opinions",
            "description": "Test 2: Price predictions research"
        }
    ]

    for i, test in enumerate(tests, 1):
        result = test_query(
            test["question"],
            test["description"],
            session_id=f"research_test_{i}"
        )
        time.sleep(3)


def test_comprehensive_analysis():
    """Test comprehensive analysis combining all tools."""
    print_section("COMPREHENSIVE ANALYSIS TESTS")

    tests = [
        {
            "question": """Phân tích toàn diện BTC:
            1. Lấy dữ liệu giá 100 ngày gần nhất
            2. Tính các chỉ báo kỹ thuật (RSI, MACD, MA20, MA50)
            3. Xác định hỗ trợ và kháng cự
            4. Tìm tin tức mới nhất
            5. Đưa ra dự đoán và khuyến nghị
            """,
            "description": "Test 1: Complete BTC analysis (Vietnamese)"
        },
        {
            "question": """Create a comprehensive ETH trading plan:
            - Retrieve latest price data
            - Calculate technical indicators
            - Identify entry and exit points
            - Check market news and sentiment
            - Provide risk management recommendations
            """,
            "description": "Test 2: Trading plan creation (English)"
        }
    ]

    for i, test in enumerate(tests, 1):
        result = test_query(
            test["question"],
            test["description"],
            session_id=f"comprehensive_test_{i}"
        )
        time.sleep(5)


def test_error_handling():
    """Test error handling and recovery."""
    print_section("ERROR HANDLING TESTS")

    tests = [
        {
            "question": "Analyze INVALID_SYMBOL cryptocurrency",
            "description": "Test 1: Invalid symbol handling"
        },
        {
            "question": "Execute impossible calculation that will fail",
            "description": "Test 2: Execution failure handling"
        }
    ]

    for i, test in enumerate(tests, 1):
        result = test_query(
            test["question"],
            test["description"],
            session_id=f"error_test_{i}"
        )
        time.sleep(2)


def test_conversation_continuity():
    """Test conversation context and memory."""
    print_section("CONVERSATION CONTINUITY TESTS")

    session_id = "continuity_test"

    # First query
    result1 = test_query(
        "Analyze BTC price and calculate RSI",
        "Test 1: Initial BTC analysis",
        session_id=session_id
    )
    time.sleep(3)

    # Follow-up query (should use context)
    result2 = test_query(
        "Based on the previous analysis, what's your trading recommendation?",
        "Test 2: Follow-up using context",
        session_id=session_id
    )
    time.sleep(3)

    # Another follow-up
    result3 = test_query(
        "Compare this with ETH",
        "Test 3: Comparative analysis using context",
        session_id=session_id
    )


def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*80)
    print("PLANNER-EXECUTOR SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("\nMake sure:")
    print("1. API server is running: python main_new.py")
    print("2. Database is configured in .env")
    print("3. OpenAI API key is set")
    print("\nStarting tests in 5 seconds...")
    time.sleep(5)

    # Run test suites
    try:
        test_database_queries()
        print("\n⏸️  Waiting 10 seconds before next suite...")
        time.sleep(10)

        test_technical_analysis()
        print("\n⏸️  Waiting 10 seconds before next suite...")
        time.sleep(10)

        test_market_research()
        print("\n⏸️  Waiting 10 seconds before next suite...")
        time.sleep(10)

        test_comprehensive_analysis()
        print("\n⏸️  Waiting 10 seconds before next suite...")
        time.sleep(10)

        test_error_handling()
        print("\n⏸️  Waiting 10 seconds before next suite...")
        time.sleep(10)

        test_conversation_continuity()

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()