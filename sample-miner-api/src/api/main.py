"""
Sample Miner API - Unified Component Interface with Conversation History

This miner implements a unified component interface where all components share
the same input/output pattern with conversation history.

INPUT PATTERN (ComponentInput):
- cid: Conversation ID
- task: Task description
- input: List[InputItem] containing user_query and notebook context
- previous_outputs: List[PreviousOutput] from previous component executions

OUTPUT PATTERN (ComponentOutput):
- task: The task that was executed
- output: The result from the component
- component: Component name (complete, refine, feedback, etc.)

SUPPORTED COMPONENTS:
1. complete: Process tasks with conversation history
2. refine: Improve outputs based on previous component results
3. feedback: Analyze outputs and provide structured feedback
4. human_feedback: Acknowledge and store user feedback in conversation history
5. internet_search: Search internet (template - miners implement actual search)
6. summary: Use LLM to summarize previous outputs
7. aggregate: Majority voting on multiple outputs

CONVERSATION MANAGEMENT:
- Stores up to 10 recent messages per conversation
- Automatically deletes messages older than 1 week
- Messages included in component execution for context

ARCHITECTURE:
- Unified interface: All components use ComponentInput/ComponentOutput
- Conversation history: Recent context for better responses
- Auto cleanup: Old messages removed automatically
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from datetime import datetime
import logging
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.models.models import (
    ComponentInput, ComponentOutput, InputItem, PreviousOutput
)
from src.api.auth import verify_api_key, optional_api_key
from src.services.llm_client import generate_response, complete_text
from src.core.conversation import conversation_manager
from src.core.config import settings
from src.core.database import create_db_and_tables
# Import new component handlers
from src.services.components import (
    component_complete,
    component_refine,
    component_feedback,
    component_human_feedback,
    component_internet_search,
    component_summary,
    component_aggregate
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Sample Miner API - Unified Component Interface",
    description="A unified component interface with conversation history (max 10 messages, auto-cleanup after 1 week). All components use the same input/output pattern.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    logger.info("🚀 Starting up Sample Miner API...")
    try:
        create_db_and_tables()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


# Shutdown event to cleanup resources
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    logger.info("🛑 Shutting down Sample Miner API...")
    try:
        # Close database connections
        from src.core.database import engine
        engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Request size limit middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Limit request body size to prevent memory exhaustion attacks."""
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    if request.headers.get("content-length"):
        content_length = int(request.headers.get("content-length"))
        if content_length > MAX_REQUEST_SIZE:
            logger.warning(f"Request too large: {content_length} bytes (max {MAX_REQUEST_SIZE})")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Maximum size: {MAX_REQUEST_SIZE // (1024*1024)}MB"}
            )
    
    return await call_next(request)


