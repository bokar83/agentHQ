from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

ORCH_DIR = Path(__file__).resolve().parent
ROOT_DIR = ORCH_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _resolve_skill_dir() -> Path:
    """Find skills/content_multiplier across local-dev, container-baked, and
    container-mounted layouts.

    Local dev: file lives at <repo>/orchestrator/content_multiplier_crew.py;
      skills at <repo>/skills/content_multiplier.
    Container mounted (correct): /app/orchestrator/content_multiplier_crew.py;
      skills at /app/skills/content_multiplier.
    Container baked (Dockerfile COPY of orchestrator/*.py to /app/):
      /app/content_multiplier_crew.py; skills mounted at /app/skills.
      ROOT_DIR resolves to / which is wrong; fall through to /app.
    """
    override = os.environ.get("CONTENT_MULTIPLIER_SKILL_DIR")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.append(ROOT_DIR / "skills" / "content_multiplier")
    candidates.append(Path("/app") / "skills" / "content_multiplier")
    candidates.append(ORCH_DIR / "skills" / "content_multiplier")
    for candidate in candidates:
        if (candidate / "prompts" / "lens_classifier.md").exists():
            return candidate
    return candidates[1]

logger = logging.getLogger("agentsHQ.content_multiplier_crew")
_MULTIPLIER_LOCK = threading.Lock()

CONTENT_DB_ID = "339bcf1a-3029-81d1-8377-dc2f2de13a20"
LENS_MODEL = "anthropic/claude-haiku-4.5"
PIECE_MODEL = "anthropic/claude-sonnet-4.6"
MAX_EXTRACTED_CHARS = 8000
MAX_RUN_COST_USD = 0.50
SONNET_INPUT_USD_PER_TOKEN = 3e-6
SONNET_OUTPUT_USD_PER_TOKEN = 15e-6

CTQ_REJECT_RE = re.compile(r"(\s--\s|\s\u2014\s|\s\u2013\s)")
BANNED_WORDS = ("Loom", "fabricated", "one weird trick")

SKILL_DIR = _resolve_skill_dir()
LENS_PROMPT_PATH = SKILL_DIR / "prompts" / "lens_classifier.md"
PIECE_PROMPT_PATH = SKILL_DIR / "prompts" / "piece_generator.md"
REMIX_PIECE_PROMPT_PATH = SKILL_DIR / "prompts" / "remix_piece_generator.md"

VALID_MODES = ("verbatim", "remix", "auto")


def _resolve_skill_md_path(skill_name: str, env_var: str) -> Path | None:
    """Locate a skills/<name>/SKILL.md across local-dev, container-mounted,
    and container-baked layouts."""
    override = os.environ.get(env_var)
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.append(ROOT_DIR / "skills" / skill_name / "SKILL.md")
    candidates.append(Path("/app") / "skills" / skill_name / "SKILL.md")
    candidates.append(ORCH_DIR / "skills" / skill_name / "SKILL.md")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _load_skill_md(skill_name: str, env_var: str, fallback: str = "") -> str:
    """Read a skill's SKILL.md body (frontmatter stripped). Returns fallback
    string when the file is unreachable so the crew does not block."""
    path = _resolve_skill_md_path(skill_name, env_var)
    if path is None:
        return fallback
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return fallback
    # Strip YAML frontmatter.
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text.strip()


def _load_voice_profile_with_references() -> str:
    """Load voice SKILL.md + key reference files (brand-spine-audit,
    voice-fingerprint) so Sonnet sees the FULL voice spec including
    Boubacar's earned anchors, signature moves, and vocabulary markers --
    not just the meta-rules in SKILL.md."""
    parts = []
    skill_md = _load_skill_md(
        "boub_voice_mastery",
        "BOUB_VOICE_PROFILE_PATH",
        fallback=(
            "Boubacar voice rules: direct, opinionated, specific. No em-dash. "
            "No buzzwords. No fabricated stories. Lead with the news."
        ),
    )
    parts.append(skill_md)

    # Pull the earned-anchor library from references/ if available.
    ref_files = [
        "skills/boub_voice_mastery/references/brand-spine-audit.md",
        "skills/boub_voice_mastery/references/voice-fingerprint.md",
        "skills/ctq-social/references/linkedin-craft.md",
    ]
    for rel in ref_files:
        for root in (ROOT_DIR, Path("/app"), ORCH_DIR):
            candidate = root / rel
            if candidate.exists():
                try:
                    text = candidate.read_text(encoding="utf-8").strip()
                    if text.startswith("---"):
                        end = text.find("\n---", 3)
                        if end != -1:
                            text = text[end + 4:].strip()
                    parts.append(f"\n\n## Reference: {rel}\n\n{text}")
                except Exception:
                    pass
                break
    return "\n".join(parts)


