#!/bin/bash
# post_build_check.sh: agentsHQ Humanized Standard Automated Linting
#
# Run from the project root after the builder agent completes.
# Exits 0 if all checks pass, 1 if any check fails.
#
# USAGE:
#   bash scripts/post_build_check.sh ./src
#   bash scripts/post_build_check.sh /path/to/project/src
#
# The script reads design_brief.md from the current directory
# to determine the declared archetype and apply the correct exceptions.

PROJECT_DIR=${1:-"./src"}
BRIEF_FILE="./design_brief.md"
FAIL=0
WARN=0
PASS_COUNT=0
TOTAL_CHECKS=12

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

pass() {
  echo "  PASS: $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "  FAIL: $1"
  if [ -n "$2" ]; then
    echo "        $2"
  fi
  FAIL=1
}

warn() {
  echo "  WARN: $1"
  WARN=$((WARN + 1))
}

check_banned_string() {
  local pattern="$1"
  local label="$2"
  local exclude_pattern="$3"

  local results
  if [ -n "$exclude_pattern" ]; then
    results=$(grep -rn --include="*.tsx" --include="*.ts" --include="*.css" \
      "$pattern" "$PROJECT_DIR" 2>/dev/null | grep -v "$exclude_pattern")
  else
    results=$(grep -rn --include="*.tsx" --include="*.ts" --include="*.css" \
      "$pattern" "$PROJECT_DIR" 2>/dev/null)
  fi

  local count
  count=$(echo "$results" | grep -c . 2>/dev/null || echo 0)

  if [ "$count" -gt 0 ]; then
    fail "$label ($count occurrence(s))" "$(echo "$results" | head -3)"
  else
    pass "$label"
  fi
}

check_required_string() {
  local pattern="$1"
  local file="$2"
  local label="$3"

  local count
  count=$(grep -c "$pattern" "$file" 2>/dev/null || echo 0)

  if [ "$count" -lt 1 ]; then
    fail "$label" "Not found in $file"
  else
    pass "$label"
  fi
}

check_required_in_dir() {
  local pattern="$1"
  local label="$2"

  local count
  count=$(grep -rn --include="*.tsx" --include="*.ts" "$pattern" "$PROJECT_DIR" 2>/dev/null | wc -l)

  if [ "$count" -lt 1 ]; then
    fail "$label" "Not found in $PROJECT_DIR"
  else
    pass "$label"
  fi
}

# ============================================================
# READ ARCHETYPE FROM design_brief.md
# ============================================================

ARCHETYPE="UNKNOWN"
if [ -f "$BRIEF_FILE" ]; then
  ARCHETYPE=$(grep "Selected archetype:" "$BRIEF_FILE" 2>/dev/null | awk '{print $NF}' | tr -d '[:space:]')
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  agentsHQ Post-Build Automated Check: Humanized Standard   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Project dir: $PROJECT_DIR"
echo "  Archetype:   ${ARCHETYPE:-UNKNOWN}"
echo ""

# ============================================================
# PHASE 1: BANNED STRING CHECKS
# ============================================================

echo "── Phase 1: Banned String Checks ──────────────────────────────"

# 1.1 ease-in-out
check_banned_string "ease-in-out" "1.1 ease-in-out banned"

# 1.2 duration-300
check_banned_string "duration-300" "1.2 duration-300 banned"

# 1.3 ease-linear (outside of linear() spring definitions)
check_banned_string "ease-linear\|ease:.*[\"']linear[\"']" \
  "1.3 ease-linear banned (outside spring defs)" \
  "linear("

# 1.4 Tailwind shadow-md pattern
check_banned_string "rgba(0,0,0,0.1)" "1.4 generic rgba shadow banned"

# 1.5 Symmetric 3-column feature grid
check_banned_string "repeat(3, 1fr)" "1.5 symmetric 3-column grid banned"

echo ""

# ============================================================
# PHASE 2: PRESENCE CHECKS
# ============================================================

echo "── Phase 2: Presence Checks ────────────────────────────────────"

# 1.6 SmoothScrollProvider (skip for BRUTALIST and TRUST_ENTERPRISE)
if [[ "$ARCHETYPE" == "BRUTALIST" || "$ARCHETYPE" == "TRUST_ENTERPRISE" ]]; then
  echo "  SKIP: 1.6 SmoothScrollProvider (archetype $ARCHETYPE: not required)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  check_required_string "SmoothScrollProvider" "src/app/layout.tsx" \
    "1.6 SmoothScrollProvider present in layout.tsx"
