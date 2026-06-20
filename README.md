``` sequenceDiagram
    participant User as User Browser
    participant Flask as Frontend (Flask)
    participant API as Orchestrator (FastAPI)
    participant Redis as Cache (Redis)
    participant DB as Vector DB (OpenSearch)
    participant LLM as Host LLM (Ollama)

    User->>Flask: POST /api/send (Query)
    Flask->>API: POST /v1/chat
    
    API->>Redis: Check Cache
    alt Cache Hit
        Redis-->>API: Cached Response
    else Cache Miss
        API->>DB: Parallel Intent Routing & Retrieval
        DB-->>API: Raw Text Context Chunks
        API->>LLM: Prompt + Context (via host.docker.internal)
        Note over LLM: LLaMA 3.2 synthesizes <br/>answer using GPU
        LLM-->>API: Markdown Response
        API->>Redis: Store Response in Cache
    end
    
    API-->>Flask: JSON Payload
    Note over Flask: Sanitize regex & <br/>parse Markdown
    Flask-->>User: Rendered UI ```