VOICE_PROFILE = _load_voice_profile_with_references()

CTQ_RULES = _load_skill_md(
    "ctq-social",
    "CTQ_SOCIAL_PATH",
    fallback=(
        "Hook stops the scroll: name something the reader felt but never said, "
        "paint a workplace scene, or make a claim that demands they keep reading. "
        "CTA holds up a mirror, ends on wit that stings, or drops a quotable line. "
        "No yes/no questions. No survey questions. No weak rhetoric. "
        "Voice: direct, earned, opinionated, zero hedging."
    ),
)


@dataclass(frozen=True)
class SourceDoc:
    title: str
    source_type: str
    extracted_text: str
    source_url: str


@dataclass(frozen=True)
class PiecePlan:
    number: int
    piece_type: str
    platform: str
    channel: str | None = None
    channel_slug: str | None = None


@dataclass
class GeneratedPiece:
    plan: PiecePlan
    body: str
    hook: str


class CostCapExceeded(RuntimeError):
    pass


class CostGuard:
    def __init__(self, cap_usd: float = MAX_RUN_COST_USD):
        self.cap_usd = cap_usd
        self.estimated_usd = 0.0
        self._lock = threading.Lock()

    def reserve_sonnet(self, prompt: str, output_tokens: int) -> float:
        input_tokens = estimate_tokens(prompt)
        estimated = (
            input_tokens * SONNET_INPUT_USD_PER_TOKEN
            + output_tokens * SONNET_OUTPUT_USD_PER_TOKEN
        )
        with self._lock:
            if self.estimated_usd + estimated > self.cap_usd:
                raise CostCapExceeded(
                    f"content multiplier cost cap exceeded: ${self.estimated_usd + estimated:.3f} > ${self.cap_usd:.2f}"
                )
            self.estimated_usd += estimated
        return estimated


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text or "") / 4))


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required content multiplier file missing: {path}")
    return path.read_text(encoding="utf-8")


def _extract_markdown_section(text: str, heading: str, next_heading_level: str = "##") -> str:
    marker = f"{next_heading_level} {heading}"
    start = text.find(marker)
    if start == -1:
        raise ValueError(f"Prompt section missing: {heading}")
    start = text.find("\n", start)
    if start == -1:
        return ""
    end = text.find(f"\n{next_heading_level} ", start + 1)
    return text[start:end if end != -1 else len(text)].strip()


def _split_lens_prompt() -> tuple[str, str]:
    text = _read_text(LENS_PROMPT_PATH)
    system = _extract_markdown_section(text, "System")
    user = _extract_markdown_section(text, "User")
    return system, user


def _piece_prompt_parts(piece_number: int, mode: str = "verbatim") -> tuple[str, str]:
    """Return (system_block, user_template) for a piece prompt.

    mode="verbatim" reads piece_generator.md (citation allowed).
    mode="remix" reads remix_piece_generator.md (no citation, no quotes).
    """
    if mode == "remix":
        path = REMIX_PIECE_PROMPT_PATH
        piece_marker = f"## Piece {piece_number} (remix):"
    else:
        path = PIECE_PROMPT_PATH
        piece_marker = f"## Piece {piece_number}:"

    text = _read_text(path)
    common_marker = "## Common system block"
    common_start = text.find(common_marker)
    common_end = text.find("\n---", common_start)
    if common_start == -1 or common_end == -1:
        raise ValueError(f"Piece prompt common system block missing in {path.name}.")
    common = text[text.find("\n", common_start):common_end].strip()

    start = text.find(piece_marker)
    if start == -1:
        raise ValueError(f"Piece prompt missing for piece {piece_number} in {path.name}.")
    end = text.find("\n---", start + 1)
    section = text[start:end if end != -1 else len(text)]
    if "User prompt template:" in section:
        section = section.split("User prompt template:", 1)[1]
    else:
        section = section.split("\n", 1)[1]
    return common, section.strip()


