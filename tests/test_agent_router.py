"""
Test script for AgentRouter

This script demonstrates how the AgentRouter detects "Phân tích" keywords
and routes to the appropriate agent.
"""

from trading_agent_tp.core.agent_router import AgentRouter, AnalysisPatterns


def test_agent_routing():
    """Test various query patterns and their routing."""

    test_cases = [
        # Should route to Trading Agent (contains "Phân tích")
        ("Phân tích BTC", "trading"),
        ("phân tích BTC", "trading"),
        ("PHÂN TÍCH BTC", "trading"),
        ("Phân tích báo cáo kỹ thuật", "trading"),
        ("Tôi muốn phân tích thị trường", "trading"),
        ("Hãy phân tích cho tôi biểu đồ này", "trading"),
        ("phan tich BTC", "trading"),  # Without diacritics
        ("Phân  tích BTC", "trading"),  # Extra space

        # Should route to Conversational Agent (no "Phân tích")
        ("Giá Bitcoin hiện tại là bao nhiêu?", "conversational"),
        ("Xu hướng thị trường như thế nào?", "conversational"),
        ("Tôi muốn biết về BTC", "conversational"),
        ("Cho tôi thông tin về crypto", "conversational"),
        ("Hôm nay thị trường ra sao?", "conversational"),
    ]

    print("=" * 80)
    print("AGENT ROUTING TEST")
    print("=" * 80)
    print()

    for query, expected_route in test_cases:
        actual_route = AgentRouter.route(query)
        agent_name = AgentRouter.get_agent_name(query)
        status = "✓" if actual_route == expected_route else "✗"

        print(f"{status} Query: {query}")
        print(f"  Expected: {expected_route}")
        print(f"  Actual: {actual_route}")
        print(f"  Agent: {agent_name}")
        print()


def test_analysis_pattern_detection():
    """Test specific analysis pattern detection."""

    test_cases = [
        ("Phân tích kỹ thuật BTC", "technical"),
        ("Phân tích báo cáo tháng 10", "report"),
        ("Phân tích thị trường crypto", "market"),
        ("Phân tích giá Bitcoin", "general"),
        ("Giá Bitcoin hiện tại", "none"),
    ]

    print("=" * 80)
    print("ANALYSIS PATTERN DETECTION TEST")
    print("=" * 80)
    print()

    for query, expected_type in test_cases:
        actual_type = AnalysisPatterns.detect_analysis_type(query)
        status = "✓" if actual_type == expected_type else "✗"

        print(f"{status} Query: {query}")
        print(f"  Expected type: {expected_type}")
        print(f"  Actual type: {actual_type}")
        print()


def test_regex_pattern():
    """Test the regex pattern directly."""

    print("=" * 80)
    print("REGEX PATTERN TEST")
    print("=" * 80)
    print()

    test_strings = [
        "Phân tích BTC",
        "phân tích",
        "PHÂN TÍCH",
        "Tôi muốn phân tích",
        "phân tích cho tôi",
        "phan tich",  # Without diacritics
        "Phân  tích",  # Extra space
        "phântích",   # No space (should not match)
        "Giá Bitcoin",
        "Không có từ khóa",
    ]

    for test_str in test_strings:
        match = AgentRouter.ANALYSIS_PATTERN.search(test_str)
        result = "MATCH" if match else "NO MATCH"
        matched_text = f"'{match.group()}'" if match else "N/A"

        print(f"String: '{test_str}'")
        print(f"  Result: {result}")
        print(f"  Matched: {matched_text}")
        print()


if __name__ == "__main__":
    test_agent_routing()
    print("\n")
    test_analysis_pattern_detection()
    print("\n")
    test_regex_pattern()

    print("=" * 80)
    print("REGEX PATTERN DETAILS")
    print("=" * 80)
    print(f"Pattern: {AgentRouter.ANALYSIS_PATTERN.pattern}")
    print(f"Flags: IGNORECASE | UNICODE")
    print()
    print("Pattern explanation:")
    print("  \\b - Word boundary (start)")
    print("  (phân\\s*tích|phan\\s*tich) - Match 'phân tích' or 'phan tich' with optional spaces")
    print("  \\b - Word boundary (end)")
    print("  re.IGNORECASE - Case insensitive matching")
    print("  re.UNICODE - Unicode-aware matching")
    print("=" * 80)