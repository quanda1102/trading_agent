import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8888/api/simple/chat",
                json={
                    "question": "test",
                    "user_id": "default_user",
                    "session_id": "default_session",
                    "use_memory": False
                },
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())