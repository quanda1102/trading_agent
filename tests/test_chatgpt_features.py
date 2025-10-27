"""
Test script for ChatGPT-like features in trading-agent-tp.

Tests session management, search, and chat history endpoints.
"""

import requests
import time
import uuid
from datetime import datetime


class ChatGPTFeaturesTester:
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.user_id = f"test_user_{int(time.time())}"
        self.session_id = str(uuid.uuid4())

        print(f"\n{'='*70}")
        print(f"ChatGPT Features Test Suite")
        print(f"{'='*70}")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test User ID: {self.user_id}")
        print(f"Test Session ID: {self.session_id}")
        print(f"{'='*70}\n")

    def test_health_check(self):
        """Test 1: Health check"""
        print("Test 1: Health Check")
        print("-" * 70)

        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Status: {data.get('status')}")
                print(f"✅ Agents Loaded: {', '.join(data.get('agents_loaded', []))}")
                print(f"✅ Orchestrator Ready: {data.get('orchestrator_ready')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_create_conversations(self):
        """Test 2: Create multiple conversations"""
        print("\nTest 2: Create Multiple Conversations")
        print("-" * 70)

        questions = [
            "What is Bitcoin?",
            "Explain RSI indicator",
            "How to use MACD?",
        ]

        try:
            for i, question in enumerate(questions, 1):
                print(f"\n  Conversation {i}: {question}")

                response = requests.post(
                    f"{self.api_url}/chat",
                    json={
                        "question": question,
                        "user_id": self.user_id,
                        "session_id": self.session_id,
                        "use_memory": True
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ Success: {response.status_code}")
                    print(f"  ✅ Interaction ID: {data.get('interaction_id')}")
                    print(f"  ✅ Answer Preview: {data.get('final_answer', '')[:100]}...")
                else:
                    print(f"  ❌ Failed: {response.status_code}")
                    print(f"  ❌ Error: {response.text}")
                    return False

                time.sleep(1)  # Rate limiting

            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_list_sessions(self):
        """Test 3: List sessions"""
        print("\nTest 3: List Sessions")
        print("-" * 70)

        try:
            response = requests.get(
                f"{self.api_url}/sessions",
                params={
                    "user_id": self.user_id,
                    "page": 1,
                    "page_size": 20
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                sessions = data.get("sessions", [])

                print(f"✅ Status Code: {response.status_code}")
                print(f"✅ Total Sessions: {data.get('total')}")
                print(f"✅ Sessions Returned: {len(sessions)}")
                print(f"✅ Has More: {data.get('has_more')}")

                if sessions:
                    session = sessions[0]
                    print(f"\n  First Session:")
                    print(f"    - ID: {session.get('session_id')}")
                    print(f"    - Title: {session.get('title')}")
                    print(f"    - Message Count: {session.get('message_count')}")
                    print(f"    - Created: {session.get('created_at')}")
                    print(f"    - Updated: {session.get('updated_at')}")

                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_get_session_details(self):
        """Test 4: Get session details"""
        print("\nTest 4: Get Session Details")
        print("-" * 70)

        try:
            response = requests.get(
                f"{self.api_url}/sessions/{self.session_id}",
                params={"user_id": self.user_id},
                timeout=10
            )

            if response.status_code == 200:
                session = response.json()
                print(f"✅ Status Code: {response.status_code}")
                print(f"✅ Session ID: {session.get('session_id')}")
                print(f"✅ Title: {session.get('title')}")
                print(f"✅ Message Count: {session.get('message_count')}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_rename_session(self):
        """Test 5: Rename session"""
        print("\nTest 5: Rename Session")
        print("-" * 70)

        new_title = f"Test Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        try:
            response = requests.patch(
                f"{self.api_url}/sessions/{self.session_id}",
                params={
                    "user_id": self.user_id,
                    "title": new_title
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status Code: {response.status_code}")
                print(f"✅ Success: {data.get('success')}")
                print(f"✅ New Title: {data['session'].get('title')}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_get_chat_history(self):
        """Test 6: Get chat history"""
        print("\nTest 6: Get Chat History")
        print("-" * 70)

        try:
            response = requests.get(
                f"{self.api_url}/chat/history",
                params={
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "page": 1,
                    "page_size": 10
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                print(f"✅ Status Code: {response.status_code}")
                print(f"✅ Total Messages: {data.get('total')}")
                print(f"✅ Page: {data.get('page')}")
                print(f"✅ Items Returned: {len(items)}")

                if items:
                    print(f"\n  Recent messages:")
                    for i, item in enumerate(items[:3], 1):
                        print(f"    {i}. Q: {item.get('question')[:50]}...")
                        print(f"       A: {item.get('answer', '')[:50]}...")

                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_search_conversations(self):
        """Test 7: Search conversations"""
        print("\nTest 7: Search Conversations (Semantic Search)")
        print("-" * 70)

        search_query = "technical indicators"

        try:
            response = requests.get(
                f"{self.api_url}/search/conversations",
                params={
                    "query": search_query,
                    "user_id": self.user_id,
                    "limit": 5
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                print(f"✅ Status Code: {response.status_code}")
                print(f"✅ Query: {data.get('query')}")
                print(f"✅ Results Found: {data.get('count')}")

                if results:
                    print(f"\n  Top Results:")
                    for i, result in enumerate(results, 1):
                        print(f"    {i}. Question: {result.get('question')[:50]}...")
                        print(f"       Similarity: {result.get('similarity_score', 0):.2f}")
                        print(f"       Session: {result.get('session_id')}")

                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_delete_session(self):
        """Test 8: Delete session"""
        print("\nTest 8: Delete Session")
        print("-" * 70)

        # First create a new session to delete
        temp_session_id = str(uuid.uuid4())

        print(f"  Creating temporary session: {temp_session_id}")

        # Create a conversation
        requests.post(
            f"{self.api_url}/chat",
            json={
                "question": "Temporary question",
                "user_id": self.user_id,
                "session_id": temp_session_id,
                "use_memory": True
            },
            timeout=30
        )

        time.sleep(1)

        # Now delete it
        try:
            response = requests.delete(
                f"{self.api_url}/sessions/{temp_session_id}",
                params={"user_id": self.user_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status Code: {response.status_code}")
                print(f"✅ Success: {data.get('success')}")
                print(f"✅ Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        tests = [
            self.test_health_check,
            self.test_create_conversations,
            self.test_list_sessions,
            self.test_get_session_details,
            self.test_rename_session,
            self.test_get_chat_history,
            self.test_search_conversations,
            self.test_delete_session,
        ]

        results = []

        for test in tests:
            try:
                result = test()
                results.append((test.__name__, result))
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append((test.__name__, False))

        # Print summary
        print(f"\n{'='*70}")
        print("Test Summary")
        print(f"{'='*70}")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print(f"{'='*70}\n")

        return passed == total


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print(" ChatGPT Features Test Suite ")
    print("="*70)
    print("\nMake sure the server is running:")
    print("  cd /path/to/trading-agent-tp")
    print("  uv run uvicorn main_multi_agent:app --reload --port 8888")
    print("\nPress Enter to start tests...")
    input()

    tester = ChatGPTFeaturesTester()

    try:
        success = tester.run_all_tests()

        if success:
            print("\n🎉 All tests passed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed. Please check the output above.")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())