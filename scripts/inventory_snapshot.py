"""
inventory_snapshot.py - Generate a structured snapshot of agentsHQ capability.

Walks skills/, orchestrator/, top-level requirements/.env, and writes:
  - docs/agentsHQ_inventory.md   (human-readable)
  - docs/agentsHQ_inventory.json (machine-readable, used by harvest-reviewer)

Read at the start of any work that needs to know "what do we already have?":
  - harvest-reviewer (decide if a Skool lesson overlaps with us)
  - skill-creator (avoid duplicating)
  - council prompts ("what already exists?")

Run after adding/removing skills or major orchestrator modules.

Usage:
    python scripts/inventory_snapshot.py
"""

from __future__ import annotations

import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
ORCH_DIR = REPO_ROOT / "orchestrator"
DOCS_DIR = REPO_ROOT / "docs"
ENV_PATH = REPO_ROOT / ".env"
REQUIREMENTS_PATH = REPO_ROOT / "orchestrator" / "requirements.txt"


# ---- skills ----------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill(skill_dir: Path) -> dict | None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {
            "slug": skill_dir.name,
            "name": skill_dir.name,
            "description": "(no frontmatter)",
            "size_bytes": skill_md.stat().st_size,
        }
    fm_raw = m.group(1)
    name = _yaml_field(fm_raw, "name") or skill_dir.name
    desc = _yaml_field(fm_raw, "description", multiline=True) or ""
    desc = re.sub(r"\s+", " ", desc).strip()
    body = text[m.end():]
    triggers = _extract_triggers(body)
    files = sorted(p.name for p in skill_dir.iterdir() if p.is_file())
    return {
        "slug": skill_dir.name,
        "name": name,
        "description": desc[:500],
        "trigger_phrases": triggers,
        "files": files,
        "size_bytes": skill_md.stat().st_size,
    }


