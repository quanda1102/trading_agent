"""Simple Agent API Endpoints

FastAPI endpoints exposing the single-agent workflow for comparison with the
multi-agent orchestration pattern.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents import Runner

from ..agents.simple_agent import simple_agent

router = APIRouter(prefix="/api/simple", tags=["simple-agent"])

runner = Runner()


class SimpleChatRequest(BaseModel):
    """Request payload mirroring the multi-agent ChatRequest."""

    question: str = Field(..., description="User's question in Vietnamese or English")
    user_id: str = Field(default="default_user", description="User identifier")
    session_id: str = Field(default="default_session", description="Session identifier")
    use_memory: bool = Field(default=False, description="(Ignored) Memory not used in simple agent")


class SimpleChatResponse(BaseModel):
    """Response model for simple agent."""

    success: bool
    final_answer: str
    created_at: datetime
    tool_outputs: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


def _extract_answer(agent_result: Any) -> str:
    """Normalise runner result to a string answer."""

    if hasattr(agent_result, "final_output") and agent_result.final_output:
        return str(agent_result.final_output)
    if hasattr(agent_result, "content") and agent_result.content:
        return str(agent_result.content)
    if hasattr(agent_result, "text") and agent_result.text:
        return str(agent_result.text)
    return str(agent_result)


def _extract_tool_outputs(agent_result: Any) -> Optional[List[Dict[str, Any]]]:
    """Collect tool outputs for debugging/inspection."""

    outputs = []
    for attr in ("tool_outputs", "new_items", "raw_responses"):
        value = getattr(agent_result, attr, None)
        if value:
            try:
                # Convert to string to ensure JSON serialization
                outputs.append({"attribute": attr, "value": str(value)})
            except Exception:  # pragma: no cover
                pass
    return outputs or None


@router.post("/chat", response_model=SimpleChatResponse)
async def simple_chat(request: SimpleChatRequest) -> SimpleChatResponse:
    """Run a one-shot analysis using the simple agent pipeline."""

    try:
        agent_result = await runner.run(simple_agent, request.question)
        answer = _extract_answer(agent_result)

        return SimpleChatResponse(
            success=True,
            final_answer=answer,
            created_at=datetime.utcnow(),
            tool_outputs=_extract_tool_outputs(agent_result),
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Simple agent failed: {exc}") from exc


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check for the simple agent API."""

    return {
        "status": "healthy",
        "service": "trading-agent-simple",
        "model": simple_agent.name,
    }