fi

# 1.7 KineticText (skip for BRUTALIST)
if [[ "$ARCHETYPE" == "BRUTALIST" ]]; then
  echo "  SKIP: 1.7 KineticText (BRUTALIST archetype: not required)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  check_required_in_dir "KineticText" "1.7 KineticText used in build"
fi

# 1.8 MagneticButton (skip for BRUTALIST)
if [[ "$ARCHETYPE" == "BRUTALIST" ]]; then
  echo "  SKIP: 1.8 MagneticButton (BRUTALIST archetype: not required)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  check_required_in_dir "MagneticButton" "1.8 MagneticButton used in build"
fi

# 1.9 craft-tokens.css imported first in globals.css
check_required_string "craft-tokens.css" "src/app/globals.css" \
  "1.9 craft-tokens.css imported in globals.css"

echo ""

# ============================================================
# PHASE 3: STRUCTURAL CHECKS
# ============================================================

echo "── Phase 3: Structural Checks ──────────────────────────────────"

# 1.10 Inter as heading font (h1, h2, h3 must not use Inter)
INTER_IN_HEADINGS=$(grep -rn --include="*.tsx" --include="*.css" \
  "font.*Inter\|Inter.*font" "$PROJECT_DIR" 2>/dev/null | \
  grep -i "h1\|h2\|h3\|heading\|display" || true)

if [ -n "$INTER_IN_HEADINGS" ]; then
  fail "1.10 Inter heading font: Inter found in heading context" \
    "$(echo "$INTER_IN_HEADINGS" | head -2)"
else
  pass "1.10 Inter not used as heading font"
fi

# 1.11 Uniform border radius: warn if same radius value appears in 3+ element types
RADIUS_VALUES=$(grep -rn --include="*.tsx" --include="*.css" \
  "border-radius\|rounded-" "$PROJECT_DIR" 2>/dev/null | \
  grep -oE "rounded-[a-z]+|border-radius:[^;]+" | sort | uniq -c | sort -rn | head -5)

if echo "$RADIUS_VALUES" | grep -qE "^\s*[3-9][0-9]* "; then
  warn "1.11 Uniform border radius: same value appears many times (review manually)"
  echo "        Top values: $RADIUS_VALUES"
else
  pass "1.11 Border radius variation looks acceptable"
fi

# 1.12 Form error states
FORM_COUNT=$(grep -rn --include="*.tsx" "form\|<Form\|<input\|<Input" \
  "$PROJECT_DIR" 2>/dev/null | wc -l)

if [ "$FORM_COUNT" -gt 0 ]; then
  ERROR_STATE_COUNT=$(grep -rn --include="*.tsx" \
    "aria-invalid\|error.*class\|class.*error\|isError\|hasError\|errorMessage" \
    "$PROJECT_DIR" 2>/dev/null | wc -l)

  if [ "$ERROR_STATE_COUNT" -lt 1 ]; then
    fail "1.12 Form error states missing" \
      "$FORM_COUNT form-related elements found, 0 error state patterns found"
  else
    pass "1.12 Form error states present ($ERROR_STATE_COUNT occurrence(s))"
  fi
else
  echo "  SKIP: 1.12 Form error states (no form elements detected)"
  PASS_COUNT=$((PASS_COUNT + 1))
fi

echo ""

# ============================================================
# RESULT SUMMARY
# ============================================================

echo "── Result ──────────────────────────────────────────────────────"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo "  ✓ ALL AUTOMATED CHECKS PASSED ($PASS_COUNT/$TOTAL_CHECKS)"
  if [ "$WARN" -gt 0 ]; then
    echo "  ⚠ $WARN warning(s) require manual review"
  fi
  echo ""
  echo "  Proceed to critic agent for human judgment scoring."
  echo "  Reference: design_upgrade/deliverables/eval_rubric.md"
  echo ""
  exit 0
else
  echo "  ✗ ONE OR MORE CHECKS FAILED"
  echo ""
  echo "  Fix the failures above before submitting to the critic agent."
  echo "  The critic agent will catch the same failures and issue REVISE."
  echo "  Fixing before submission saves a build cycle."
  echo ""
  exit 1
fi
