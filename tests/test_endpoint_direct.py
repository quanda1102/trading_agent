import asyncio
import sys
from trading_agent_tp.api.simple_agent_endpoints import SimpleChatRequest, simple_chat

async def test():
    try:
        request = SimpleChatRequest(
            question="test",
            user_id="default_user",
            session_id="default_session",
            use_memory=False
        )
        result = await simple_chat(request)
        print("Success!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())