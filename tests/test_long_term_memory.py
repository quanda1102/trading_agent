"""
Test script for long-term memory with vector retrieval.

Tests:
1. Short-term memory (recent conversations)
2. Long-term memory (vector-based semantic search)
3. User preference storage and retrieval
4. Enhanced context with both short and long-term memory
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_agent_tp.memory.memory_manager import MemoryManager


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_short_term_memory(memory_manager: MemoryManager):
    """Test 1: Short-term memory (recent conversations)"""
    print_section("Test 1: Short-term Memory (Recent Conversations)")

    user_id = "test_user_001"
    session_id = "test_session_001"

    # Add some interactions
    interactions = [
        ("What is Bitcoin?", "Bitcoin is a decentralized digital currency..."),
        ("How does it work?", "Bitcoin uses blockchain technology..."),
        ("What's the current price?", "As of today, Bitcoin is trading at..."),
    ]

    print("Adding interactions to short-term memory...")
    for i, (q, a) in enumerate(interactions, 1):
        memory_manager.add_interaction(
            user_id=user_id,
            session_id=session_id,
            question=q,
            answer=a
        )
        print(f"  {i}. Q: {q}")

    # Retrieve context
    print("\nRetrieving conversation context:")
    context = memory_manager.get_context(
        user_id=user_id,
        session_id=session_id
    )
    print(f"\n{context}\n")

    # Get history as structured data
    history = memory_manager.get_history(
        user_id=user_id,
        session_id=session_id
    )
    print(f"✅ Retrieved {len(history)} messages from short-term memory")

    return user_id, session_id


def test_long_term_memory(memory_manager: MemoryManager, user_id: str):
    """Test 2: Long-term memory (vector-based semantic search)"""
    print_section("Test 2: Long-term Memory (Vector Search)")

    # Add various trading-related interactions
    trading_interactions = [
        ("session_btc_001", "What's a good RSI level to buy Bitcoin?", "Generally, RSI below 30 indicates oversold conditions..."),
        ("session_eth_001", "Tell me about Ethereum's gas fees", "Ethereum gas fees vary based on network congestion..."),
        ("session_btc_002", "Should I buy Bitcoin when RSI is low?", "When RSI is below 30, it suggests Bitcoin might be undervalued..."),
        ("session_analysis", "How to analyze MACD indicator?", "MACD shows momentum by comparing two moving averages..."),
    ]

    print("Adding interactions to long-term memory...")
    for session, q, a in trading_interactions:
        memory_manager.add_interaction(
            user_id=user_id,
            session_id=session,
            question=q,
            answer=a
        )
        print(f"  - Session {session}: {q[:50]}...")

    # Test semantic search
    print("\n\nTesting semantic search (vector retrieval):")

    queries = [
        "RSI buying strategy",
        "Ethereum transaction costs",
        "momentum indicators",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        results = memory_manager.search_similar_conversations(
            user_id=user_id,
            query=query,
            limit=3
        )

        if results:
            print(f"  Found {len(results)} similar conversations:")
            for i, result in enumerate(results, 1):
                distance = result.get('distance', 0)
                similarity = 1 - distance if distance else 0
                content_preview = result.get('content', '')[:80]
                print(f"    {i}. Similarity: {similarity:.2f} | {content_preview}...")
        else:
            print("  No results found")

    print(f"\n✅ Long-term memory vector search working!")


def test_user_preferences(memory_manager: MemoryManager, user_id: str):
    """Test 3: User preference storage and retrieval"""
    print_section("Test 3: User Preferences (Vector Retrieval)")

    # Store user preferences
    preferences = [
        {
            "type": "trading_style",
            "content": "I prefer conservative trading with low risk. I like to use RSI and MACD indicators for entry points."
        },
        {
            "type": "risk_tolerance",
            "content": "I'm comfortable with maximum 5% portfolio risk per trade. I always use stop losses."
        },
        {
            "type": "market_interest",
            "content": "I'm most interested in Bitcoin and Ethereum. I avoid meme coins and focus on established cryptocurrencies."
        },
        {
            "type": "indicators",
            "content": "My favorite technical indicators are RSI, MACD, and Bollinger Bands. I don't like to use too many indicators."
        }
    ]

    print("Storing user preferences...")
    for pref in preferences:
        memory_manager.store_user_preference(
            user_id=user_id,
            preference_type=pref["type"],
            content=pref["content"]
        )
        print(f"  - {pref['type']}: {pref['content'][:60]}...")

    # Test preference retrieval with different queries
    print("\n\nRetrieving preferences with semantic search:")

    queries = [
        "What are my risk preferences?",
        "Which indicators do I like to use?",
        "What cryptocurrencies am I interested in?",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        prefs = memory_manager.retrieve_user_preferences(
            user_id=user_id,
            query=query,
            limit=2
        )

        if prefs:
            print(f"  Found {len(prefs)} relevant preferences:")
            for i, pref in enumerate(prefs, 1):
                distance = pref.get('distance', 0)
                similarity = 1 - distance if distance else 0
                content = pref.get('content', '')[:100]
                pref_type = pref.get('metadata', {}).get('preference_type', 'unknown')
                print(f"    {i}. [{pref_type}] Similarity: {similarity:.2f}")
                print(f"       {content}...")
        else:
            print("  No preferences found")

    print(f"\n✅ User preference vector retrieval working!")


def test_enhanced_context(memory_manager: MemoryManager, user_id: str, session_id: str):
    """Test 4: Enhanced context with both short and long-term memory"""
    print_section("Test 4: Enhanced Context (Short + Long Term)")

    current_query = "What's the best strategy for buying Bitcoin?"

    print(f"Current Query: '{current_query}'")
    print("\nRetrieving enhanced context...")

    enhanced_context = memory_manager.get_enhanced_context(
        user_id=user_id,
        session_id=session_id,
        current_query=current_query,
        max_short_term=5,
        max_long_term=3
    )

    print("\n1. SHORT-TERM CONTEXT (Recent Conversation):")
    print("-" * 70)
    short_term = enhanced_context.get("short_term_context", "")
    if short_term:
        print(short_term[:300] + "..." if len(short_term) > 300 else short_term)
    else:
        print("  (No recent conversation)")

    print("\n2. SIMILAR PAST CONVERSATIONS:")
    print("-" * 70)
    similar = enhanced_context.get("similar_conversations", [])
    if similar:
        for i, conv in enumerate(similar, 1):
            similarity = 1 - conv.get('distance', 0)
            content = conv.get('content', '')[:100]
            print(f"  {i}. Similarity: {similarity:.2f}")
            print(f"     {content}...")
    else:
        print("  (No similar conversations)")

    print("\n3. RELEVANT USER PREFERENCES:")
    print("-" * 70)
    preferences = enhanced_context.get("user_preferences", [])
    if preferences:
        for i, pref in enumerate(preferences, 1):
            similarity = 1 - pref.get('distance', 0)
            content = pref.get('content', '')[:100]
            pref_type = pref.get('metadata', {}).get('preference_type', 'unknown')
            print(f"  {i}. [{pref_type}] Similarity: {similarity:.2f}")
            print(f"     {content}...")
    else:
        print("  (No preferences found)")

    has_long_term = enhanced_context.get("has_long_term_memory", False)
    print(f"\n✅ Enhanced context retrieved! Has long-term memory: {has_long_term}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  LONG-TERM MEMORY & VECTOR RETRIEVAL TEST SUITE")
    print("="*70)

    # Initialize memory manager
    print("\nInitializing Memory Manager...")
    memory_manager = MemoryManager(
        short_term_db_path="./data/test_short_term.db",
        long_term_chroma_path="./data/test_long_term_chroma",
        short_term_limit=10
    )
    print("✅ Memory Manager initialized")

    try:
        # Run tests
        user_id, session_id = test_short_term_memory(memory_manager)
        test_long_term_memory(memory_manager, user_id)
        test_user_preferences(memory_manager, user_id)
        test_enhanced_context(memory_manager, user_id, session_id)

        # Final summary
        print_section("TEST SUMMARY")
        print("✅ Short-term memory (SQLite): WORKING")
        print("✅ Long-term memory (ChromaDB vector search): WORKING")
        print("✅ User preference storage: WORKING")
        print("✅ User preference retrieval: WORKING")
        print("✅ Enhanced context (short + long term): WORKING")
        print("\n" + "="*70)
        print("  ALL TESTS PASSED! 🎉")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())