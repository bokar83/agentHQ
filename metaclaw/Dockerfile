FROM python:3.11-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install all metaclaw deps at build time (no runtime pip install)
# torch CPU-only from pytorch index, everything else from PyPI
RUN pip install --no-cache-dir \
    aiming-metaclaw \
    openai \
    torch \
    --extra-index-url https://download.pytorch.org/whl/cpu

WORKDIR /app

CMD ["metaclaw", "start", "--mode", "skills_only"]
