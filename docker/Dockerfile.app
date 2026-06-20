# ---------------------------------------------------------------------------
# STAGE 1: Builder (Compiles dependencies)
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for high-speed dependency resolution
RUN pip install uv

# Copy the frozen dependency list
COPY requirements.txt .

# Create a dedicated virtual environment inside the container
RUN uv venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install all dependencies into the container's virtual environment
RUN uv pip install -r requirements.txt

# ---------------------------------------------------------------------------
# STAGE 2: Production Runtime (Lean execution environment)
# ---------------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy ONLY the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code (Ignore raw data, tests, and scripts)
COPY src/ ./src/

# Enforce secure Python execution standards
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the internal container port to the Docker network
EXPOSE 8000

# Boot the FastAPI application via Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]