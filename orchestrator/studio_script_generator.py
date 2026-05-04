"""
studio_script_generator.py — Studio M3: Script generation from Pipeline DB candidate.

Input:  candidate dict (hook, twist, niche, title, channel_id)
        brand_config dict (loaded via studio_brand_config.load_brand_config)
Output: script dict (title, full_text, scenes_hint, word_count, estimated_duration_sec)

Enforces:
  - Hook in first 30 words
  - Retention loop trigger (curiosity/cliffhanger) every ~200 words
  - CTA in final paragraph
  - Pronunciation-safe (SSML phonetic tags injected for ElevenLabs)
  - No em-dashes (house rule: use commas/periods instead)
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentsHQ.studio_script_generator")

_DEFAULT_TARGET_WORDS = 1500  # ~10 minutes at 150 wpm

_DOSSIER_DIR = Path(__file__).parent.parent / "research-vault" / "dossiers"
_CHANNEL_DOSSIER_MAP = {
    "under_the_baobab": "under_the_baobab.md",
    "under-the-baobab": "under_the_baobab.md",
    "ai_catalyst": "ai_catalyst.md",
    "ai-catalyst": "ai_catalyst.md",
    "first_generation_money": "first_generation_money.md",
    "first-generation-money": "first_generation_money.md",
    "1stgen": "first_generation_money.md",
}


def _load_dossier(channel_id: str) -> str:
    slug = channel_id.lower().replace(" ", "_")
    filename = _CHANNEL_DOSSIER_MAP.get(slug) or _CHANNEL_DOSSIER_MAP.get(channel_id.lower())
    if not filename:
        return ""
    path = _DOSSIER_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def generate_script(
    candidate: dict[str, Any],
    brand: dict[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Generate a full video script from a trend-scout candidate.

    Returns:
        {
            "title": str,
            "full_text": str,          # narration-ready, SSML-tagged
            "scenes_hint": list[str],  # rough scene break markers for scene_builder
            "word_count": int,
            "estimated_duration_sec": int,
        }
    """
    hook = candidate.get("hook") or candidate.get("title") or "Unknown hook"
    twist = candidate.get("twist") or candidate.get("angle") or ""
    niche = candidate.get("niche") or "general"
    title = candidate.get("title") or hook
    channel_id = candidate.get("channel_id") or brand.get("channel_id", "unknown")

    script_tone = brand.get("script_tone", "warm, storytelling")
    visual_style = brand.get("visual_style", "cinematic")
    target_duration = brand.get("target_duration_sec", 600)
    hook_budget = brand.get("hook_word_budget", 30)
    loop_interval = brand.get("retention_loop_interval_words", 200)
    target_words = int(target_duration / 60 * 150)  # 150 wpm average

    pronunciation_dict = brand.get("pronunciation_dict", {})

    voice_role = _select_voice_role(niche, channel_id)
    dossier = _load_dossier(channel_id)

    if dry_run:
        logger.info("[dry_run] script_generator skipping LLM call for '%s'", title)
        stub = _stub_script(title, target_words)
        stub["voice_role"] = voice_role
        return stub

    system_prompt = _build_system_prompt(
        channel_id, script_tone, visual_style, hook_budget, loop_interval, target_words,
        dossier=dossier,
    )
    user_prompt = _build_user_prompt(hook, twist, niche, title)

    raw_script = _call_llm(system_prompt, user_prompt)
    clean_script = _post_process(raw_script, pronunciation_dict, loop_interval)

    word_count = len(clean_script.split())
    duration_sec = int(word_count / 150 * 60)
    scenes_hint = _extract_scene_hints(clean_script)

    return {
        "title": title,
        "full_text": clean_script,
        "scenes_hint": scenes_hint,
        "word_count": word_count,
        "estimated_duration_sec": duration_sec,
        "voice_role": voice_role,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_system_prompt(
    channel_id: str,
    tone: str,
    visual_style: str,
    hook_budget: int,
    loop_interval: int,
    target_words: int,
    *,
    dossier: str = "",
) -> str:
    dossier_block = ""
    if dossier:
        dossier_block = f"\n\nCHANNEL INTELLIGENCE DOSSIER — use this to inform hooks, topics, and angle choices:\n{dossier}\n"
    return f"""You are a professional YouTube scriptwriter for the "{channel_id}" channel.{dossier_block}

VOICE AND TONE: {tone}
VISUAL STYLE THIS CHANNEL USES: {visual_style}

HARD RULES — follow exactly:
1. Hook MUST appear in the first {hook_budget} words. It must name a felt problem or surprising fact. NO generic intros.
2. 4-PART FORMULA — every script must follow this structure in order:
   - HOOK (first {hook_budget} words): felt problem or surprising fact — stops the scroll
   - VALUE BODY: useful, surprising, or specific information — deliver immediately after hook
   - CURIOSITY GAP (at least once before the final 10%): leave something slightly incomplete to trigger rewatch or continued watching. Use phrases like "But here is the part nobody talks about" or a [RETENTION:] marker.
   - LOOP ENDING (final paragraph): close with a question, a rewatch trigger, or a "watch next" CTA — make the viewer want to loop or continue.
3. RETENTION LOOPS — required every {loop_interval} words without exception. Insert a line in this exact format:
   [RETENTION: phrase]
   Where phrase is one of: "But here is the part nobody talks about." / "Stay with me, because this is where it gets surprising." / "Here is what the research actually shows." / "And this next part changes everything." / "Most people get this completely wrong."
   These ARE narrated aloud — they are spoken by the narrator to keep viewers watching.
4. End with a clear CTA (subscribe, share, or watch another video) in the last paragraph.
5. Target length: ~{target_words} words ({target_words // 150} minutes at 150 wpm).
6. NO em-dashes (use commas or periods instead).
7. NO first-person Boubacar references. This is a faceless channel.
8. NO fabricated client stories or testimonials.
9. NO alcohol, coffee, or substance imagery.
10. EVERY factual claim MUST have a named source inline. Format: "according to [University/Organization] researchers" or "a [year] [Journal] study found". NO bare claims like "scientists discovered" or "research shows" without naming the source. If you cannot name a real source, reframe as an observation rather than a study claim.
11. Write for narration — spoken aloud, not read. Short sentences. Active voice.

SCENE MARKERS: After every 150-200 words, insert a line in the format:
[SCENE: brief visual description for the visual team]
These help the visual team, not the narrator — do not narrate them.

RETENTION MARKER EXAMPLE (correct):
...The brain forms more than one million new neural connections per second in the first three years of life.
[RETENTION: But here is the part nobody talks about.]
That number drops by half before a child's fifth birthday...

OUTPUT: Return only the script text. No preamble, no "Here is your script", no metadata."""


def _build_user_prompt(hook: str, twist: str, niche: str, title: str) -> str:
    parts = [
        f'VIDEO TITLE: "{title}"',
        f'OPENING LINE (use this or riff from it): {hook}',
    ]
    if twist:
        parts.append(
            f'VIDEO CONCEPT BRIEF (who this is for, what insight it delivers, how it ends):\n{twist}'
        )
    parts.append(f'NICHE: {niche}')
    parts.append(
        "Write the full script now. Follow the concept brief exactly — "
        "this video was designed for a specific audience, not a generic one."
    )
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Post-processing
# ─────────────────────────────────────────────────────────────────────────────

_RETENTION_PHRASES = [
    "But here is the part nobody talks about.",
    "Stay with me, because this is where it gets surprising.",
    "And this next part changes everything.",
    "Most people get this completely wrong.",
    "Here is what actually happens next.",
]


def _inject_retention_loops(text: str, interval: int = 200) -> str:
    """Ensure a [RETENTION:] marker appears at least every `interval` words.
    Inserts one at the nearest paragraph break if a segment is missing one.
    """
    paragraphs = text.split("\n\n")
    result = []
    words_since_retention = 0
    phrase_idx = 0

    for para in paragraphs:
        has_retention = bool(re.search(r'\[RETENTION:', para))
        word_count = len(para.split())

        if not has_retention and (words_since_retention + word_count) >= interval:
            phrase = _RETENTION_PHRASES[phrase_idx % len(_RETENTION_PHRASES)]
            phrase_idx += 1
            para = para.rstrip() + f"\n[RETENTION: {phrase}]"
            words_since_retention = 0
        elif has_retention:
            words_since_retention = 0
        else:
            words_since_retention += word_count

        result.append(para)

    return "\n\n".join(result)


def _post_process(text: str, pronunciation_dict: dict[str, str], loop_interval: int = 200) -> str:
    # Strip em-dashes (house rule)
    text = text.replace("—", ", ").replace(" -- ", ", ")

    # Guarantee retention loops every loop_interval words
    text = _inject_retention_loops(text, loop_interval)

    # Apply SSML phonetic tags for ElevenLabs pronunciation
    for word, phonetic in pronunciation_dict.items():
        escaped = re.escape(word)
        ssml_tag = f'<phoneme alphabet="ipa" ph="{phonetic}">{word}</phoneme>'
        text = re.sub(rf'\b{escaped}\b', ssml_tag, text)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text.strip())
    return text


