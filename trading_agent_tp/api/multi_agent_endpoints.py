"""
Multi-Agent API Endpoints

FastAPI endpoints for multi-agent trading analysis system.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
import logging

from ..core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..storage import ConversationRepository
from ..services.chat_search import ChatSearchService
from ..utils.file_proxy import replace_sandbox_links

try:
    from ..memory.memory_manager import MemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("MemoryManager not available - memory features disabled")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["multi-agent"])

# Initialize orchestrator, memory manager, and search service
orchestrator = MultiAgentOrchestrator()
memory_manager = MemoryManager() if MEMORY_AVAILABLE else None
conversation_repository = ConversationRepository()
chat_search = ChatSearchService()


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., description="User's question in Vietnamese or English")
    user_id: str = Field(default="default_user", description="User identifier")
    session_id: str = Field(default="default_session", description="Session identifier")
    use_memory: bool = Field(default=True, description="Whether to use conversation memory")


class TraceEvent(BaseModel):
    """Timeline event describing planner/agent behaviour."""
    id: str
    type: Literal["plan", "action", "final", "error"]
    cycle: int
    agent: str
    status: Literal["success", "failed", "timeout"]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool
    final_answer: str
    plan_history: List[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]
    agent_results: Dict[str, Optional[List[Dict[str, Any]]]]
    cycles_used: int
    trace: List[TraceEvent] = Field(default_factory=list)
    interaction_id: Optional[int] = None
    created_at: Optional[datetime] = None
    error: Optional[str] = None
    timeout: bool = False
    response: Optional[str] = None  # Backwards compatibility for older clients

    @validator("plan_history", "execution_log", pre=True)
    def ensure_iterables(cls, value: Any) -> List[Dict[str, Any]]:
        return value or []


class ChatHistoryEntry(ChatResponse):
    """A stored conversation turn with metadata for history listings."""
    id: int
    user_id: str
    session_id: str
    question: str
    answer: Optional[str] = None
    status: Literal["success", "failed", "timeout"]
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Paginated chat history response."""
    items: List[ChatHistoryEntry]
    total: int
    page: int
    page_size: int


