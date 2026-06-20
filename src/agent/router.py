import logging
from typing import List
from src.core.config import settings

logger = logging.getLogger(__name__)

class IntentRouter:
    def __init__(self):
        self.strategy = settings.ROUTING_STRATEGY

    def route_query(self, query: str) -> List[str]:
        """
        Evaluates the user query and resolves which book indices must be targeted.
        """
        logger.info(f"Routing query via strategy: '{self.strategy}'")
        
        if self.strategy == "bedrock":
            # Real production hook: inside this block, you initialize boto3 bedrock-runtime
            # and use structural tool-calling / JSON parsing to let the LLM return the indices.
            logger.info("Redirecting routing routing decision to AWS Bedrock...")
            return ["ml_book", "dl_book", "mlops_book"]

        # Local Default Strategy: High-Performance Structural Intent Keywords
        tokens = query.lower().split()
        target_indices = set()

        # Domain Maps
        ml_keywords = {"ml", "machine", "regression", "svm", "classification", "random", "forest", "scikit", "feature"}
        dl_keywords = {"dl", "deep", "neural", "network", "transformer", "cnn", "rnn", "weights", "backprop", "llm"}
        mlops_keywords = {"ops", "mlops", "deploy", "pipeline", "docker", "kubernetes", "cicd", "monitor", "serve"}

        # Check intersections
        for token in tokens:
            cleaned_token = token.strip("?.!,:;")
            if cleaned_token in ml_keywords:
                target_indices.add("ml_book")
            if cleaned_token in dl_keywords:
                target_indices.add("dl_book")
            if cleaned_token in mlops_keywords:
                target_indices.add("mlops_book")

        # Fallback Matrix Rules
        # Rule 1: Comparative context detection (Forces a multi-index merge match)
        comparative_triggers = {"compare", "versus", "vs", "difference", "between"}
        if any(trigger in query.lower() for trigger in comparative_triggers):
            logger.info("Comparative query intent triggered. Fan-out to all indices activated.")
            return ["ml_book", "dl_book", "mlops_book"]

        # Rule 2: Complete miss fallback (Scan everything to prevent complete blind spots)
        if not target_indices:
            logger.warning(f"No explicit intent tokens found for query: '{query}'. Defaulting to comprehensive search.")
            return ["ml_book", "dl_book", "mlops_book"]

        resolved_routes = list(target_indices)
        logger.info(f"Query resolved to target indices: {resolved_routes}")
        return resolved_routes