def _yaml_field(text: str, field: str, multiline: bool = False) -> str | None:
    """Tiny YAML-frontmatter field extractor. Avoids a yaml dependency."""
    if multiline:
        # Match `description: >`, `description: |`, or `description:` followed by
        # indented continuation lines.
        m = re.search(rf"^{re.escape(field)}\s*:\s*[>|]?\s*\n((?:[ \t]+\S.*\n?)+)",
                      text, re.MULTILINE)
        if m:
            lines = [ln.strip() for ln in m.group(1).splitlines()]
            return " ".join(lines)
        m = re.search(rf"^{re.escape(field)}\s*:\s*(.*)$", text, re.MULTILINE)
        return m.group(1).strip() if m else None
    m = re.search(rf"^{re.escape(field)}\s*:\s*(.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _extract_triggers(body: str) -> list[str]:
    """Pull explicit trigger phrases from common patterns."""
    triggers: list[str] = []
    # "Trigger on..." or "Triggers on..." sentences in the body
    for m in re.finditer(r"[Tt]rigger(?:s|s on| on)[^.]{0,300}\.", body):
        chunk = m.group(0)
        for q in re.findall(r'"([^"]{2,50})"', chunk):
            if q not in triggers:
                triggers.append(q)
    # Slash-command style mentions
    for m in re.finditer(r"`?(/[a-z][a-z0-9_-]+)`?", body):
        cmd = m.group(1)
        if cmd not in triggers:
            triggers.append(cmd)
        if len(triggers) >= 12:
            break
    return triggers[:12]


def collect_skills() -> list[dict]:
    if not SKILLS_DIR.exists():
        return []
    out = []
    for sub in sorted(SKILLS_DIR.iterdir()):
        if not sub.is_dir():
            continue
        info = parse_skill(sub)
        if info:
            out.append(info)
    return out


# ---- orchestrator modules --------------------------------------------------

def parse_python_module(path: Path) -> dict:
    """Extract module docstring, public defs/classes, and key string constants."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"file": path.name, "error": f"syntax error: {e}"}

    docstring = (ast.get_docstring(tree) or "").strip()
    docstring_one_line = re.sub(r"\s+", " ", docstring)[:500]

    public_funcs: list[str] = []
    public_classes: list[str] = []
    tool_classes: list[str] = []
    tool_bundles: list[str] = []  # e.g. KIE_MEDIA_TOOLS = [...]

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            public_funcs.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_"):
            public_funcs.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            public_classes.append(node.name)
            # CrewAI BaseTool subclass?
            base_names = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    base_names.append(b.id)
                elif isinstance(b, ast.Attribute):
                    base_names.append(b.attr)
            if "BaseTool" in base_names:
                tool_classes.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    if target.id.endswith("_TOOLS") or target.id.endswith("_BUNDLE"):
                        tool_bundles.append(target.id)

    return {
        "file": path.name,
        "purpose": docstring_one_line,
        "public_functions": public_funcs[:25],
        "public_classes": public_classes[:25],
        "tool_classes": tool_classes,
        "tool_bundles": tool_bundles,
        "lines": len(src.splitlines()),
    }


def collect_orchestrator() -> list[dict]:
    if not ORCH_DIR.exists():
        return []
    out = []
    for path in sorted(ORCH_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        out.append(parse_python_module(path))
    return out


# ---- env vars (key names only, never values) -------------------------------

def collect_env_keys() -> list[str]:
    if not ENV_PATH.exists():
        return []
    keys: list[str] = []
    for line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" in s:
            k = s.split("=", 1)[0].strip()
            if re.fullmatch(r"[A-Z_][A-Z0-9_]*", k):
                keys.append(k)
    return sorted(set(keys))


# ---- requirements ----------------------------------------------------------

def collect_requirements() -> list[str]:
    if not REQUIREMENTS_PATH.exists():
        return []
    out: list[str] = []
    for line in REQUIREMENTS_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


# ---- assemble + write ------------------------------------------------------

def build_inventory() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "skills": collect_skills(),
        "orchestrator_modules": collect_orchestrator(),
        "env_keys": collect_env_keys(),
        "requirements": collect_requirements(),
    }


def render_markdown(inv: dict) -> str:
    lines: list[str] = []
    lines.append(f"# agentsHQ Inventory")
    lines.append("")
    lines.append(f"_Generated: {inv['generated_at']}_")
    lines.append("")
    lines.append("Read this when you need to know what already exists in agentsHQ before "
                 "proposing a new skill, tool, or crew. Regenerate via "
                 "`python scripts/inventory_snapshot.py`.")
    lines.append("")

    skills = inv["skills"]
    lines.append(f"## Skills ({len(skills)})")
    lines.append("")
    lines.append("| Slug | Description (truncated) |")
    lines.append("|---|---|")
    for s in skills:
        desc = (s.get("description") or "").replace("|", "\\|")[:160]
        lines.append(f"| `{s['slug']}` | {desc} |")
    lines.append("")

    om = inv["orchestrator_modules"]
    lines.append(f"## Orchestrator modules ({len(om)})")
    lines.append("")
    lines.append("| File | Purpose | Public funcs | Tool classes | Tool bundles |")
    lines.append("|---|---|---|---|---|")
    for m in om:
        purpose = (m.get("purpose") or "").replace("|", "\\|")[:80]
        funcs = ", ".join((m.get("public_functions") or [])[:6])
        tcs = ", ".join((m.get("tool_classes") or [])[:4])
        tbs = ", ".join((m.get("tool_bundles") or [])[:4])
        lines.append(f"| `{m['file']}` | {purpose} | {funcs} | {tcs} | {tbs} |")
    lines.append("")

    keys = inv["env_keys"]
    lines.append(f"## Environment keys ({len(keys)})")
    lines.append("")
    lines.append("Names only; values live in `.env`.")
    lines.append("")
    lines.append("```")
    for k in keys:
        lines.append(k)
    lines.append("```")
    lines.append("")

    reqs = inv["requirements"]
    lines.append(f"## Python requirements ({len(reqs)})")
    lines.append("")
    lines.append("```")
    for r in reqs:
        lines.append(r)
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    inv = build_inventory()

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DOCS_DIR / "agentsHQ_inventory.json"
    md_path = DOCS_DIR / "agentsHQ_inventory.md"

    json_path.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(inv), encoding="utf-8")

    print(f"[inventory] skills:     {len(inv['skills'])}")
    print(f"[inventory] orch mods:  {len(inv['orchestrator_modules'])}")
    print(f"[inventory] env keys:   {len(inv['env_keys'])}")
    print(f"[inventory] reqs:       {len(inv['requirements'])}")
    print(f"[inventory] wrote {json_path}")
    print(f"[inventory] wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
