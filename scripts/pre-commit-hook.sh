#!/usr/bin/env bash
# pre-commit: no-stash, no-auto-modify, fail-with-instructions only.
# Replaces pre-commit framework to eliminate silent branch switching
# and silent file reversion caused by the framework's stash cycle.

set -euo pipefail

BRANCH_AT_ENTRY=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")

fail() {
    echo "" >&2
    echo "PRE-COMMIT BLOCKED: $1" >&2
    echo "  $2" >&2
    echo "" >&2
    exit 1
}

check_branch() {
    local current
    current=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")
    if [ "$current" != "$BRANCH_AT_ENTRY" ]; then
        fail "Branch switched during hook!" \
             "Started on '$BRANCH_AT_ENTRY', now on '$current'. Do not commit."
    fi
}

# 1. Secrets scan
if command -v detect-secrets-hook &>/dev/null && [ -f .secrets.baseline ]; then
    echo "Scanning for secrets..."
    staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
    if [ -n "$staged_files" ]; then
        if ! echo "$staged_files" | xargs detect-secrets-hook --baseline .secrets.baseline 2>/dev/null; then
            fail "Secrets detected in staged files." \
                 "Run: detect-secrets scan --baseline .secrets.baseline  then re-stage."
        fi
    fi
    echo "No secrets detected."
fi

check_branch

# 2. Em-dash check (staged .md files only -- never auto-fixes)
staged_md=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '\.md$' || true)
if [ -n "$staged_md" ]; then
    bad=""
    while IFS= read -r f; do
        [ -f "$f" ] || continue
        if python3 -c "
import sys
try:
    t = open('$f', encoding='utf-8', errors='ignore').read()
    if u'—' in t:
        sys.exit(1)
    import re
    if re.search(r'(?<![!-]) -- (?!>)', t):
        sys.exit(1)
except: pass
" 2>/dev/null; then
            : # clean
        else
            bad="$bad $f"
        fi
    done <<< "$staged_md"
    if [ -n "$bad" ]; then
        fail "Em-dash found in:$bad" \
             "Replace em-dash or ' -- ' with comma / period / colon. Re-stage and commit."
    fi
fi

check_branch

# 3. Skill frontmatter lint (read-only)
staged_skills=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '^skills/.*SKILL\.md$' || true)
if [ -n "$staged_skills" ]; then
    if [ -f scripts/lint_and_index_skills.py ]; then
        python3 scripts/lint_and_index_skills.py --check-only 2>/dev/null || \
            fail "Skill SKILL.md missing required frontmatter (name/description)." \
                 "Add ---\nname: ...\ndescription: ...\n--- to top of SKILL.md, re-stage."
    fi
fi

# 4. Hook registration guard
if git diff --cached --name-only 2>/dev/null | grep -qE '\.claude/|settings\.json'; then
    if [ -f scripts/check_hook_registration.py ]; then
        python3 scripts/check_hook_registration.py 2>/dev/null || \
            fail "Hook registration check failed." \
                 "Add HOOK_MODEL / HOOK_COST_PER_FIRE / HOOK_FIRING_RATE annotation."
    fi
fi

# 5. Provider redirect guard
if [ -f scripts/check_no_provider_redirect.py ]; then
    python3 scripts/check_no_provider_redirect.py 2>/dev/null || \
        fail "ANTHROPIC_BASE_URL redirect detected in staged files." \
             "Remove or revert the redirect before committing."
fi

# 6. Docker doc-drift guard
# When docker-compose.yml or Dockerfile changes, scan docs for stale claims about
# the deploy model. If we removed a COPY or added a volume, old "code is baked"
# rules in CLAUDE.md / AGENT_SOP.md / skill docs become lies.
docker_changed=$(git diff --cached --name-only 2>/dev/null | grep -E '^(docker-compose\.ya?ml|orchestrator/Dockerfile)$' || true)
if [ -n "$docker_changed" ]; then
    stale_phrases='code is baked|baked into image|not volume-mounted|baked from the Dockerfile'
    drift=$(grep -rEln "$stale_phrases" CLAUDE.md docs/AGENT_SOP.md skills/*/SKILL.md 2>/dev/null || true)
    if [ -n "$drift" ]; then
        fail "Docker config changed but stale 'code is baked' phrasing in: $drift" \
             "Update those files to match new docker-compose.yml reality, then commit them in the SAME commit."
    fi
fi

check_branch

echo "Pre-commit checks passed."
exit 0
