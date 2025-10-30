"""Simple Agent API Endpoints

FastAPI endpoints exposing the single-agent workflow for comparison with the
multi-agent orchestration pattern.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from agents import ItemHelpers

from ..agents.simple_agent import simple_agent
from ..utils.file_proxy import collect_file_refs, replace_sandbox_links
from ..services.simple_agent_sessions import get_session_manager
from ..storage import ConversationRepository
from ..services.chat_search import ChatSearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simple", tags=["simple-agent"])

runner = Runner()
session_manager = get_session_manager()
conversation_repository = ConversationRepository()
chat_search = ChatSearchService()


class SimpleChatRequest(BaseModel):
    """Request payload mirroring the multi-agent ChatRequest."""

    question: str = Field(..., description="User's question in Vietnamese or English")
    user_id: str = Field(default="default_user", description="User identifier")
    session_id: str = Field(default="default_session", description="Session identifier")
    use_memory: bool = Field(default=False, description="Whether to use conversation memory")
    streaming: bool = Field(default=False, description="Whether to stream the response")


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


async def _stream_agent_response(question: str, session=None, user_id: str = None, session_id: str = None):
    """
    Stream agent response using Server-Sent Events (SSE).

    Args:
        question: User's question
        session: Optional session for memory
        user_id: User identifier for persistence
        session_id: Session identifier for persistence

    Returns:
        StreamingResponse with text/event-stream
    """
    result = runner.run_streamed(simple_agent, question, session=session)

    async def generator():
        final_output = None
        try:
            yield f"data: {json.dumps({'event': 'start', 'message': 'Stream started'})}\n\n"

            async for event in result.stream_events():
                # Handle text delta events (streaming response content)
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield f"data: {json.dumps({'event': 'message', 'data': {'content': event.data.delta}})}\n\n"

                # Handle agent updates (if using multiple agents)
                elif event.type == 'agent_updated_stream_event':
                    yield f"data: {json.dumps({'event': 'agent_updated', 'agent': event.new_agent.name})}\n\n"
                    continue

                # Handle run item events (tool calls, outputs)
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        tool_name = getattr(event.item, 'name', 'unknown')
                        yield f"data: {json.dumps({'event': 'tool_call', 'tool': tool_name})}\n\n"

                    elif event.item.type == "tool_call_output_item":
                        output_str = str(event.item.output)
                        # Truncate large outputs for streaming
                        if len(output_str) > 500:
                            output_str = output_str[:500] + "... (truncated)"
                        yield f"data: {json.dumps({'event': 'tool_call_output', 'output': output_str})}\n\n"

                    elif event.item.type == "message_output_item":
                        message_output = ItemHelpers.text_message_output(event.item)
                        yield f"data: {json.dumps({'event': 'message_output', 'output': message_output})}\n\n"

            # Send final output
            final_output = _extract_answer(result)

            # Process file proxy for final output
            file_refs = []
            if hasattr(result, 'raw_responses') and result.raw_responses:
                raw_response = result.raw_responses[0]
                file_refs = collect_file_refs(raw_response)

            if file_refs:
                final_output = replace_sandbox_links(final_output, file_refs)

            yield f"data: {json.dumps({'event': 'final_output', 'data': final_output})}\n\n"
            yield f"data: {json.dumps({'event': 'end', 'message': 'Stream ended'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
        finally:
            # Persist conversation after streaming completes (if we have user/session info)
            if final_output and user_id and session_id:
                try:
                    interaction = conversation_repository.add_interaction(
                        user_id=user_id,
                        session_id=session_id,
                        question=question,
                        answer=final_output,
                        trace=[],
                        plan_history=[],
                        execution_log=[],
                        status="success",
                        cycles_used=1,
                    )

                    # Update session metadata
                    conversation_repository.upsert_session(
                        user_id=user_id,
                        session_id=session_id,
                        agent_type="simple_agent"
                    )

                    # Index conversation for semantic search
                    chat_search.index_conversation(
                        interaction_id=interaction["id"],
                        user_id=user_id,
                        session_id=session_id,
                        question=question,
                        answer=final_output,
                        created_at=interaction["created_at"]
                    )

                    logger.info(f"Simple agent streaming conversation persisted: interaction_id={interaction['id']}")
                except Exception as persistence_error:
                    logger.error(
                        "Failed to persist streaming conversation: %s",
                        persistence_error,
                        exc_info=True
                    )

    return StreamingResponse(
        content=generator(),
        status_code=200,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/chat")
async def simple_chat(request: SimpleChatRequest):
    """Run a one-shot analysis using the simple agent pipeline."""

    try:
        # Get session if memory is enabled
        session = None
        if request.use_memory:
            session = session_manager.get_session(request.user_id, request.session_id)
            logger.info(f"Using session for {request.user_id}/{request.session_id}")
        else:
            logger.debug("Memory disabled - running without session")

        # Handle streaming mode
        if request.streaming:
            return await _stream_agent_response(
                request.question,
                session,
                user_id=request.user_id,
                session_id=request.session_id
            )

        # Non-streaming mode
        agent_result = await runner.run(simple_agent, request.question, session=session)
        answer = _extract_answer(agent_result)

        # Process file proxy - extract file references from raw responses
        file_refs = []
        if hasattr(agent_result, 'raw_responses') and agent_result.raw_responses:
            # Get the first raw response (similar to test/main.py line 66)
            raw_response = agent_result.raw_responses[0]
            # Extract file citations from annotations
            file_refs = collect_file_refs(raw_response)

        # Replace sandbox links with proxy URLs
        if file_refs:
            answer = replace_sandbox_links(answer, file_refs)

        # Persist conversation history to unified repository
        try:
            interaction = conversation_repository.add_interaction(
                user_id=request.user_id,
                session_id=request.session_id,
                question=request.question,
                answer=answer,
                trace=[],  # Simple agent doesn't have trace
                plan_history=[],
                execution_log=[],
                status="success",
                cycles_used=1,
            )

            # Update session metadata (auto-generates title from first message)
            conversation_repository.upsert_session(
                user_id=request.user_id,
                session_id=request.session_id,
                agent_type="simple_agent"
            )

            # Index conversation for semantic search
            chat_search.index_conversation(
                interaction_id=interaction["id"],
                user_id=request.user_id,
                session_id=request.session_id,
                question=request.question,
                answer=answer,
                created_at=interaction["created_at"]
            )

            logger.info(f"Simple agent conversation persisted: interaction_id={interaction['id']}")
        except Exception as persistence_error:
            logger.error(
                "Failed to persist simple agent conversation: %s",
                persistence_error,
                exc_info=True
            )
            # Don't fail the request if persistence fails

        return SimpleChatResponse(
            success=True,
            final_answer=answer,
            created_at=datetime.utcnow(),
            tool_outputs=_extract_tool_outputs(agent_result),
        )
    except Exception as exc:  # pragma: no cover
        logger.error(f"Simple agent failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simple agent failed: {exc}") from exc


@router.delete("/session/{user_id}/{session_id}")
async def clear_session(user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Clear conversation memory for a specific session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        Success confirmation
    """
    try:
        # Clear from simple agent session manager (AdvancedSQLiteSession)
        session_manager.clear_session(user_id, session_id)
        
        # Also clear from unified conversation repository
        conversation_repository.clear_session(user_id=user_id, session_id=session_id)
        
        # Clear from search index
        chat_search.delete_conversation_index(user_id=user_id, session_id=session_id)
        
        logger.info(f"Cleared simple agent session: {user_id}/{session_id}")
        
        return {
            "success": True,
            "message": f"Session cleared for {user_id}/{session_id}"
        }
    except Exception as exc:
        logger.error(f"Failed to clear session: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {exc}") from exc


@router.get("/session/{user_id}/{session_id}")
async def get_session_info(user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get information about a session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        Session information
    """
    try:
        info = session_manager.get_session_info(user_id, session_id)
        return {
            "success": True,
            "session_info": info
        }
    except Exception as exc:
        logger.error(f"Failed to get session info: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {exc}") from exc


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check for the simple agent API."""

    return {
        "status": "healthy",
        "service": "trading-agent-simple",
        "model": simple_agent.name,
        "memory_enabled": True,
        "streaming_enabled": True,
    }
