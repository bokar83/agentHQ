# agentsHQ Orchestrator Container
# Build: docker compose build orchestrator
# Run: docker compose up -d orchestrator

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies + Node.js 22 (required by hyperframes) + ffmpeg (required by hyperframes render)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Google Workspace CLI (gws) + hyperframes globally
RUN npm install -g @googleworkspace/cli@0.22.1
RUN npm install -g hyperframes

# Set gws credentials path (file mounted from secrets/ volume at runtime)
ENV GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=/app/secrets/gws-oauth-credentials.json

# Copy and install Python dependencies
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all orchestrator source files
COPY orchestrator/*.py .

# Copy voice prompts for the Sankofa Council
COPY orchestrator/prompts/ prompts/

# Copy skills, templates, and docs (quote bank etc.).
# tests/ is NOT copied into the production image. Shipping tests to prod
# inflates the image and leaks fixture data. Removed 2026-04-22 per code
# review. Run tests locally: pytest (or from the repo root before build).
COPY skills/ skills/
COPY templates/ templates/
COPY docs/ docs/
COPY signal_works/ signal_works/
COPY configs/ configs/

# Create required directories
RUN mkdir -p /app/outputs /app/logs /app/outputs/proposals /app/outputs/council

# Expose the FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the service. Flipped from orchestrator:app to app:app on 2026-04-24
# as part of the shadow module backport. orchestrator.py stays in the
# image as a rollback reference for at least one week after the flip.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
