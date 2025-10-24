#!/usr/bin/env python3
"""Test script to check structured planner output."""

import asyncio
import json
from agents import Runner
from trading_agent_tp.core.planner_agent_structured import planner_agent_structured

async def main():
    print("🧪 Testing Structured Planner Output")
    print("=" * 70)

    query = "Phân tích BTC ngắn hạn"
    print(f"Query: {query}\n")

    runner = Runner()
    result = await runner.run(planner_agent_structured, query)

    print("📊 Result type:", type(result))
    print("📊 Final output type:", type(result.final_output))
    print()

    # Check if it's a Pydantic model
    if hasattr(result.final_output, 'model_dump'):
        print("✅ Output is a Pydantic model!")
        output_dict = result.final_output.model_dump()
        print("Converted to dict:")
        print(json.dumps(output_dict, indent=2))
    elif isinstance(result.final_output, dict):
        print("✅ Output is already a dict!")
        print(json.dumps(result.final_output, indent=2))
    elif isinstance(result.final_output, str):
        print("⚠️  Output is a string (not structured)!")
        print(f"String length: {len(result.final_output)} characters")
        print("String content:")
        print(result.final_output)  # Print full output

        # Try to parse it as JSON
        try:
            import json
            parsed = json.loads(result.final_output)
            print("\n✅ But it's valid JSON!")
            print("Parsed successfully:")
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parsing failed: {e}")
    else:
        print("❌ Unknown output type!")
        print("Output:", result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
