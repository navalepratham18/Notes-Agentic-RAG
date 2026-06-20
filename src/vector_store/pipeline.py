import asyncio
import logging
from typing import Dict, Any, List
from src.vector_store.client import os_manager

logger = logging.getLogger(__name__)

async def _search_single_index(index_name: str, query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Executes an async search against a single specific OpenSearch index.
    """
    client = os_manager.get_client()
    
    # Standard BM25 Keyword/Semantic mock query for our local OpenSearch
    search_body = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["content", "title^2"] # Boosts matches in the title
            }
        }
    }
    
    try:
        response = await client.search(index=index_name, body=search_body)
        hits = response.get("hits", {}).get("hits", [])
        
        # Extract just the raw text payload we want to feed to the LLM
        extracted_texts = [hit["_source"].get("content", "") for hit in hits]
        logger.info(f"Retrieved {len(extracted_texts)} chunks from index: {index_name}")
        
        return {"index": index_name, "context": extracted_texts, "status": "success"}
    
    except Exception as e:
        logger.error(f"Search failed on index '{index_name}': {e}")
        return {"index": index_name, "context": [], "status": "failed", "error": str(e)}

async def parallel_retrieval(query: str, target_indices: List[str]) -> Dict[str, List[str]]:
    """
    Fires multiple search requests to OpenSearch simultaneously and aggregates the results.
    """
    if not target_indices:
        logger.warning("No target indices provided for retrieval.")
        return {}

    logger.info(f"Initiating parallel search across indices: {target_indices}")
    
    # 1. Create a list of async tasks, one for each targeted book
    tasks = [
        _search_single_index(index_name=index, query=query) 
        for index in target_indices
    ]
    
    # 2. Execute all tasks simultaneously. 
    # return_exceptions=True ensures that if the DL index crashes, the ML index still returns its data.
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 3. Format the aggregated results into a clean dictionary for the LLM
    aggregated_context = {}
    for res in results:
        if isinstance(res, dict) and res.get("status") == "success":
            aggregated_context[res["index"]] = res["context"]
        else:
            # Handle the exception gracefully without blowing up the orchestration
            failed_index = res.get("index", "unknown") if isinstance(res, dict) else "unknown"
            logger.warning(f"Skipping failed index in aggregation: {failed_index}")
            
    return aggregated_context