# Request timeout middleware
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add timeout to all requests to prevent hanging."""
    try:
        return await asyncio.wait_for(
            call_next(request),
            timeout=60.0  # 60 second timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Request timeout: {request.method} {request.url}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timeout after 60 seconds"}
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Sample Miner API",
        "status": "running",
        "architecture": "Unified component interface with conversation history",
        "endpoints": {
            "complete": "/complete - Process tasks with conversation history",
            "refine": "/refine - Refine outputs based on previous results",
            "feedback": "/feedback - Analyze outputs and provide feedback",
            "human_feedback": "/human_feedback - Acknowledge user feedback",
            "internet_search": "/internet_search - Search internet (template)",
            "summary": "/summary - Summarize previous outputs",
            "aggregate": "/aggregate - Majority voting on outputs"
        },
        "conversation_management": {
            "list_conversations": "GET /conversations - List all conversations (requires auth)",
            "get_conversation": "GET /conversations/{cid} - Get conversation history (requires auth)",
            "delete_conversation": "DELETE /conversations/{cid} - Delete conversation (requires auth)"
        },
        "playbook_endpoints": {
            "get_playbook": "GET /playbook/{cid} - Get playbook entries (requires auth)",
            "get_playbook_context": "GET /playbook/{cid}/context - Get formatted playbook context (requires auth)"
        },
        "other_endpoints": {
            "capabilities": "/capabilities - Get miner capabilities",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        },
        "features": {
            "conversation_history": "Stores max 10 recent messages per conversation",
            "auto_cleanup": "Deletes messages older than 1 week",
            "unified_interface": "All components use same input/output pattern"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = conversation_manager.get_stats()
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "model": settings.get_model_name,
        "active_conversations": stats["total_conversations"],
        "features": {
            "unified_api": True,
            "conversation_history": True,
            "playbook_system": True
        }
    }


@app.get("/capabilities", dependencies=[Depends(optional_api_key)])
async def get_capabilities():
    """Get miner capabilities and supported functions."""
    return {
        "miner_name": settings.miner_name,
        "llm_provider": settings.llm_provider,
        "model": settings.get_model_name,
        "conversation_history_enabled": True,
        "max_conversation_messages": settings.max_conversation_messages,
        "message_retention_days": settings.conversation_cleanup_days,
        "components": [
            "complete",
            "refine",
            "feedback",
            "human_feedback",
            "internet_search",
            "summary",
            "aggregate"
        ],
        "features": {
            "unified_component_interface": True,
            "conversation_history": True,
            "auto_message_cleanup": True,
            "internet_search_template": True,
            "llm_summary": True,
            "majority_voting": True,
            "privacy_friendly": True,
            "multi_provider_support": True,
            "quantized_model_friendly": True
        }
    }


# ============================================================================
# Unified Component API Endpoints
# ============================================================================

@app.post("/complete", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def complete_component(request: Request, component_input: ComponentInput):
    """
    Complete a task with conversation history.
    
    All components now use the same input/output pattern:
    - Input: ComponentInput (task, input list, previous_outputs)
    - Output: ComponentOutput (task, output, component)
    
    This endpoint processes tasks using conversation history (max 10 recent messages,
    auto-deletes messages older than 1 week).
    
    Rate limit: 20 requests per minute per IP address.
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_complete(component_input, context)
    except Exception as e:
        logger.error(f"Error in complete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def refine_component(request: Request, component_input: ComponentInput):
    """
    Refine outputs based on previous component results.
    
    Analyzes previous outputs (from previous_outputs field) and provides
    an improved, refined version with conversation history context.
    
    Rate limit: 20 requests per minute per IP address.
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_refine(component_input, context)
    except Exception as e:
        logger.error(f"Error in refine: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def feedback_component(request: Request, component_input: ComponentInput):
    """
    Analyze outputs and provide structured feedback.
    
    Reviews previous outputs (from previous_outputs field) and provides
    constructive feedback with conversation history context.
    
    Rate limit: 20 requests per minute per IP address.
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_feedback(component_input, context)
    except Exception as e:
        logger.error(f"Error in feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/human_feedback", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def human_feedback_component(request: Request, component_input: ComponentInput):
    """
    Process human feedback and store in conversation history.
    
    Takes human feedback from input field and stores it in conversation history
    for context in future interactions.
    
    Rate limit: 30 requests per minute per IP address (higher limit for feedback).
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_human_feedback(component_input, context)
    except Exception as e:
        logger.error(f"Error in human_feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/internet_search", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def internet_search_component(request: Request, component_input: ComponentInput):
    """
    Search the internet for information.
    
    NOTE: This is a template implementation that returns "unavailable service".
    Miners should implement actual internet search functionality using services like:
    - Google Custom Search API
    - Bing Search API
    - DuckDuckGo API
    - SerpAPI
    
    See the implementation in src/services/components.py for detailed notes.
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_internet_search(component_input, context)
    except Exception as e:
        logger.error(f"Error in internet_search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summary", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
async def summary_component(request: Request, component_input: ComponentInput):
    """
    Summarize previous outputs using LLM.
    
    Takes multiple previous outputs (from previous_outputs field) and creates
    a concise, comprehensive summary that captures main points and key insights.
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_summary(component_input, context)
    except Exception as e:
        logger.error(f"Error in summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/aggregate", response_model=ComponentOutput, dependencies=[Depends(verify_api_key)])
@limiter.limit("15/minute")
async def aggregate_component(request: Request, component_input: ComponentInput):
    """
    Aggregate outputs using majority voting.
    
    Analyzes multiple previous outputs (from previous_outputs field) and
    determines the consensus answer through majority voting logic.
    """
    try:
        context = conversation_manager.get_or_create(component_input.cid)
        return await component_aggregate(component_input, context)
    except Exception as e:
        logger.error(f"Error in aggregate: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def list_all_conversations(request: Request):
    """
    List all active conversations with basic metadata.
    
    Returns a list of all conversations from the database with their
    message counts and timestamps.
    
    Returns:
        Dict with list of conversations and total count
    """
    try:
        # Get stats directly from conversation manager (uses database)
        stats = conversation_manager.get_stats()
        
        return {
            "total_conversations": stats["total_conversations"],
            "conversations": stats["conversations"]
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{cid}", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_conversation_history(request: Request, cid: str):
    """
    Get full conversation history for a specific conversation ID.
    
    Returns all messages, metadata, and statistics for the specified conversation.
    
    Args:
        cid: Conversation ID
        
    Returns:
        Dict with conversation metadata and complete message history
    """
    try:
        context = conversation_manager.get_or_create(cid)
        messages = context.get_messages()
        
        return {
            "cid": cid,
            "message_count": len(messages),
            "messages": messages,
            "created_at": context.created_at.isoformat() if hasattr(context, 'created_at') else None,
            "last_activity": context.last_activity.isoformat() if hasattr(context, 'last_activity') else None
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation {cid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{cid}", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def delete_conversation(request: Request, cid: str):
    """
    Delete a conversation and all its history.
    
    This removes the conversation from the database and deletes all associated messages.
    
    Args:
        cid: Conversation ID to delete
        
    Returns:
        Success message
    """
    try:
        # Check if conversation exists in database
        context = conversation_manager.get(cid)
        
        if context is None:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {cid} not found"
            )
        
        # Delete from database
        conversation_manager.delete(cid)
        logger.info(f"Deleted conversation {cid} from database")
        
        return {
            "success": True,
            "message": f"Conversation {cid} deleted successfully",
            "cid": cid
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {cid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/playbook/{cid}", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_playbook(request: Request, cid: str):
    """
    Get playbook entries for a specific conversation.
    
    Returns all playbook entries (user preferences, insights, and learned context)
    associated with the conversation ID.
    
    Args:
        cid: Conversation ID
        
    Returns:
        Dict with playbook entries and metadata
    """
    try:
        from src.services.components import get_playbook_service
        
        playbook_service = get_playbook_service()
        entries = await playbook_service.get_playbook(cid)
        
        return {
            "cid": cid,
            "entry_count": len(entries),
            "entries": entries
        }
    except Exception as e:
        logger.error(f"Error retrieving playbook for {cid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/playbook/{cid}/context", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_playbook_context(request: Request, cid: str):
    """
    Get formatted playbook context for a conversation.
    
    Returns the playbook entries formatted as context text that can be used
    in prompts to provide user preferences and learned insights to the LLM.
    
    Args:
        cid: Conversation ID
        
    Returns:
        Dict with formatted context string
    """
    try:
        from src.services.components import get_playbook_service
        
        playbook_service = get_playbook_service()
        entries = await playbook_service.get_playbook(cid)
        
        if entries:
            context = playbook_service.format_playbook_context(entries)
        else:
            context = "No playbook entries found for this conversation."
        
        return {
            "cid": cid,
            "entry_count": len(entries),
            "formatted_context": context,
            "entries": entries
        }
    except Exception as e:
        logger.error(f"Error retrieving playbook context for {cid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.get_port)