class MemorySummary(BaseModel):
    """Memory summary model."""
    conversation_count: int
    last_interaction: Optional[str]
    context_summary: Optional[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agents_loaded: List[str]
    orchestrator_ready: bool


# Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint with multi-agent orchestration.

    Processes user questions through specialized agents:
    - DatabaseAgent: Data retrieval and validation
    - AnalysisAgent: Technical analysis with indicators
    - ResearchAgent: Web research and fact-checking
    - ReportAgent: Vietnamese structured output formatting

    Example:
        ```json
        {
            "question": "Phân tích kỹ thuật BTC hiện tại",
            "user_id": "user123",
            "session_id": "session456",
            "use_memory": true
        }
        ```
    """
    try:
        logger.info(f"Received question from user {request.user_id}: {request.question[:100]}")

        # Retrieve conversation memory if enabled
        memory_context = None
        if request.use_memory and memory_manager:
            memory_context = memory_manager.get_context(
                user_id=request.user_id,
                session_id=request.session_id
            )
            logger.info(f"Retrieved memory context: {len(memory_context) if memory_context else 0} chars")

        # Process query through multi-agent orchestrator
        result = await orchestrator.process_query(
            query=request.question,
            user_id=request.user_id,
            session_id=request.session_id,
            memory_context=memory_context
        )

        # Collect file references from all agent raw responses
        file_refs = []
        agent_results = result.get("agent_results", {})
        for agent_type, agent_data in agent_results.items():
            if agent_data:  # agent_data is a list of task results
                for task_result in agent_data:
                    raw_response = task_result.get("raw_response")
                    if raw_response:
                        # Import collect_file_refs from file_proxy utils
                        from ..utils.file_proxy import collect_file_refs
                        task_refs = collect_file_refs(raw_response)
                        file_refs.extend(task_refs)

        logger.info(f"Collected {len(file_refs)} file references from agent responses")

        # Replace sandbox links with proxy URLs
        if result.get("final_answer") and file_refs:
            result["final_answer"] = replace_sandbox_links(
                text=result["final_answer"],
                refs=file_refs,
                backend_base=None  # Uses default from environment
            )
            logger.info("Replaced sandbox links in final answer")

        status_label: Literal["success", "failed", "timeout"]
        if result.get("success"):
            status_label = "success"
        elif result.get("timeout"):
            status_label = "timeout"
        else:
            status_label = "failed"

        # Save to memory if successful
        if request.use_memory and result["success"] and memory_manager:
            memory_manager.add_interaction(
                user_id=request.user_id,
                session_id=request.session_id,
                question=request.question,
                answer=result["final_answer"]
            )
            logger.info("Interaction saved to memory")

        # Persist conversation history
        try:
            interaction = conversation_repository.add_interaction(
                user_id=request.user_id,
                session_id=request.session_id,
                question=request.question,
                answer=result.get("final_answer", ""),
                trace=result.get("trace", []),
                plan_history=result.get("plan_history", []),
                execution_log=result.get("execution_log", []),
                status=status_label,
                cycles_used=result.get("cycles_used", 0),
            )

            # Update session metadata (auto-generates title from first message)
            conversation_repository.upsert_session(
                user_id=request.user_id,
                session_id=request.session_id,
                agent_type="multi_agent"
            )

            # Index conversation for semantic search
            chat_search.index_conversation(
                interaction_id=interaction["id"],
                user_id=request.user_id,
                session_id=request.session_id,
                question=request.question,
                answer=result.get("final_answer", ""),
                created_at=interaction["created_at"]
            )

            result["interaction_id"] = interaction["id"]
            result["created_at"] = interaction["created_at"]
            result["trace"] = interaction["trace"]
            result["plan_history"] = interaction["plan_history"]
            result["execution_log"] = interaction["execution_log"]
        except Exception as persistence_error:
            logger.error(
                "Failed to persist conversation history: %s",
                persistence_error,
                exc_info=True
            )

        result.setdefault("response", result.get("final_answer", ""))

        logger.info(
            f"Query processed successfully in {result['cycles_used']} cycles. "
            f"Success: {result['success']}"
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history_endpoint(
    user_id: str = Query(..., description="User identifier"),
    session_id: str = Query(..., description="Session identifier"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Return the persisted conversation history for a session."""
    try:
        records, total = conversation_repository.get_history(
            user_id=user_id,
            session_id=session_id,
            page=page,
            page_size=page_size,
        )

        entries = [ChatHistoryEntry(**record) for record in records]

        return ChatHistoryResponse(
            items=entries,
            total=total,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Error fetching chat history: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching chat history: {exc}"
        )


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint (future implementation).

    Will provide real-time updates as agents complete tasks.
    """
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented. Use /api/v1/chat for now."
    )


@router.get("/memory/{user_id}/{session_id}", response_model=MemorySummary)
async def get_memory_endpoint(user_id: str, session_id: str):
    """
    Get conversation memory summary for a user session.

    Returns:
        - Number of conversations
        - Last interaction timestamp
        - Context summary
    """
    if not memory_manager:
        raise HTTPException(
            status_code=503,
            detail="Memory features not available - MemoryManager not configured"
        )

    try:
        context = memory_manager.get_context(user_id=user_id, session_id=session_id)
        history = memory_manager.get_history(user_id=user_id, session_id=session_id)

        return MemorySummary(
            conversation_count=len(history),
            last_interaction=history[-1]["timestamp"] if history else None,
            context_summary=context[:200] + "..." if context and len(context) > 200 else context
        )

    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving memory: {str(e)}"
        )


@router.delete("/memory/{user_id}/{session_id}")
async def clear_memory_endpoint(user_id: str, session_id: str):
    """
    Clear conversation memory and persisted history for a user session.

    Useful for starting fresh conversations.
    """
    try:
        if memory_manager:
            memory_manager.clear_session(user_id=user_id, session_id=session_id)
            logger.info(f"Cleared in-memory context for user {user_id}, session {session_id}")
        else:
            logger.info("MemoryManager not configured; skipping in-memory clear")

        conversation_repository.clear_session(user_id=user_id, session_id=session_id)
        logger.info("Cleared stored history for user %s, session %s", user_id, session_id)

        return {
            "success": True,
            "message": f"Conversation history cleared for user {user_id}, session {session_id}"
        }

    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing memory: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Verifies all agents and orchestrator are loaded correctly.
    """
    try:
        agents_loaded = list(orchestrator.agents.keys())

        return HealthResponse(
            status="healthy",
            agents_loaded=agents_loaded,
            orchestrator_ready=True
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            agents_loaded=[],
            orchestrator_ready=False
        )


@router.get("/agents")
async def list_agents():
    """
    List all available specialized agents and their capabilities.

    Returns detailed information about each agent's role and tools.
    """
    agents_info = {
        "database": {
            "name": "DatabaseAgent",
            "model": "gpt-4o-mini",
            "specialization": "Data retrieval and validation",
            "tools": ["database_query_tool"],
            "capabilities": [
                "Fetch OHLCV data from database",
                "Validate data quality",
                "Cross-check data consistency",
                "Smart SQL query generation"
            ]
        },
        "analysis": {
            "name": "AnalysisAgent",
            "model": "gpt-4o",
            "specialization": "Technical analysis",
            "tools": ["CodeInterpreterTool"],
            "capabilities": [
                "Calculate RSI, MACD, Bollinger Bands",
                "Identify support and resistance levels",
                "Detect candlestick patterns",
                "Statistical analysis",
                "Trend identification"
            ]
        },
        "research": {
            "name": "ResearchAgent",
            "model": "gpt-4o-mini",
            "specialization": "Web research and fact-checking",
            "tools": ["WebSearchTool"],
            "capabilities": [
                "Search latest crypto news",
                "Analyze market sentiment",
                "Fact-check information from multiple sources",
                "Track regulatory updates",
                "Monitor social sentiment"
            ]
        },
        "report": {
            "name": "ReportAgent",
            "model": "gpt-4o",
            "specialization": "Vietnamese structured output formatting",
            "tools": [],
            "capabilities": [
                "Generate Vietnamese trading reports",
                "Format with emojis and tables",
                "Create actionable trading strategies",
                "Synthesize multi-agent results",
                "Provide risk warnings and disclaimers"
            ]
        }
    }

    return {
        "total_agents": len(agents_info),
        "agents": agents_info,
        "orchestration": {
            "max_cycles": orchestrator.MAX_CYCLES,
            "coordination_strategy": "Task-based intelligent delegation"
        }
    }


@router.get("/sessions")
async def list_sessions_endpoint(
    user_id: str = Query(..., description="User identifier"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type: 'multi_agent' or 'simple_agent'"),
):
    """
    List all chat sessions for a user (ChatGPT-like session list).

    Returns sessions ordered by most recent activity with auto-generated titles.
    Supports both multi-agent and simple-agent sessions in a unified list.

    Examples:
        GET /api/v1/sessions?user_id=user123&page=1&page_size=20
        GET /api/v1/sessions?user_id=user123&agent_type=simple_agent
        GET /api/v1/sessions?user_id=user123&agent_type=multi_agent
    """
    try:
        sessions, total = conversation_repository.list_sessions(
            user_id=user_id,
            page=page,
            page_size=page_size,
            agent_type=agent_type
        )

        return {
            "sessions": sessions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total,
            "agent_type_filter": agent_type
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Error listing sessions: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing sessions: {exc}"
        )


@router.get("/sessions/{session_id}")
async def get_session_endpoint(
    session_id: str,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Get detailed information about a specific session.

    Returns session metadata including title, message count, and timestamps.

    Example:
        GET /api/v1/sessions/session123?user_id=user123
    """
    try:
        session = conversation_repository.get_session(
            user_id=user_id,
            session_id=session_id
        )
        return session

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error getting session: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session: {exc}"
        )


@router.patch("/sessions/{session_id}")
async def update_session_endpoint(
    session_id: str,
    user_id: str = Query(..., description="User identifier"),
    title: str = Query(..., description="New session title"),
):
    """
    Update session title (rename conversation).

    Allows users to customize the auto-generated conversation title.

    Example:
        PATCH /api/v1/sessions/session123?user_id=user123&title=Bitcoin Analysis

    Request body:
        ```json
        {
            "title": "My Bitcoin Trading Strategy"
        }
        ```
    """
    try:
        session = conversation_repository.update_session_title(
            user_id=user_id,
            session_id=session_id,
            title=title
        )
        return {
            "success": True,
            "message": "Session title updated successfully",
            "session": session
        }

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error updating session: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating session: {exc}"
        )


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(
    session_id: str,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Delete a session and all its conversations (ChatGPT-like delete).

    This will permanently remove the session and all associated chat history.

    Example:
        DELETE /api/v1/sessions/session123?user_id=user123
    """
    try:
        # Delete from database
        conversation_repository.delete_session(
            user_id=user_id,
            session_id=session_id
        )

        # Delete from search index
        chat_search.delete_conversation_index(
            user_id=user_id,
            session_id=session_id
        )

        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully"
        }

    except Exception as exc:
        logger.error("Error deleting session: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {exc}"
        )


@router.get("/search/conversations")
async def search_conversations_endpoint(
    query: str = Query(..., description="Search query"),
    user_id: str = Query(..., description="User identifier"),
    session_id: Optional[str] = Query(None, description="Optional session filter"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Search conversations using semantic similarity (ChatGPT-like search).

    Uses ChromaDB for vector-based semantic search across all conversations.
    Finds conversations by meaning, not just exact text match.

    Example:
        GET /api/v1/search/conversations?query=bitcoin%20analysis&user_id=user123&limit=10
    """
    try:
        results = chat_search.search_conversations(
            query=query,
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "user_id": user_id,
            "session_filter": session_id
        }

    except Exception as exc:
        logger.error("Error searching conversations: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching conversations: {exc}"
        )


@router.post("/analyze")
async def quick_analysis_endpoint(
    symbol: str = "BTC",
    analysis_type: str = "technical"
):
    """
    Quick analysis endpoint for specific cryptocurrencies.

    Parameters:
        - symbol: Cryptocurrency symbol (BTC, ETH, SOL, etc.)
        - analysis_type: Type of analysis (technical, fundamental, sentiment)

    This is a convenience endpoint that constructs an appropriate query
    and processes it through the multi-agent system.
    """
    # Construct query based on analysis type
    queries = {
        "technical": f"Phân tích kỹ thuật {symbol} hiện tại với các chỉ báo RSI, MACD, và MA",
        "fundamental": f"Phân tích cơ bản {symbol}: tin tức, sự kiện, và xu hướng thị trường",
        "sentiment": f"Phân tích tâm lý thị trường {symbol} từ tin tức và mạng xã hội",
        "full": f"Phân tích toàn diện {symbol}: kỹ thuật, tin tức, và khuyến nghị giao dịch"
    }

    query = queries.get(analysis_type, queries["technical"])

    request = ChatRequest(
        question=query,
        user_id="quick_analysis",
        session_id=f"{symbol}_{analysis_type}",
        use_memory=False
    )

    return await chat_endpoint(request)
