import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # ---------------------------------------------------------------------------
    # Core Application Settings
    # ---------------------------------------------------------------------------
    ENV: Literal["development", "staging", "production"] = Field(
        default="development", 
        description="The active deployment stage environment."
    )
    PROJECT_NAME: str = Field(
        default="agentic-rag-core",
        description="The name of the underlying service."
    )
    
    # ---------------------------------------------------------------------------
    # Compute & Engine Strategy
    # ---------------------------------------------------------------------------
    # For a local non-spend setup, we default to local mock routing. 
    # Switch to 'bedrock' to trigger active AWS calls.
    ROUTING_STRATEGY: Literal["mock", "bedrock"] = Field(
        default="mock",
        description="Determines if routing is handled locally or passed to AWS Bedrock."
    )
    MAX_ROUTING_RETRIES: int = Field(
        default=3,
        description="Circuit breaker threshold to prevent infinite agent routing loops."
    )

    # ---------------------------------------------------------------------------
    # Memory Layer (AWS ElastiCache for Redis)
    # ---------------------------------------------------------------------------
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Connection string for the Redis cache cluster."
    )
    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        description="Time-to-live for cached semantic RAG responses (1 hour)."
    )

    # ---------------------------------------------------------------------------
    # Data Layer (Amazon OpenSearch Serverless)
    # ---------------------------------------------------------------------------
    OPENSEARCH_HOST: str = Field(
        default="localhost",
        description="The host endpoint for the vector database node."
    )
    OPENSEARCH_PORT: int = Field(
        default=9200,
        description="The connection network port for the vector database node."
    )

    # ---------------------------------------------------------------------------
    # Pydantic Settings Configuration
    # ---------------------------------------------------------------------------
    # Automatically reads from a local .env file if it exists, matching environment targets
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Drops non-declared environment variables safely
    )

# Instantiate a single global settings object to share across the application modules
settings = Settings()