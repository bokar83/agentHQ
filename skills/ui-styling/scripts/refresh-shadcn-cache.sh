#!/usr/bin/env bash
set -euo pipefail
DATE="$(date +%Y-%m-%d)"
OUT="$(dirname "$0")/../cache"
mkdir -p "$OUT"
CURL_OPTS=(-fsSL)
[[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* ]] && CURL_OPTS+=(--ssl-no-revoke)
curl "${CURL_OPTS[@]}" "https://ui.shadcn.com/llms.txt" -o "$OUT/llms-$DATE.txt"
curl "${CURL_OPTS[@]}" "https://ui.shadcn.com/schema/registry.json" -o "$OUT/registry-schema-$DATE.json"
echo "cached: $OUT/llms-$DATE.txt + $OUT/registry-schema-$DATE.json"
