import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# Import from our cleanly defined facades
from src.core import settings, guardrails
from src.cache import semantic_cache
from src.agent import agent_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the API
app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

class ChatRequest(BaseModel):
    query: str

@app.post("/v1/chat")
async def chat_endpoint(request: ChatRequest) -> Dict[str, Any]:
    user_query = request.query.strip()
    
    # -------------------------------------------------------------------------
    # STEP 1: The Perimeter (AWS Bedrock Guardrails Mock)
    # -------------------------------------------------------------------------
    is_safe, rejection_reason = guardrails.validate_query(user_query)
    if not is_safe:
        raise HTTPException(status_code=400, detail=rejection_reason)

    # -------------------------------------------------------------------------
    # STEP 2: The Memory Layer (AWS ElastiCache for Redis Mock)
    # -------------------------------------------------------------------------
    cached_data = semantic_cache.get(user_query)
    if cached_data:
        return {
            "source": "cache",
            "latency_optimization": "active",
            "data": cached_data
        }

    # -------------------------------------------------------------------------
    # STEP 3: The Brain (Agent Orchestrator & OpenSearch Pipeline)
    # -------------------------------------------------------------------------
    try:
        agent_response = await agent_orchestrator.execute_rag_cycle(user_query)
    except Exception as e:
        logger.error(f"Critical execution failure in orchestrator: {e}")
        raise HTTPException(status_code=500, detail="Internal system error during RAG processing.")

    # -------------------------------------------------------------------------
    # STEP 4: State Preservation
    # -------------------------------------------------------------------------
    if agent_response.get("status") == "success":
        semantic_cache.set(user_query, agent_response)

    return {
        "source": "orchestrator",
        "latency_optimization": "miss",
        "data": agent_response
    }