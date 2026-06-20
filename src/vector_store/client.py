import logging
from opensearchpy import AsyncOpenSearch
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenSearchManager:
    def __init__(self):
        self.host = settings.OPENSEARCH_HOST
        self.port = settings.OPENSEARCH_PORT
        
        # We use an async client to allow parallel queries across multiple book indices
        self.client = AsyncOpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_compress=True,
            use_ssl=False,     # SSL is disabled locally via our docker-compose config
            verify_certs=False # Bypasses certificate checks for local development
        )

    async def check_health(self) -> bool:
        """Pings the OpenSearch cluster to verify it is responsive."""
        try:
            is_connected = await self.client.ping()
            if is_connected:
                logger.info(f"Successfully connected to OpenSearch at {self.host}:{self.port}")
            else:
                logger.warning("OpenSearch node is unresponsive.")
            return is_connected
        except Exception as e:
            logger.error(f"OpenSearch connection failed. Error: {e}")
            return False

    def get_client(self) -> AsyncOpenSearch:
        """Returns the active async client pool."""
        return self.client

# Instantiate a single global connection pool
os_manager = OpenSearchManager()