from ..agents.alert_agent import agent
from agents import Runner
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["alert"])
class Request(BaseModel):
    question: str = Field(..., description="User's question in Vietnamese or English")

@router.post("/alert")
async def alert(request: Request):
    response = await Runner.run(agent, request.question)
    return response.final_output




