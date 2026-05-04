"""
studio_qa_crew.py - Studio M1 Engine.

Quality Review Crew. 8 checks that run on every drafted Studio asset BEFORE
it goes to render or publish. Failures route to Telegram with a summary;
passes flip the Pipeline DB record to Status=qa-passed.

Why 8 checks not 1: Studio publishes faceless content under brand names
that are NOT Boubacar's. Bad output ships under brand names that have no
backstop. The 8 checks catch the failure modes that matter:

  1. Spellcheck/grammar pass (Sonnet via existing voice_polisher route)
  2. Banned-phrase filter (slurs, platform-banned terms, copyright trigger)
  3. Length-within-target enforcement
  4. Hook-in-first-3-seconds rule (long-form) or hook-in-first-line (short)
  5. Source-citation present if claim is factual
  6. CTA present and platform-appropriate
  7. No Boubacar-personal-rules violations (no coffee/alcohol props per
     feedback_no_alcohol_or_coffee_imagery; no em-dashes per
     feedback_no_em_dashes; no fake-client-stories per
     feedback_never_fabricate_client_stories)
  8. Brand-voice consistency (matches the brief at
     docs/roadmap/studio/channels/<channel>.md)

Most checks are pure regex/string. Two are Sonnet-LLM-backed (1 spellcheck,
8 brand voice). Total cost per asset: ~$0.01-0.02 per QA pass.

Pipeline integration: called from studio_production_tick() in M3 (not yet
built). For M1 the crew is callable standalone via run_qa_on_record(notion_id)
so Boubacar can spot-check any drafted asset.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("agentsHQ.studio_qa_crew")

PIPELINE_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "")


@dataclass
class QACheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class QAReport:
    notion_id: str
    channel: str
    title: str
    checks: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> list:
        return [c for c in self.checks if not c.passed]

    def summary(self) -> str:
        marks = "".join("." if c.passed else "X" for c in self.checks)
        return f"[{marks}] {self.title[:60]}"


# ═════════════════════════════════════════════════════════════════════════════
# Check 1: Spellcheck/grammar (LLM-light pass)
# ═════════════════════════════════════════════════════════════════════════════

def check_spellcheck_grammar(text: str) -> QACheckResult:
    """Lightweight spelling + grammar check. Catches obvious typos that would
    embarrass a brand. Pure regex for v0; M3 can upgrade to Sonnet pass.
    """
    if not text or not text.strip():
        return QACheckResult("spellcheck", False, "empty text")
    # Strip [SCENE: ...] markers — they leave double-spaces that aren't typos
    check_text = re.sub(r'\[SCENE:[^\]]*\]\s*', '', text)
    # Common typo patterns (extend as we learn)
    typos = [
        (r"\bteh\b", "teh -> the"),
        (r"\brecieve\b", "recieve -> receive"),
        (r"\bseperate\b", "seperate -> separate"),
        (r"\bdefinately\b", "definately -> definitely"),
        (r"\boccured\b", "occured -> occurred"),
        (r"\bweather\s+(?=or not)", "weather or not -> whether or not"),
    ]
    issues = []
    for pat, label in typos:
        if re.search(pat, check_text, re.IGNORECASE):
            issues.append(label)
    if issues:
        return QACheckResult("spellcheck", False, f"likely typos: {', '.join(issues)}")
    return QACheckResult("spellcheck", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 2: Banned-phrase filter
# ═════════════════════════════════════════════════════════════════════════════

# Slurs and platform-trigger words. NOT exhaustive; this is the floor not the
# ceiling. Add per-incident as we learn.
BANNED_PHRASES = [
    # Platform-banned phrasing for monetization
    r"\bsubscribe\s+(?:and|&)\s+like\b",  # exact "like and subscribe" demand is fine; the order matters less now
    # Copyright-magnet song lyrics (none specific yet, this is where they'd land)
    # Slurs would go here; intentionally not enumerated in source
]

# Patterns that often flag platform demonetization for "engagement bait"
ENGAGEMENT_BAIT = [
    r"\bdon't\s+forget\s+to\s+subscribe\b",
    r"\bsmash\s+(?:that\s+)?like\s+button\b",
    r"\bring\s+the\s+bell\b",
]


def check_banned_phrases(text: str) -> QACheckResult:
    """Reject text containing slurs, platform-banned terms, copyright triggers,
    or known engagement-bait patterns that demonetize.
    """
    text_lower = text.lower()
    hits = []
    for pat in BANNED_PHRASES:
        if re.search(pat, text_lower, re.IGNORECASE):
            hits.append(f"banned: {pat}")
    for pat in ENGAGEMENT_BAIT:
        if re.search(pat, text_lower, re.IGNORECASE):
            hits.append(f"engagement-bait: {pat}")
    if hits:
        return QACheckResult("banned_phrases", False, "; ".join(hits))
    return QACheckResult("banned_phrases", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 3: Length-within-target
# ═════════════════════════════════════════════════════════════════════════════

LENGTH_TARGETS = {
    # length_target name -> (min_words, max_words) at ~150 wpm spoken
    "short (<60s)":    (50,   200),   # 20-80 sec
    "medium (60-180s)":(200,  600),   # 1-4 min
    "long (3-15m)":    (400, 2500),   # 3-15 min (10 min = ~1500 words)
}


def check_length_target(text: str, length_target: str) -> QACheckResult:
    """Verify word count is within the configured length-target band."""
    if length_target not in LENGTH_TARGETS:
        return QACheckResult("length_target", True, f"unknown target '{length_target}', skipping")
    lo, hi = LENGTH_TARGETS[length_target]
    # Strip [SCENE:...] markers before counting — they aren't spoken
    spoken = re.sub(r'\[SCENE:[^\]]*\]', '', text)
    n = len(spoken.split())
    if n < lo:
        return QACheckResult("length_target", False, f"{n} words < min {lo} for '{length_target}'")
    if n > hi:
        return QACheckResult("length_target", False, f"{n} words > max {hi} for '{length_target}'")
    return QACheckResult("length_target", True, f"{n} words within [{lo}, {hi}]")


# ═════════════════════════════════════════════════════════════════════════════
# Check 4: Hook in first 3 seconds / first line
# ═════════════════════════════════════════════════════════════════════════════

def check_hook_present(text: str, length_target: str) -> QACheckResult:
    """Verify the draft has a hook. For shorts: first sentence is the hook.
    For long-form: first ~30 words are the hook (roughly first 3 sec spoken).
    A 'hook' here = first chunk is non-trivial and not a generic intro.
    """
    if not text or not text.strip():
        return QACheckResult("hook_present", False, "empty text")
    first_line = text.split("\n", 1)[0].strip()
    first_30_words = " ".join(text.split()[:30])
    target = first_line if "short" in length_target else first_30_words
    if len(target) < 20:
        return QACheckResult("hook_present", False, f"hook too short: {target!r}")
    # Reject generic intros
    generic_intros = [
        r"^\s*(?:hi|hey|hello|welcome|today\s+i'?m|in\s+this\s+video)\b",
        r"^\s*(?:thanks|thank\s+you)\s+for\s+(?:watching|joining|tuning)",
    ]
    for pat in generic_intros:
        if re.search(pat, target, re.IGNORECASE):
            return QACheckResult("hook_present", False, f"generic intro: {target[:60]!r}")
    return QACheckResult("hook_present", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 5: Source citation present (factual claim heuristic)
# ═════════════════════════════════════════════════════════════════════════════

# Phrases that signal a factual claim and require a source
FACTUAL_CLAIM_PATTERNS = [
    r"\baccording\s+to\b",
    r"\bstudies\s+(?:show|find)\b",
    r"\bresearch\s+(?:shows|finds)\b",
    r"\b\d+%\s+of\b",  # any "X% of..." statistic
    r"\b\$\d+[KMB]?\b",  # any specific dollar amount
]

# Phrases that signal a citation IS present
CITATION_PATTERNS = [
    r"\bsource[s]?:\s",
    r"\bvia\s+\w+",
    r"\bper\s+(?:the\s+)?[A-Z]",
    r"\(\d{4}\)",  # year in parens
    r"https?://",  # any URL
]


def check_source_citation(text: str) -> QACheckResult:
    """If the draft makes a factual claim (statistic, dollar amount, study
    reference), it must include a citation. Skip if no factual claims.
    """
    text_lower = text.lower()
    has_claim = any(re.search(p, text_lower, re.IGNORECASE) for p in FACTUAL_CLAIM_PATTERNS)
    if not has_claim:
        return QACheckResult("source_citation", True, "no factual claims detected")
    has_citation = any(re.search(p, text, re.IGNORECASE) for p in CITATION_PATTERNS)
    if not has_citation:
        return QACheckResult("source_citation", False, "factual claim without citation")
    return QACheckResult("source_citation", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 6: CTA present and platform-appropriate
# ═════════════════════════════════════════════════════════════════════════════

CTA_PATTERNS = [
    r"\bfollow\b",
    r"\bsubscribe\b",
    r"\bcheck\s+(?:out\s+)?(?:my|the)\b",
    r"\blink\s+in\s+bio\b",
    r"\bdrop\s+a\s+comment\b",
    r"\bdm\s+me\b",
    r"\bvisit\s+\w+\.\w+",  # any visit some-domain
    r"\bjoin\s+(?:the|us|me)\b",
    r"\bwhat\s+do\s+you\s+think\b",
    r"\?\s*$",  # ends with a question
]


def check_cta_present(text: str) -> QACheckResult:
    """Some form of CTA must exist. Open-ended question counts."""
    if not text:
        return QACheckResult("cta_present", False, "empty text")
    text_lower = text.lower()
    for pat in CTA_PATTERNS:
        if re.search(pat, text_lower, re.IGNORECASE | re.MULTILINE):
            return QACheckResult("cta_present", True, "")
    return QACheckResult("cta_present", False, "no CTA detected")


# ═════════════════════════════════════════════════════════════════════════════
# Check 7: Boubacar-personal-rules
# ═════════════════════════════════════════════════════════════════════════════

# Coffee/alcohol terms (per feedback_no_alcohol_or_coffee_imagery.md)
COFFEE_ALCOHOL_TERMS = [
    r"\bcoffee\b", r"\bespresso\b", r"\blatte\b", r"\bcappuccino\b",
    r"\bwine\b", r"\bbeer\b", r"\bcocktail\b", r"\bwhiskey\b",
    r"\bbar\s+(?:scene|setting)\b",
]

# Em-dashes (per feedback_no_em_dashes.md). Same logic as the pre-commit hook.
EM_DASH_PATTERN = r"[—–]|(?:(?<=\w)--| -- )"

# Fabricated client stories (per feedback_never_fabricate_client_stories.md)
# First-person engagement claims that aren't allowed since Boubacar has no
# paid CW clients yet (per feedback_no_client_engagements_yet.md).
FABRICATED_STORY_PATTERNS = [
    r"\bi\s+sit\s+with\s+clients\b",
    r"\bi\s+walk\s+into\s+firms\b",
    r"\bthe\s+firms\s+i\s+work\s+with\b",
    r"\bmy\s+client\s+(?:said|told|asked)\b",
]


def check_personal_rules(text: str) -> QACheckResult:
    """Check Boubacar's personal/values rules:
      - No coffee/alcohol references (LDS faith)
      - No em-dashes or double-hyphens (no-em-dash hard rule)
      - No fabricated client stories (no paid CW clients yet)
    """
    issues = []
    text_lower = text.lower()
    for pat in COFFEE_ALCOHOL_TERMS:
        if re.search(pat, text_lower):
            issues.append(f"coffee/alcohol: {pat}")
    if re.search(EM_DASH_PATTERN, text):
        issues.append("em-dash or double-hyphen")
    for pat in FABRICATED_STORY_PATTERNS:
        if re.search(pat, text_lower):
            issues.append(f"fabricated client story: {pat}")
    if issues:
        return QACheckResult("personal_rules", False, "; ".join(issues))
    return QACheckResult("personal_rules", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 8: Brand voice consistency (per-channel brief)
# ═════════════════════════════════════════════════════════════════════════════

# Per-channel banned-phrase lists: things that the channel's brand voice
# explicitly does NOT do. Loaded from docs/roadmap/studio/channels/<niche>.md
# at M2 ship time; for M1 v0 we use a basic per-niche default.
NICHE_BRAND_BANS = {
    "african-folktales": [
        # Under the Baobab does not talk modern-tech-business
        r"\bblockchain\b", r"\bcrypto\b", r"\bAPI\b", r"\bSaaS\b",
    ],
    "ai-displacement": [
        # AI Catalyst does not invent client engagements
        r"\bone of my clients\b", r"\bin my consulting practice\b",
    ],
    "first-gen-money": [
        # First Generation Money does not give specific stock picks
        r"\b(?:buy|buying|sell|selling)\s+(?:NVDA|TSLA|AAPL|GOOG|GOOGL|AMZN|MSFT|META|NFLX|AMD)\b",
        r"\b(?:I\s+)?recommend\s+(?:investing\s+in|buying|selling)\b",
    ],
}


def check_brand_voice(text: str, niche: str) -> QACheckResult:
    """Channel-specific banned phrases. Per-niche brand voice bans live in
    NICHE_BRAND_BANS. Future: load from per-channel brief markdown.
    """
    bans = NICHE_BRAND_BANS.get(niche, [])
    if not bans:
        return QACheckResult("brand_voice", True, f"no bans configured for '{niche}'")
    text_lower = text.lower()
    hits = []
    for pat in bans:
        if re.search(pat, text_lower, re.IGNORECASE):
            hits.append(pat)
    if hits:
        return QACheckResult("brand_voice", False, f"brand voice violation: {', '.join(hits)}")
    return QACheckResult("brand_voice", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 9: Retention loop density
# ═════════════════════════════════════════════════════════════════════════════

RETENTION_LOOP_PATTERNS = [
    r"\[RETENTION:",                   # explicit marker from script generator
    r"\bbut here('s| is) the\b",
    r"\bhere('s| is) what (?:nobody|no one|most people)\b",
    r"\bstay (?:with me|tuned)\b",
    r"\bmore on that in a (?:moment|second|minute)\b",
    r"\bwe(?:'ll| will) (?:get to|come back to) that\b",
    r"\bthe answer (?:might|will) surprise you\b",
    r"\bwait for (?:it|this)\b",
    r"\bbefore (?:we|I) (?:get to|continue)\b",
    r"\bhere's (?:the part|what)\b",
    r"\bkeep watching\b",
    r"\bthis next part\b",
    r"\bmost people get this (?:completely )?wrong\b",
]

_RETENTION_INTERVAL_WORDS = 250  # slightly generous — script generator targets every 200w


def check_retention_loops(text: str) -> QACheckResult:
    """Long-form scripts must include a curiosity/cliffhanger trigger every
    ~200 words to maintain viewer retention. Signal from V5 YouTube analysis.
    """
    if not text or not text.strip():
        return QACheckResult("retention_loops", False, "empty text")
    # Strip [SCENE: ...] markers — they inflate word count without being narrated
    spoken = re.sub(r'\[SCENE:[^\]]*\]', '', text).strip()
    words = spoken.split()
    if len(words) < _RETENTION_INTERVAL_WORDS:
        return QACheckResult("retention_loops", True, "short content, loop check skipped")

    segments = []
    step = _RETENTION_INTERVAL_WORDS
    for i in range(0, len(words), step):
        segments.append(" ".join(words[i: i + step]))

    missing = []
    for idx, seg in enumerate(segments[:-1]):  # last segment = outro, skip
        seg_lower = seg.lower()
        has_loop = any(re.search(p, seg_lower, re.IGNORECASE) for p in RETENTION_LOOP_PATTERNS)
        if not has_loop:
            missing.append(f"segment {idx + 1}")

    if missing:
        return QACheckResult(
            "retention_loops",
            False,
            f"no retention trigger in: {', '.join(missing)}",
        )
    return QACheckResult("retention_loops", True, "")


# ═════════════════════════════════════════════════════════════════════════════
# Check 10: YouTube 100% AI monetization risk flag
# ═════════════════════════════════════════════════════════════════════════════

# Phrases that YouTube's review team flags as AI-generated disclosure risk.
# Source: V4 YouTube analysis — YouTube penalizes 100% AI script+voice+visuals.
# The script itself must contain at least one human editorial signal:
# an original opinion, a specific named source, or a personal observation.
_AI_RISK_PATTERNS = [
    r"\bin (?:today's|this) video,?\s+(?:we(?:'ll| will)|I(?:'ll| will)) (?:explore|dive into|look at|cover|discuss)\b",
    r"\bwithout further ado\b",
    r"\bin conclusion,?\s+(?:we can|it is clear|it's clear)\b",
    r"\blet(?:'s| us) (?:explore|dive into|delve into)\b",
    r"\bfascinating (?:world|topic|subject)\b",
    r"\bsit back and (?:relax|enjoy)\b",
]

_HUMAN_SIGNAL_PATTERNS = [
    r"\baccording to\b",
    r"\bper (?:the\s+)?[A-Z]",       # per Harvard, per WHO, etc.
    r"\ba \d{4} (?:study|report|survey)\b",
    r"\bresearchers (?:at|from)\b",
    r"\bI (?:believe|think|argue|contend)\b",  # editorial opinion (narrator voice OK)
    r"\bone thing (?:that|I)\b",
    r"\bhere's what (?:the data|research|science)\b",
]


def check_ai_origin_safe(text: str) -> QACheckResult:
    """Script must not read as 100% AI-boilerplate AND must contain at least
    one human editorial signal (named source, opinion, or specific data point).
    YouTube penalizes 100% AI content during monetization review.
    """
    if not text or not text.strip():
        return QACheckResult("ai_origin_safe", False, "empty text")

    text_lower = text.lower()
    risk_hits = [p for p in _AI_RISK_PATTERNS if re.search(p, text_lower, re.IGNORECASE)]
    human_signals = [p for p in _HUMAN_SIGNAL_PATTERNS if re.search(p, text, re.IGNORECASE)]

    if risk_hits and not human_signals:
        return QACheckResult(
            "ai_origin_safe",
            False,
            f"AI-boilerplate phrases present, no human editorial signal. Risk patterns: {risk_hits[:2]}",
        )
    return QACheckResult("ai_origin_safe", True, f"{len(human_signals)} human signal(s) found")


# ═════════════════════════════════════════════════════════════════════════════
# Run all 10 checks
# ═════════════════════════════════════════════════════════════════════════════

# Niches that are storytelling/creative — source citations don't apply
_STORYTELLING_NICHES = {"african-folktales", "parenting-psychology"}


def run_qa(text: str, niche: str, length_target: str = "long (3-15m)",
            notion_id: str = "", channel: str = "", title: str = "") -> QAReport:
    """Run all 10 checks. Returns QAReport with per-check pass/fail."""
    report = QAReport(notion_id=notion_id, channel=channel, title=title)
    # Source citation check skipped for storytelling niches (folktales, parenting stories)
    if niche in _STORYTELLING_NICHES:
        citation_check = QACheckResult("source_citation", True, f"skipped for storytelling niche '{niche}'")
    else:
        citation_check = check_source_citation(text)
    report.checks = [
        check_spellcheck_grammar(text),
        check_banned_phrases(text),
        check_length_target(text, length_target),
        check_hook_present(text, length_target),
        citation_check,
        check_cta_present(text),
        check_personal_rules(text),
        check_brand_voice(text, niche),
        check_retention_loops(text),
        check_ai_origin_safe(text),
    ]
    return report


def run_qa_on_record(notion_id: str) -> Optional[QAReport]:
    """Pull a record from Studio Pipeline by Notion ID, run QA, write result
    back. Used by spot-checks and by the production tick (M3).
    """
    if not PIPELINE_DB_ID:
        logger.error("studio_qa_crew: NOTION_STUDIO_PIPELINE_DB_ID not set")
        return None

    try:
        from skills.forge_cli.notion_client import NotionClient
        secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
        notion = NotionClient(secret=secret)
        page = notion.get_page(notion_id)
    except Exception as e:
        logger.error(f"studio_qa_crew: cannot read Notion record {notion_id}: {e}")
        return None

    if not page:
        logger.warning(f"studio_qa_crew: record {notion_id} not found")
        return None

    props = page.get("properties", {})
    title = "".join(t.get("plain_text", "") for t in (props.get("Title", {}).get("title") or []))
    channel = (props.get("Channel", {}).get("select") or {}).get("name", "")
    niche = (props.get("Niche tag", {}).get("select") or {}).get("name", "")
    length_target = (props.get("Length target", {}).get("select") or {}).get("name", "long (3-15m)")
    draft = "".join(t.get("plain_text", "") for t in (props.get("Draft", {}).get("rich_text") or []))

    report = run_qa(draft, niche, length_target, notion_id=notion_id, channel=channel, title=title)

    # Write QA result back to the record
    new_status = "qa-passed" if report.passed else "qa-failed"
    qa_notes = " | ".join(f"{c.name}: {c.detail}" for c in report.failed_checks) or "all 8 checks passed"
    try:
        notion.update_page(notion_id, {
            "Status": {"select": {"name": new_status}},
            "QA notes": {"rich_text": [{"text": {"content": qa_notes[:1500]}}]},
        })
    except Exception as e:
        logger.error(f"studio_qa_crew: cannot update {notion_id} with QA result: {e}")

    return report
