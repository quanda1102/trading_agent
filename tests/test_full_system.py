#!/usr/bin/env python3
"""Test script to verify the full multi-agent system with structured planner."""

import asyncio
import json
from trading_agent_tp.core.multi_agent_orchestrator import MultiAgentOrchestrator

async def main():
    print("🧪 Testing Full Multi-Agent System")
    print("=" * 70)

    orchestrator = MultiAgentOrchestrator()

    query = "Phân tích BTC ngắn hạn"
    print(f"Query: {query}\n")

    try:
        result = await orchestrator.process_query(
            query=query,
            user_id="test",
            session_id="test123"
        )

        print("=" * 70)
        print("📊 RESULT")
        print("=" * 70)
        print(f"Success: {result['success']}")
        print(f"Cycles used: {result['cycles_used']}")

        if result['success']:
            print("\n✅ Query succeeded!")
            print("\nFinal Answer:")
            print(result['final_answer'][:500])

            print("\nPlan History:")
            for i, plan in enumerate(result['plan_history'], 1):
                print(f"  Cycle {i}: {len(plan.get('plan', []))} tasks")
        else:
            print("\n❌ Query failed!")
            print("Error:", result.get('error', 'Unknown error'))

        print("\n" + "=" * 70)
        print("TRACE EVENTS")
        print("=" * 70)
        for event in result['trace'][:5]:  # Show first 5 events
            print(f"  {event['type']:10s} | {event['agent']:15s} | {event['status']}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())