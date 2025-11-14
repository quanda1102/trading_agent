"""
Multi-Agent Trading System - Main Application

FastAPI application with specialized agents for comprehensive trading analysis.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from trading_agent_tp.api.multi_agent_endpoints import router as multi_agent_router
from trading_agent_tp.api.simple_agent_endpoints import router as simple_agent_router
from trading_agent_tp.api.file_proxy_endpoints import router as file_proxy_router
from trading_agent_tp.api.alert_agent_endpoints import router as alert_agent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Trading Analysis System",
    description="""
    Advanced cryptocurrency trading analysis system powered by specialized AI agents:

    ## Agents

    - **DatabaseAgent**: Data retrieval and validation
    - **AnalysisAgent**: Technical analysis with RSI, MACD, MA, Bollinger Bands
    - **ResearchAgent**: Web research and fact-checking
    - **ReportAgent**: Vietnamese structured output formatting

    ## Features

    - Intelligent task delegation to specialized agents
    - Comprehensive technical analysis
    - Real-time market research
    - Vietnamese language support
    - Conversation memory management
    - Structured trading reports with emojis and tables

    ## Example Usage

    ```python
    import requests

    response = requests.post("http://localhost:8000/api/v1/chat", json={
        "question": "Phân tích kỹ thuật BTC hiện tại",
        "user_id": "trader123",
        "session_id": "session456",
        "use_memory": true
    })

    print(response.json()["final_answer"])
    ```
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(multi_agent_router)
app.include_router(simple_agent_router)
app.include_router(file_proxy_router)
app.include_router(alert_agent_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Multi-Agent Trading Analysis System",
        "version": "2.0.0",
        "description": "AI-powered cryptocurrency trading analysis with specialized agents",
        "endpoints": {
            "chat": "/api/v1/chat",
            "quick_analysis": "/api/v1/analyze",
            "agents_info": "/api/v1/agents",
            "health": "/api/v1/health",
            "memory": "/api/v1/memory/{user_id}/{session_id}",
            "simple_chat": "/api/simple/chat",
            "simple_health": "/api/simple/health",
            "simple_session": "/api/simple/session/{user_id}/{session_id}",
            "simple_clear_session": "/api/simple/session/{user_id}/{session_id} (DELETE)",
            "file_download": "/api/v1/files/download/{container_id}/{file_id}/{filename}",
            "file_proxy_health": "/api/v1/files/health",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "agents": [
            "DatabaseAgent - Data retrieval & validation",
            "AnalysisAgent - Technical analysis",
            "ResearchAgent - Market research",
            "ReportAgent - Vietnamese reports"
        ],
        "features": [
            "Intelligent task delegation",
            "Multi-agent coordination",
            "Vietnamese language support",
            "Conversation memory (both multi-agent and simple agent)",
            "Comprehensive technical indicators",
            "Real-time market research",
            "Structured output with emojis",
            "Simple agent with persistent session memory"
        ]
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("="*80)
    logger.info("MULTI-AGENT TRADING SYSTEM STARTING")
    logger.info("="*80)
    logger.info("Loading specialized agents...")
    logger.info("DatabaseAgent - Data retrieval & validation")
    logger.info("AnalysisAgent - Technical analysis")
    logger.info("ResearchAgent - Market research")
    logger.info("ReportAgent - Vietnamese reports")
    logger.info("="*80)
    logger.info("System ready! Access docs at http://localhost:8888/docs")
    logger.info("="*80)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("="*80)
    logger.info("MULTI-AGENT TRADING SYSTEM SHUTTING DOWN")
    logger.info("="*80)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=False,
        log_level="info"
    )
