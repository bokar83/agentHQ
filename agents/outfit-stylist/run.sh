#!/usr/bin/env bash
# Run the Outfit Stylist app
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load env vars if .env exists in project root
if [ -f "../../.env" ]; then
  export $(grep -v '^#' ../../.env | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set."
  echo "Add it to your .env file or export it before running."
  exit 1
fi

echo "Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "🎨 Starting Outfit Stylist on http://localhost:8080"
echo "   Open this URL in your browser to get started."
echo ""
python app.py
