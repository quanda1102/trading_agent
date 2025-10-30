"""
Test script for simple agent streaming functionality.

Tests:
1. Non-streaming mode (baseline)
2. Streaming mode with SSE events
3. Streaming with memory enabled
"""

import asyncio
import httpx
import json


BASE_URL = "http://localhost:8888"


async def test_non_streaming():
    """Test 1: Non-streaming mode (baseline)"""
    print("="*80)
    print("Test 1: Non-streaming Mode")
    print("="*80)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/simple/chat",
            json={
                "question": "What is 2+2?",
                "user_id": "test_user",
                "session_id": "test_stream_session",
                "use_memory": False,
                "streaming": False
            },
            timeout=60.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Non-streaming successful")
            print(f"Answer: {data['final_answer'][:100]}...")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)

    print()


async def test_streaming():
    """Test 2: Streaming mode with SSE events"""
    print("="*80)
    print("Test 2: Streaming Mode (SSE)")
    print("="*80)

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/simple/chat",
            json={
                "question": "Explain Bitcoin in one sentence",
                "user_id": "test_user",
                "session_id": "test_stream_session",
                "use_memory": False,
                "streaming": True
            },
            timeout=120.0
        ) as response:
            if response.status_code != 200:
                print(f"❌ Failed: {response.status_code}")
                content = await response.aread()
                print(content.decode())
                return

            print("✅ Streaming started, receiving events:\n")

            event_count = 0
            final_output = None

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    data_str = line[6:]  # Remove "data: " prefix

                    try:
                        event_data = json.loads(data_str)
                        event_type = event_data.get("event")

                        if event_type == "start":
                            print(f"🟢 Stream started")

                        elif event_type == "message":
                            content = event_data.get("data", {}).get("content", "")
                            print(f"📝 {content}", end="", flush=True)

                        elif event_type == "tool_call":
                            tool = event_data.get("tool", "unknown")
                            print(f"\n🔧 Tool call: {tool}")

                        elif event_type == "tool_call_output":
                            output = event_data.get("output", "")
                            print(f"   Output: {output[:100]}...")

                        elif event_type == "final_output":
                            final_output = event_data.get("data")
                            print(f"\n\n✅ Final output received ({len(final_output)} chars)")

                        elif event_type == "end":
                            print(f"🔴 Stream ended")

                        elif event_type == "error":
                            print(f"\n❌ Error: {event_data.get('message')}")

                    except json.JSONDecodeError:
                        print(f"⚠️  Invalid JSON: {data_str[:50]}")

            print(f"\n📊 Total events received: {event_count}")
            if final_output:
                print(f"📄 Final answer preview: {final_output[:200]}...")

    print()


async def test_streaming_with_memory():
    """Test 3: Streaming with memory enabled"""
    print("="*80)
    print("Test 3: Streaming with Memory")
    print("="*80)

    async with httpx.AsyncClient() as client:
        # First interaction
        print("First interaction: Setting context...")
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/simple/chat",
            json={
                "question": "My favorite crypto is Ethereum",
                "user_id": "memory_test_user",
                "session_id": "memory_stream_session",
                "use_memory": True,
                "streaming": True
            },
            timeout=120.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event_data = json.loads(line[6:])
                        if event_data.get("event") == "final_output":
                            print(f"✅ Context set")
                            break
                    except:
                        pass

        print("\nSecond interaction: Testing memory recall...")

        # Second interaction - test memory
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/simple/chat",
            json={
                "question": "What is my favorite crypto?",
                "user_id": "memory_test_user",
                "session_id": "memory_stream_session",
                "use_memory": True,
                "streaming": True
            },
            timeout=120.0
        ) as response:
            final_output = None
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event_data = json.loads(line[6:])

                        if event_data.get("event") == "message":
                            content = event_data.get("data", {}).get("content", "")
                            print(content, end="", flush=True)

                        elif event_data.get("event") == "final_output":
                            final_output = event_data.get("data")
                    except:
                        pass

            print("\n")
            if final_output and "ethereum" in final_output.lower():
                print("✅ SUCCESS: Agent remembered favorite crypto in streaming mode!")
            else:
                print("⚠️  Memory might not have worked (check full response)")
                if final_output:
                    print(f"Response: {final_output[:200]}")

    print()


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("Simple Agent Streaming Tests")
    print("="*80 + "\n")

    try:
        await test_non_streaming()
        await test_streaming()
        await test_streaming_with_memory()

        print("="*80)
        print("All tests completed!")
        print("="*80)

    except httpx.ConnectError:
        print("❌ Could not connect to backend. Make sure the server is running:")
        print("   uv run python main.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())