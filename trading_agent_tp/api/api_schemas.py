from pydantic import BaseModel

# Request schema for the trading agent
class trading_agent_request(BaseModel):
    question: str
    session_id: str = None
    streaming: bool = False
    user_id: str = "test"  # Can be chat_id in groups
    telegram_user_id: str = None  # Actual Telegram user ID of the requester