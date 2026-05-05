#!/usr/bin/env bash
# scripts/session_start_audit.sh
# Read-only working-tree audit. Fired by SessionStart hook.
# Reports drift so the agent surfaces clutter to the user instead of carrying it forward.
# Never modifies state. Exits 0 always (so SessionStart never blocks).

set -uo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" || exit 0

mod=$(git diff --name-only 2>/dev/null | wc -l)
staged=$(git diff --cached --name-only 2>/dev/null | wc -l)
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
unpushed=$(git log @{u}..HEAD --oneline 2>/dev/null | wc -l)

# Specific clutter patterns at repo root
root_pngs=$(find . -maxdepth 1 -name "*.png" -type f 2>/dev/null | wc -l)
root_html=$(find . -maxdepth 1 -name "*.html" -type f 2>/dev/null | wc -l)

# Old/stale archive candidates: untracked deliverables/handoffs >= 3 days old
old_handoffs=$(find docs/handoff -maxdepth 1 -name "*.md" -mtime +3 2>/dev/null | grep -v archive/ | wc -l)

[ "$mod" -eq 0 ] && [ "$staged" -eq 0 ] && [ "$untracked" -eq 0 ] && [ "$unpushed" -eq 0 ] && [ "$root_pngs" -eq 0 ] && [ "$root_html" -eq 0 ] && exit 0

echo "==== SESSION START AUDIT ===="
echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
[ "$mod" -gt 0 ]       && echo "  modified:   $mod"
[ "$staged" -gt 0 ]    && echo "  staged:     $staged"
[ "$untracked" -gt 0 ] && echo "  untracked:  $untracked"
[ "$unpushed" -gt 0 ]  && echo "  unpushed:   $unpushed commits"
[ "$root_pngs" -gt 0 ] && echo "  WARN: $root_pngs PNG(s) at repo root -- move to deliverables/ or zzzArchive/"
[ "$root_html" -gt 0 ] && echo "  WARN: $root_html HTML(s) at repo root -- move to deliverables/"
[ "$old_handoffs" -gt 0 ] && echo "  WARN: $old_handoffs handoff doc(s) >3 days old in docs/handoff/ root -- move to docs/handoff/archive/"
echo "Run /nsync to triage, or address before next push."
echo "============================="
exit 0
