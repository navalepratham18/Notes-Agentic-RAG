import logging
import httpx
from typing import Dict, Any
from src.agent.router import IntentRouter
from src.vector_store.pipeline import parallel_retrieval
from src.core.config import settings

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.router = IntentRouter()
        self.max_retries = settings.MAX_ROUTING_RETRIES

    async def execute_rag_cycle(self, user_query: str) -> Dict[str, Any]:
        """
        The master control loop. Routes the query, triggers parallel retrieval, 
        and validates the retrieved context.
        """
        logger.info(f"Orchestrator received query: '{user_query}'")
        
        # Step 1: Agentic Routing
        target_indices = self.router.route_query(user_query)
        
        # Step 2: Retrieve with Circuit Breaker Loop
        retries = 0
        context_data = {}
        
        while retries < self.max_retries:
            context_data = await parallel_retrieval(user_query, target_indices)
            
            if self._validate_context(context_data):
                logger.info("Context retrieved and validated successfully.")
                break
                
            logger.warning(f"Retrieval yielded empty context. Retry {retries + 1}/{self.max_retries}")
            retries += 1
            target_indices = ["ml_book", "dl_book", "mlops_book"] 
            
        if not self._validate_context(context_data):
            logger.error("Max retries hit. Agent failed to retrieve sufficient context.")
            return {
                "status": "degraded",
                "response": "I could not find enough relevant information in the knowledge base to answer that confidently.",
                "context": {},
                "routed_indices": target_indices
            }

        # Step 4: LLM Synthesis via Local Ollama
        llm_response = await self._synthesize_response(user_query, context_data)

        return {
            "status": "success",
            "response": llm_response,
            "context": context_data,
            "routed_indices": target_indices
        }

    def _validate_context(self, context_data: Dict[str, list]) -> bool:
        if not context_data:
            return False
        for index, chunks in context_data.items():
            if chunks and len(chunks) > 0:
                return True
        return False

    async def _synthesize_response(self, query: str, context_data: Dict[str, list]) -> str:
        """Packages the retrieved text and sends it to LLaMA 3.2 for synthesis."""
        logger.info(f"Sending context to LLaMA 3.2 for synthesis...")
        
        # Flatten the context chunks into a single readable string for the LLM
        flattened_context = ""
        for index, chunks in context_data.items():
            flattened_context += f"--- From {index} ---\n"
            flattened_context += "\n".join(chunks) + "\n\n"

        prompt = f"""You are a highly technical AI assistant. 
        Use the following retrieved context to inform your answer. If the context does not contain the exact answer, rely on your general knowledge to provide a helpful, accurate, and technical response.

        Context:
        {flattened_context}

        User Query: {query}

        Answer clearly, using bullet points or concise technical explanations if appropriate:"""

        payload = {
            "model": settings.LLM_MODEL,
            "prompt": prompt,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "Error: No response generated.")
        except Exception as e:
            logger.error(f"Ollama synthesis failed: {e}")
            return "Error: Could not connect to local LLM for synthesis."

# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()