def _substitute(template: str, values: dict[str, Any]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out


def _json_from_llm_text(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    if not raw.startswith("{"):
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise ValueError(f"LLM response did not contain JSON: {raw[:200]}")
        raw = match.group(0)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("LLM JSON response was not an object.")
    return data


def _llm_content(response: Any) -> str:
    return response.choices[0].message.content.strip()


def classify_lens(doc: SourceDoc) -> dict[str, Any]:
    from llm_helpers import call_llm

    system, user_template = _split_lens_prompt()
    user = _substitute(
        user_template,
        {
            "title": doc.title,
            "source_type": doc.source_type,
            "extracted_text": doc.extracted_text[:6000],
        },
    )
    response = call_llm(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=LENS_MODEL,
        temperature=0.3,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    lens = _json_from_llm_text(_llm_content(response))
    lens.setdefault("lenses", ["Theory of Constraints", "Systems Thinking"])
    lens.setdefault("channel_fit", ["Boubacar-personal"])
    lens.setdefault("skip_reason", "")
    return lens


def _is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def _youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    if "youtu.be" in parsed.netloc.lower():
        return parsed.path.strip("/")
    qs = parse_qs(parsed.query)
    return (qs.get("v") or [""])[0]


def _infer_source_type(source_url: str, source_type: str) -> str:
    if source_type and source_type != "auto":
        return source_type
    if source_url.startswith("http") and _is_youtube_url(source_url):
        return "youtube"
    if source_url.lower().endswith(".pdf"):
        return "pdf"
    if source_url.startswith("http"):
        return "url"
    return "text"


def ingest_source(source_url: str, source_type: str = "auto") -> SourceDoc:
    actual_type = _infer_source_type(source_url, source_type)
    if actual_type == "youtube":
        title, text = _ingest_youtube(source_url)
    elif actual_type == "url":
        title, text = _ingest_url(source_url)
    elif actual_type == "pdf":
        title, text = _ingest_pdf(source_url)
    elif actual_type == "text":
        title, text = "Raw text source", source_url
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")
    return SourceDoc(
        title=title[:200] or source_url[:120],
        source_type=actual_type,
        extracted_text=(text or "")[:MAX_EXTRACTED_CHARS],
        source_url=source_url,
    )


def _ingest_url(url: str) -> tuple[str, str]:
    response = httpx.get(url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return _extract_pdf_bytes(url, response.content)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    article = soup.find("article") or soup.find("main") or soup.body or soup
    text = "\n".join(line.strip() for line in article.get_text("\n").splitlines() if line.strip())
    return title, text


def _ingest_pdf(path_or_url: str) -> tuple[str, str]:
    if path_or_url.startswith("http"):
        response = httpx.get(path_or_url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        return _extract_pdf_bytes(path_or_url, response.content)
    from pypdf import PdfReader

    reader = PdfReader(path_or_url)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return Path(path_or_url).name, text


def _extract_pdf_bytes(label: str, content: bytes) -> tuple[str, str]:
    from io import BytesIO
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return Path(urlparse(label).path).name or label, text


def _ingest_youtube(url: str) -> tuple[str, str]:
    video_id = _youtube_video_id(url)
    if not video_id:
        raise ValueError("Could not parse YouTube video id.")
    from youtube_transcript_api import YouTubeTranscriptApi

    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    lines = []
    for item in transcript:
        start = float(item.get("start") or 0.0)
        lines.append(f"[{start:.1f}s] {item.get('text', '')}")
    return f"YouTube {video_id}", "\n".join(lines)


def _channel_fit(lens: dict[str, Any], target_channels: list[str] | None) -> list[str]:
    fit = [str(c) for c in lens.get("channel_fit") or []]
    if target_channels:
        allowed = set(target_channels)
        fit = [c for c in fit if c in allowed]
    return fit


PIECE_CAP = 4
PIECE_FLOOR = 1

# Auto-promote-eligible piece types post to FACELESS brand accounts only
# (UTB / 1stGen / AIC YouTube + TikTok + Instagram). They go to Notion as
# Status=Ready, allowing auto_publisher / griot_scheduler to schedule them
# without manual approval.
#
# Every OTHER piece type (LI-long, X-thread, X-single, direct, adjacent,
# contrarian, quote, newsletter) lands on Boubacar's PERSONAL LinkedIn / X
# accounts. Those always stay as Status=Idea so Griot or Boubacar promotes
# them manually. Boubacar's hard rule 2026-05-07: nothing auto-posts to his
# personal social accounts.
AUTO_PROMOTE_PIECE_TYPES = frozenset({
    "video-UTB",
    "video-1stGen",
    "video-AIC",
})


def _initial_status_for_piece_type(piece_type: str) -> str:
    return "Ready" if piece_type in AUTO_PROMOTE_PIECE_TYPES else "Idea"


def build_piece_plans(lens: dict[str, Any], target_channels: list[str] | None = None) -> list[PiecePlan]:
    """Channel-aware piece routing with quality-driven count.

    UTB and 1stGen are FACELESS brand channels: video script ONLY.
    AIC + Boubacar-personal carry the personal pieces.

    Cap at PIECE_CAP (4). Floor at PIECE_FLOOR (1). Lens classifier returns
    `recommended_piece_types` ranked by fit; crew honors that ranking and
    truncates to the cap. Never force 9 pieces from a thin source.
    """
    fit = set(_channel_fit(lens, target_channels))
    can_personal = "Boubacar-personal" in fit or "AIC" in fit

    # Map every possible piece type to a PiecePlan. The lens classifier picks
    # which subset to actually produce.
    catalog: dict[str, PiecePlan] = {}
    if can_personal:
        catalog["LI-long"] = PiecePlan(1, "LI-long", "LinkedIn")
        catalog["X-thread"] = PiecePlan(2, "X-thread", "X")
        catalog["X-single"] = PiecePlan(3, "X-single", "X")
        catalog["direct"] = PiecePlan(4, "direct", "LinkedIn")
        catalog["adjacent"] = PiecePlan(5, "adjacent", "LinkedIn")
        catalog["contrarian"] = PiecePlan(6, "contrarian", "LinkedIn")
        catalog["quote"] = PiecePlan(8, "quote", "X")
        catalog["newsletter"] = PiecePlan(9, "newsletter", "Newsletter")
    for channel in ("UTB", "1stGen", "AIC"):
        if channel in fit:
            catalog[f"video-{channel}"] = PiecePlan(
                7, f"video-{channel}", channel,
                channel=channel, channel_slug=channel.lower(),
            )

    if not catalog:
        return []

    # Lens classifier may pre-rank piece types. Honor the ranking; otherwise
    # fall back to a sane default ordering.
    recommended = lens.get("recommended_piece_types") or []
    ordered: list[PiecePlan] = []
    seen: set[str] = set()
    for piece_type in recommended:
        plan = catalog.get(piece_type)
        if plan and piece_type not in seen:
            ordered.append(plan)
            seen.add(piece_type)
    # Fill from default order if classifier under-recommended.
    default_order = [
        "video-UTB", "video-1stGen", "video-AIC",
        "LI-long", "X-thread", "direct", "adjacent", "contrarian",
        "X-single", "newsletter", "quote",
    ]
    for piece_type in default_order:
        plan = catalog.get(piece_type)
        if plan and piece_type not in seen and len(ordered) < PIECE_CAP:
            ordered.append(plan)
            seen.add(piece_type)

    # Cap and floor.
    if len(ordered) > PIECE_CAP:
        ordered = ordered[:PIECE_CAP]
    if not ordered:
        # Emergency floor: at least one piece if the catalog had anything.
        ordered = [next(iter(catalog.values()))]
    return ordered


def _lens_brief_text(lens: dict[str, Any]) -> str:
    return json.dumps(lens, ensure_ascii=True, indent=2)


def _generate_one_piece(
    doc: SourceDoc,
    lens: dict[str, Any],
    plan: PiecePlan,
    cost_guard: CostGuard,
    mode: str = "verbatim",
    remix_notes: dict[str, Any] | None = None,
    diversity_context: str = "",
) -> GeneratedPiece:
    from llm_helpers import call_llm

    system, user_template = _piece_prompt_parts(plan.number, mode=mode)
    remix_notes = remix_notes or {}
    values = {
        "lenses": ", ".join(lens.get("lenses") or []),
        "key_claim": lens.get("key_claim", ""),
        "unique_angle": lens.get("unique_angle", ""),
        "contrarian_read": lens.get("contrarian_read", ""),
        "source_url": doc.source_url if mode == "verbatim" else "",
        "extracted_text": doc.extracted_text[:6000],
        "lens_brief": _lens_brief_text(lens),
        "source_excerpt": doc.extracted_text[:6000],
        "voice_profile": VOICE_PROFILE,
        "ctq_rules": CTQ_RULES,
        "channel": plan.channel or "",
        "channel_slug": plan.channel_slug or "",
        # Remix-specific substitutions. Empty in verbatim mode.
        "concept_to_keep": remix_notes.get("concept_to_keep", ""),
        "remix_hint": remix_notes.get("remix_hint", ""),
        "fixable_strips": "; ".join(remix_notes.get("fixable_strips") or []),
    }
    user = _substitute(user_template, values)
    if diversity_context:
        user = (
            f"{user}\n\n"
            f"=== DIVERSITY CONSTRAINT ===\n"
            f"You are writing piece {plan.number} ({plan.piece_type}). The other "
            f"pieces from this run already lead with these hooks:\n"
            f"{diversity_context}\n"
            f"Your piece MUST take a meaningfully different angle. Do not "
            f"reuse the same hook, the same example, or the same closing "
            f"phrase. Different anchor (cultural bridge / failure / "
            f"contrarian / values), different specific example, different "
            f"close. If the only honest piece is a paraphrase of the others, "
            f"return the literal string SKIP_NO_NEW_ANGLE and nothing else."
        )
    prompt_for_cost = system + "\n\n" + user
    cost_guard.reserve_sonnet(prompt_for_cost, output_tokens=800)
    response = call_llm(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=PIECE_MODEL,
        temperature=0.7,
        max_tokens=800,
    )
    body = _strip_code_fences(_llm_content(response))
    return GeneratedPiece(plan=plan, body=body, hook=_extract_hook(body))


def _strip_code_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences from an LLM response.

    Sonnet sometimes wraps the formatted output in triple-backticks. The fence
    leaks into Title extraction (record titled '```') and clutters the Draft
    body. Strip them so the hook is the real first line.
    """
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        else:
            cleaned = cleaned[3:]
    if cleaned.rstrip().endswith("```"):
        cleaned = cleaned.rstrip()
        cleaned = cleaned[: -3].rstrip()
    return cleaned.strip()


_LABEL_RE = re.compile(
    r"^(HOOK|BEAT\s*\d+|CLOSE|HEADLINE|QUOTE|BODY|ATTRIBUTION|"
    r"IMAGE_PROMPT|PALETTE|VARIATION\s*\d+)\b[^:]*:\s*",
    re.IGNORECASE,
)


def _extract_hook(body: str) -> str:
    cleaned = _strip_code_fences(body)
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Drop label-only lines like "HOOK (0-2s):" that prefix the actual hook.
        if line.endswith(":") and len(line) < 60:
            continue
        # Strip a known label prefix like "HOOK (0-2s):" or "HEADLINE:".
        match = _LABEL_RE.match(line)
        if match:
            tail = line[match.end():].strip()
            if tail:
                return tail[:200]
            continue
        return line[:200]
    return "Content multiplier draft"


def ctq_reject_reason(
    text: str,
    mode: str = "verbatim",
    forbidden_strips: list[str] | None = None,
    forbidden_url: str | None = None,
) -> str | None:
    if CTQ_REJECT_RE.search(text or ""):
        return "dash pattern"
    # Block the banned acronym (the 3-letter that means female genital mutilation).
    # Boubacar's hard rule: always "1stGen" or "1stGen Money" in copy.
    # Built from char join so the source itself never contains the literal.
    _banned_acronym = "F" + "G" + "M"
    if _banned_acronym in (text or "") and "1stGen" not in (text or ""):
        return "banned acronym"
    lowered = (text or "").lower()
    for word in BANNED_WORDS:
        if word.lower() in lowered:
            return f"banned word: {word}"
    if mode == "remix":
        # Remix mode forbids any source URL leak in the body.
        if forbidden_url and forbidden_url in (text or ""):
            return "remix leaked source URL"
        for strip in forbidden_strips or []:
            if not strip:
                continue
            # Reject if the model reproduced a flagged quote/stat verbatim.
            if strip.strip() and strip.strip().lower() in lowered:
                return "remix reproduced forbidden strip"
    return None


def _generate_pieces_parallel(
    doc: SourceDoc,
    lens: dict[str, Any],
    target_channels: list[str] | None,
    cost_guard: CostGuard,
    mode: str = "verbatim",
    remix_notes: dict[str, Any] | None = None,
) -> tuple[list[GeneratedPiece], list[dict[str, str]]]:
    """Generate pieces with diversity awareness.

    Pattern: piece 1 fires solo (sets the anchor hook + angle). Remaining
    pieces fire in parallel but each receives the prior hooks as a
    DIVERSITY CONSTRAINT. Pieces that return SKIP_NO_NEW_ANGLE are dropped
    instead of producing paraphrase. Cap and floor enforced upstream by
    build_piece_plans.
    """
    plans = build_piece_plans(lens, target_channels)
    generated: list[GeneratedPiece] = []
    dropped: list[dict[str, str]] = []
    forbidden_strips = (remix_notes or {}).get("fixable_strips") or []
    forbidden_url = doc.source_url if mode == "remix" else None

    if not plans:
        return generated, dropped

    def _check_and_collect(plan: PiecePlan, piece: GeneratedPiece) -> bool:
        if piece.body.strip() == "SKIP_NO_NEW_ANGLE":
            dropped.append({"piece_type": plan.piece_type, "reason": "skipped: no new angle"})
            return False
        reason = ctq_reject_reason(
            piece.body,
            mode=mode,
            forbidden_strips=forbidden_strips,
            forbidden_url=forbidden_url,
        )
        if reason:
            dropped.append({"piece_type": plan.piece_type, "reason": reason})
            return False
        generated.append(piece)
        return True

    # Piece 1 fires solo to set the anchor hook + angle.
    first_plan = plans[0]
    try:
        first_piece = _generate_one_piece(doc, lens, first_plan, cost_guard, mode, remix_notes)
        _check_and_collect(first_plan, first_piece)
    except Exception as exc:
        logger.exception("content multiplier piece failed: %s", first_plan.piece_type)
        dropped.append({"piece_type": first_plan.piece_type, "reason": str(exc)})

    if len(plans) == 1:
        return generated, dropped

    # Remaining pieces fire in parallel with diversity context.
    diversity_lines = "\n".join(
        f"- piece {p.plan.number} ({p.plan.piece_type}): {p.hook[:160]}"
        for p in generated
    )
    rest_plans = plans[1:]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(
                _generate_one_piece, doc, lens, plan, cost_guard, mode,
                remix_notes, diversity_lines,
            ): plan
            for plan in rest_plans
        }
        for future in concurrent.futures.as_completed(future_map):
            plan = future_map[future]
            try:
                piece = future.result()
                _check_and_collect(plan, piece)
            except Exception as exc:
                logger.exception("content multiplier piece failed: %s", plan.piece_type)
                dropped.append({"piece_type": plan.piece_type, "reason": str(exc)})
    generated.sort(key=lambda p: (p.plan.number, p.plan.piece_type))
    return generated, dropped


def _notion_secret() -> str:
    secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
    if not secret:
        raise RuntimeError("NOTION_SECRET, NOTION_API_KEY, or NOTION_TOKEN is required for Notion writes.")
    return secret


def _content_db_id() -> str:
    return os.environ.get("FORGE_CONTENT_DB") or CONTENT_DB_ID


def _notion_client():
    from skills.forge_cli.notion_client import NotionClient

    return NotionClient(secret=_notion_secret())


def _rich_text(text: str) -> dict[str, Any]:
    return {"rich_text": [{"text": {"content": (text or "")[:2000]}}]}


def _title(text: str) -> dict[str, Any]:
    return {"title": [{"text": {"content": (text or "Untitled")[:200]}}]}


def _select(name: str) -> dict[str, Any]:
    return {"select": {"name": name}}


def _multi(names: list[str]) -> dict[str, Any]:
    return {"multi_select": [{"name": name[:100]} for name in names if name]}


def _url(url: str) -> dict[str, Any]:
    return {"url": url if url.startswith("http") else None}


def _has_prop(schema: dict[str, Any], name: str) -> bool:
    return not schema or name in schema


def _write_piece_to_notion(
    notion: Any,
    db_id: str,
    schema: dict[str, Any],
    piece: GeneratedPiece,
    doc: SourceDoc,
    lens: dict[str, Any],
    run_id: str,
    source_trend_notion_id: str | None,
    source_treatment: str = "verbatim",
) -> dict[str, Any]:
    draft = piece.body
    missing_guarded = []
    for guarded in ("Multiplier Run ID", "Piece Type", "Source Treatment"):
        if schema and guarded not in schema:
            missing_guarded.append(guarded)
    if missing_guarded:
        logger.warning("Content Board missing optional multiplier properties: %s", ", ".join(missing_guarded))
        draft = (
            f"Multiplier Run ID: {run_id}\n"
            f"Piece Type: {piece.plan.piece_type}\n"
            f"Source Treatment: {source_treatment}\n\n"
            f"{draft}"
        )

    props: dict[str, Any] = {}
    # Remix mode never writes the source URL into the Notion record body.
    source_url_value = doc.source_url if source_treatment == "verbatim" else ""
    # Platform is a multi_select on the Content Board (LinkedIn, X, YouTube,
    # Newsletter, etc.). Send as multi even though each piece targets one
    # platform.
    platform_value = _multi([piece.plan.platform]) if piece.plan.platform else _multi([])
    # Topic is an Apollo-style multi_select with controlled options. Lens
    # names will not match the existing option list, so we skip writing
    # them here. The lens names live in the prepended Draft body header
    # for now; future extension can map lens to Topic options.
    candidates = {
        "Title": _title(piece.hook),
        "Status": _select(_initial_status_for_piece_type(piece.plan.piece_type)),
        "Platform": platform_value,
        "Draft": _rich_text(draft),
        "Hook": _rich_text(piece.hook),
        "Source URL": _url(source_url_value),
        "Multiplier Run ID": _rich_text(run_id),
        "Piece Type": _select(piece.plan.piece_type),
        "Source Treatment": _select(source_treatment),
        "Created From": _rich_text(source_trend_notion_id or ""),
    }
    for name, value in candidates.items():
        if _has_prop(schema, name):
            props[name] = value
        else:
            logger.warning("Content Board property missing, skipping: %s", name)
    return notion.create_page(database_id=db_id, properties=props)


def _write_pieces_to_notion(
    pieces: list[GeneratedPiece],
    doc: SourceDoc,
    lens: dict[str, Any],
    run_id: str,
    source_trend_notion_id: str | None,
    source_treatment: str = "verbatim",
) -> list[dict[str, Any]]:
    notion = _notion_client()
    db_id = _content_db_id()
    schema = notion.get_database_schema(db_id)
    pages = []
    for piece in pieces:
        pages.append(
            _write_piece_to_notion(
                notion,
                db_id,
                schema,
                piece,
                doc,
                lens,
                run_id,
                source_trend_notion_id,
                source_treatment=source_treatment,
            )
        )
    return pages


def _review_url(run_id: str) -> str:
    db_id = _content_db_id().replace("-", "")
    return f"https://www.notion.so/{db_id}?v=content_multiplier&run_id={run_id}"


def _send_batch_review(title: str, count: int, run_id: str) -> bool:
    chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        logger.warning("content multiplier Telegram skipped because no chat id is configured.")
        return False
    from notifier import send_message_with_buttons

    text = f"Trend [{title}] yielded {count} pieces. Review: {_review_url(run_id)}"
    buttons = [
        [
            ("Approve all", f"multiplier_approve_all:{run_id}"),
            ("Per-piece review", f"multiplier_per_piece:{run_id}"),
            ("Reject all", f"multiplier_reject_all:{run_id}"),
        ]
    ]
    return send_message_with_buttons(str(chat_id), text, buttons) is not None


def multiply_source(
    source_url: str,
    source_type: str = "auto",
    target_channels: list[str] | None = None,
    source_trend_notion_id: str | None = None,
    mode: str = "auto",
    qa_verdict: str | None = None,
    remix_notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Multiply ONE source into N atomic content pieces.

    mode:
      verbatim -- cite source, may quote, attribute stats.
      remix    -- strip unverifiable bits, no citation, Boubacar's original take.
      auto     -- pick from qa_verdict (qa-passed -> verbatim, qa-remix -> remix,
                  qa-failed -> abort).

    qa_verdict + remix_notes are required when mode resolves to remix.
    remix_notes shape: {"fixable_strips": [...], "concept_to_keep": "...", "remix_hint": "..."}
    """
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}, got {mode!r}")
    if mode == "auto":
        if qa_verdict == "qa-failed":
            return {
                "run_id": None,
                "pieces_written": 0,
                "pieces_dropped": 0,
                "telegram_sent": False,
                "mode": "auto",
                "skip_reason": "qa-failed",
            }
        resolved_mode = "remix" if qa_verdict == "qa-remix" else "verbatim"
    else:
        resolved_mode = mode

    if resolved_mode == "remix" and not remix_notes:
        # Remix without notes degrades to a stricter verbatim that still
        # withholds the source URL. Log so future runs supply notes from QA.
        logger.warning("remix mode invoked without remix_notes; running stricter verbatim instead.")
        resolved_mode = "verbatim"

    doc = ingest_source(source_url, source_type)
    lens = classify_lens(doc)
    skip_reason = str(lens.get("skip_reason") or "").strip()
    if skip_reason:
        return {
            "run_id": None,
            "pieces_written": 0,
            "pieces_dropped": 0,
            "telegram_sent": False,
            "mode": resolved_mode,
            "skip_reason": skip_reason,
        }

    run_id = f"{hashlib.sha256(source_url.encode('utf-8')).hexdigest()[:8]}_{int(time.time())}"
    cost_guard = CostGuard()
    pieces, dropped = _generate_pieces_parallel(
        doc, lens, target_channels, cost_guard, mode=resolved_mode, remix_notes=remix_notes
    )
    if not pieces:
        logger.error("content multiplier produced no publishable pieces for run %s", run_id)
        return {
            "run_id": run_id,
            "pieces_written": 0,
            "pieces_dropped": len(dropped),
            "telegram_sent": False,
            "mode": resolved_mode,
        }

    pages = _write_pieces_to_notion(
        pieces, doc, lens, run_id, source_trend_notion_id, source_treatment=resolved_mode
    )
    telegram_sent = _send_batch_review(doc.title, len(pages), run_id)
    return {
        "run_id": run_id,
        "pieces_written": len(pages),
        "pieces_dropped": len(dropped),
        "telegram_sent": telegram_sent,
        "mode": resolved_mode,
    }


def _plain_text_prop(page: dict[str, Any], prop_name: str) -> str:
    prop = (page.get("properties") or {}).get(prop_name) or {}
    ptype = prop.get("type")
    data = prop.get(ptype) if ptype else None
    if ptype == "title" or ptype == "rich_text":
        return "".join(part.get("plain_text", "") for part in data or [])
    if ptype == "url":
        return data or ""
    if ptype == "select":
        return (data or {}).get("name", "")
    return ""


def _source_from_page(page: dict[str, Any]) -> str:
    for prop in ("Source URL", "URL", "Link"):
        value = _plain_text_prop(page, prop)
        if value:
            return value
    draft = _plain_text_prop(page, "Draft")
    if draft:
        return draft
    raise ValueError(f"Multiply record has no Source URL, URL, Link, or Draft: {page.get('id')}")


def _remix_notes_from_page(page: dict[str, Any]) -> dict[str, Any] | None:
    """Pull remix triage from the QA verdict record. Returns None if absent."""
    fixable_raw = _plain_text_prop(page, "Fixable Strips")
    concept = _plain_text_prop(page, "Concept To Keep")
    hint = _plain_text_prop(page, "Remix Hint")
    if not (fixable_raw or concept or hint):
        return None
    fixable = [s.strip() for s in (fixable_raw or "").split("|") if s.strip()]
    return {"fixable_strips": fixable, "concept_to_keep": concept, "remix_hint": hint}


def multiply_from_page_id(page_id: str) -> dict[str, Any]:
    """Fetch a Notion Content Board page, extract its source URL + QA fields, and multiply.

    Used by scout_approve immediate-fire and /multiply <notion_page_id>.
    Mirrors the extraction path inside multiplier_tick() so the poller and
    on-demand triggers behave identically. On success, sets Status -> Idea.
    """
    notion = _notion_client()
    page = notion.get_page(page_id)
    source = _source_from_page(page)
    qa_verdict = _plain_text_prop(page, "QA Verdict") or None
    remix_notes = _remix_notes_from_page(page)
    result = multiply_source(
        source,
        source_type="auto",
        source_trend_notion_id=page_id,
        mode="auto",
        qa_verdict=qa_verdict,
        remix_notes=remix_notes,
    )
    notion.update_page(page_id, properties={"Status": {"select": {"name": "Idea"}}})
    return result


def multiplier_tick() -> None:
    if not _MULTIPLIER_LOCK.acquire(blocking=False):
        logger.info("content multiplier tick: already running, skipping.")
        return
    try:
        notion = _notion_client()
        db_id = _content_db_id()
        rows = notion.query_database(
            db_id,
            filter_obj={"property": "Status", "select": {"equals": "Multiply"}},
            sorts=[{"timestamp": "created_time", "direction": "ascending"}],
        )
        if not rows:
            logger.info("content multiplier tick: no Multiply records.")
            return

        page = rows[0]
        page_id = page["id"]
        source = _source_from_page(page)
        qa_verdict = _plain_text_prop(page, "QA Verdict") or None
        remix_notes = _remix_notes_from_page(page)
        try:
            multiply_source(
                source,
                source_type="auto",
                source_trend_notion_id=page_id,
                mode="auto",
                qa_verdict=qa_verdict,
                remix_notes=remix_notes,
            )
            notion.update_page(page_id, properties={"Status": {"select": {"name": "Idea"}}})
        except Exception:
            logger.exception("content multiplier tick failed for page %s", page_id)
            raise
    finally:
        _MULTIPLIER_LOCK.release()

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the agentsHQ content multiplier.")
    parser.add_argument("source", help="URL, YouTube URL, PDF URL, local PDF path, or raw text.")
    parser.add_argument("--source-type", default="auto", choices=["auto", "url", "youtube", "text", "pdf"])
    parser.add_argument("--channels", default="", help="Comma-separated channel_fit filter.")
    parser.add_argument("--mode", default="auto", choices=list(VALID_MODES),
                        help="verbatim cites source; remix strips unverifiable; auto picks from --qa-verdict.")
    parser.add_argument("--qa-verdict", default=None, choices=[None, "qa-passed", "qa-remix", "qa-failed"],
                        help="Used when --mode=auto.")
    parser.add_argument("--remix-strips", default="", help="Comma-separated quotes/stats to drop in remix mode.")
    parser.add_argument("--concept-keep", default="", help="One-line salvageable angle for remix mode.")
    parser.add_argument("--remix-hint", default="", help="Reframing direction for remix mode.")
    args = parser.parse_args(argv)
    channels = [c.strip() for c in args.channels.split(",") if c.strip()] or None
    remix_notes = None
    if args.remix_strips or args.concept_keep or args.remix_hint:
        remix_notes = {
            "fixable_strips": [s.strip() for s in args.remix_strips.split(",") if s.strip()],
            "concept_to_keep": args.concept_keep,
            "remix_hint": args.remix_hint,
        }
    result = multiply_source(
        args.source,
        source_type=args.source_type,
        target_channels=channels,
        mode=args.mode,
        qa_verdict=args.qa_verdict,
        remix_notes=remix_notes,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
