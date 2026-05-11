#!/bin/bash
# docker-entrypoint.sh
# Syncs volume-mounted orchestrator/*.py over the baked /app/*.py copies on
# every container start. Eliminates silent import-precedence drift where
# Dockerfile COPY bakes stale files into /app/ root and Python resolves them
# before the volume-mounted /app/orchestrator/ path.
#
# Safe to run even if volume is not yet attached: || true guards all ops.
# Added 2026-05-08 after 10 baked files were found drifted in production.

set -e

if [ -d /app/orchestrator ] && [ "$(ls -A /app/orchestrator/*.py 2>/dev/null)" ]; then
    cp /app/orchestrator/*.py /app/ 2>/dev/null || true
    # Also sync orchestrator/*.json so config edits actually deploy. Without
    # this, modules that read JSON via CWD-resolved fallback get the stale
    # baked copy. Hit 2026-05-11 when studio_trend_seeds.default.json re-seed
    # had no effect because /app/studio_trend_seeds.default.json was missing
    # and the loader fell back to inline _DEFAULT_SEEDS in code.
    cp /app/orchestrator/*.json /app/ 2>/dev/null || true
    find /app -maxdepth 1 -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
fi

exec "$@"
