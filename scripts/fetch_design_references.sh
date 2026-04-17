#!/usr/bin/env bash
# scripts/fetch_design_references.sh
# Fetches all awesome-design-md reference files into docs/design-references/
# Run from repo root: bash scripts/fetch_design_references.sh
# Re-run anytime to add new references.

set -e

DESIGNS=(
  airbnb airtable apple bmw cal claude clay clickhouse cohere coinbase
  composio cursor elevenlabs expo ferrari figma framer hashicorp ibm
  intercom kraken lamborghini linear.app lovable minimax mintlify miro
  mistral.ai mongodb notion nvidia ollama opencode.ai pinterest posthog
  raycast renault replicate resend revolut runwayml sanity semrush sentry
  spacex spotify stripe supabase superhuman tesla together.ai uber vercel
  voltagent warp webflow wise x.ai zapier
)

OUTPUT_DIR="docs/design-references"
mkdir -p "$OUTPUT_DIR"

echo "Fetching ${#DESIGNS[@]} design references..."

for name in "${DESIGNS[@]}"; do
  outfile="$OUTPUT_DIR/${name}.md"
  if [ -f "$outfile" ]; then
    echo "  [skip] $name (already exists)"
    continue
  fi
  echo "  Fetching $name..."
  tmpdir=$(mktemp -d)
  (cd "$tmpdir" && npx getdesign@latest add "$name" 2>/dev/null) || true
  if [ -f "$tmpdir/DESIGN.md" ]; then
    cp "$tmpdir/DESIGN.md" "$outfile"
    echo "    -> saved to $outfile"
  else
    echo "    [warn] no output for $name"
  fi
  rm -rf "$tmpdir"
done

echo ""
echo "Done. $(ls "$OUTPUT_DIR"/*.md 2>/dev/null | wc -l) references in $OUTPUT_DIR/"