def _extract_scene_hints(text: str) -> list[str]:
    """Pull [SCENE: ...] markers the LLM inserted."""
    return re.findall(r'\[SCENE:\s*([^\]]+)\]', text)


# ─────────────────────────────────────────────────────────────────────────────
# LLM call
# ─────────────────────────────────────────────────────────────────────────────

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    from llm_helpers import call_llm

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    # Sonnet for script quality — this is brand-published content
    response = call_llm(
        messages,
        model="anthropic/claude-sonnet-4-6",
        max_tokens=4096,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────────────────────────────────────
# Voice role selection
# ─────────────────────────────────────────────────────────────────────────────

# Niche → voice role mapping. Script generator sets this; voice generator resolves
# the actual ElevenLabs voice_id from voice_registry.json.
_NICHE_VOICE_ROLES: dict[str, str] = {
    "african-folktales":    "male",    # warm male narrator default for folktales
    "parenting-psychology": "female",  # female voice tests better for parenting content
    "ai-displacement":      "boubacar",
    "ai-displacement-first-gen": "boubacar",
    "first-gen-money":      "hunter",
    "ai-governance-regulation": "boubacar",
    "ai-adoption-what-works":   "boubacar",
    "ai-tools-smb":             "boubacar",
}

# Channel → default voice role (used when niche has no explicit mapping)
_CHANNEL_VOICE_ROLES: dict[str, str] = {
    "ai_catalyst":    "boubacar",
    "catalyst_works": "boubacar",
    "under_the_baobab": "male",
}


def _select_voice_role(niche: str, channel_id: str) -> str:
    """Return voice role string for this niche/channel combination.

    Callers can override by setting script["voice_role"] after generation.
    Use "elder" explicitly in script metadata when content calls for a wisdom
    narrator (e.g. folktale told by village elder character).
    """
    if niche in _NICHE_VOICE_ROLES:
        return _NICHE_VOICE_ROLES[niche]
    if channel_id in _CHANNEL_VOICE_ROLES:
        return _CHANNEL_VOICE_ROLES[channel_id]
    return "male"  # default


# ─────────────────────────────────────────────────────────────────────────────
# Stub for smoke-test / dry-run
# ─────────────────────────────────────────────────────────────────────────────

def _stub_script(title: str, target_words: int = 0) -> dict[str, Any]:  # noqa: ARG001
    text_parts = [
        f"[STUB SCRIPT] {title}\n\n",
        "Have you ever wondered why some children grow into confident adults while others carry invisible wounds for decades? "
        "The answer lies in something that happens before a child even learns to speak.\n\n",
        "[SCENE: close-up of parent and toddler, warm afternoon light]\n\n",
        "Scientists at Harvard discovered that the first three years of a child's life wire their brain in ways that last a lifetime. "
        "And most parents have no idea this window is closing.\n\n",
        "[SCENE: brain scan imagery with soft overlay]\n\n",
        "Here is the part nobody talks about. The way you respond to a crying baby does not just comfort them in the moment. "
        "It physically shapes the architecture of their nervous system.\n\n",
        "[SCENE: parent picking up infant, gentle slow motion]\n\n",
        "By the end of this video, you will understand exactly what secure attachment looks like, "
        "why it matters more than any school or sport, and three things you can do starting tonight.\n\n",
        "[SCENE: warm family home, evening, candles]\n\n",
        "If this changes how you see parenting, share it with someone who needs to hear it. "
        "And watch the next video to go deeper into attachment styles.\n",
    ]
    full_text = "".join(text_parts)
    word_count = len(full_text.split())
    return {
        "title": title,
        "full_text": full_text,
        "scenes_hint": _extract_scene_hints(full_text),
        "word_count": word_count,
        "estimated_duration_sec": int(word_count / 150 * 60),
    }
