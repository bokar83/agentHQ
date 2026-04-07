# agentsHQ Orchestrator Container
# Build: docker compose build orchestrator
# Run: docker compose up -d orchestrator

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all orchestrator source files
COPY orchestrator/*.py .

# Copy voice prompts for the Sankofa Council
COPY orchestrator/prompts/ prompts/

# Copy skills, tests, and docs (quote bank etc.)
COPY skills/ skills/
COPY tests/ tests/
COPY docs/ docs/

# Create required directories
RUN mkdir -p /app/outputs /app/logs /app/outputs/proposals /app/outputs/council

# Expose the FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the service
CMD ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
