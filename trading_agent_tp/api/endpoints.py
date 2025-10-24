"""
Legacy API Endpoints

Basic trading agent endpoints for backward compatibility.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..core.conversational_agent import agent
from ..services.ai_memory import AIMemory
from ..services.storage_sqlite import SQLiteStorage
from ..services.storage_chromadb import ChromaDBStorage
from ..services.storage_openai import OpenAIServices
from agents import Runner
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/v1", tags=["legacy"])

# Initialize components
runner = Runner()

# Initialize AI Memory with storage adapters
ai_memory = AIMemory.create_with_adapters(
    short_term=SQLiteStorage(db_path="./data/short_term_memory.db"),
    long_term=ChromaDBStorage(chroma_path="./data/chroma_db"),
    ai_services=OpenAIServices(api_key=os.getenv("OPENAI_API_KEY", "")),
    short_term_limit=10
)


class TradingAgentRequest(BaseModel):
    """Request model for trading agent."""
    question: str
    user_id: str = "default_user"
    session_id: str = "default_session"
    use_memory: bool = True


class TradingAgentResponse(BaseModel):
    """Response model for trading agent."""
    success: bool
    answer: str
    error: Optional[str] = None


async def get_session_memory(user_id: str, session_id: str, n: int = 5) -> str:
    """
    Get conversation memory for a session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        n: Number of recent messages to retrieve
        
    Returns:
        Conversation context as string
    """
    try:
        memory_context = ai_memory.get_context(user_id, session_id, n)
        return memory_context
    except Exception as e:
        logging.error(f"Error retrieving memory: {e}")
        return ""


@router.post("/chat", response_model=TradingAgentResponse)
async def chat(request: TradingAgentRequest):
    """
    Main chat endpoint for trading analysis.
    
    Processes user questions through the conversational agent.
    """
    try:
        # Get conversation memory if enabled
        memory_context = None
        if request.use_memory:
            memory_context = await get_session_memory(
                request.user_id, 
                request.session_id
            )
        
        # Prepare input with memory context
        if memory_context:
            agent_input = f"Previous conversation:\n{memory_context}\n\nCurrent question: {request.question}"
        else:
            agent_input = request.question
        
        # Run conversational agent
        response = await runner.run(agent, agent_input)
        
        # Extract answer
        if hasattr(response, "content"):
            answer = str(response.content) if response.content else ""
        elif hasattr(response, "text"):
            answer = str(response.text)
        else:
            answer = str(response)
        
        # Save to memory if successful
        if request.use_memory and answer:
            ai_memory.add_interaction(
                user_id=request.user_id,
                session_id=request.session_id,
                question=request.question,
                answer=answer
            )
        
        return TradingAgentResponse(
            success=True,
            answer=answer
        )
        
    except Exception as e:
        logging.error(f"Error processing chat request: {e}")
        return TradingAgentResponse(
            success=False,
            answer="",
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "trading-agent-tp",
        "version": "1.0.0"
    }


@router.get("/memory/{user_id}/{session_id}")
async def get_memory(user_id: str, session_id: str):
    """Get conversation memory for a session."""
    try:
        context = ai_memory.get_context(user_id, session_id)
        history = ai_memory.get_history(user_id, session_id)
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "context": context,
            "history_count": len(history),
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{user_id}/{session_id}")
async def clear_memory(user_id: str, session_id: str):
    """Clear conversation memory for a session."""
    try:
        ai_memory.clear_session(user_id, session_id)
        return {
            "success": True,
            "message": f"Memory cleared for user {user_id}, session {session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
