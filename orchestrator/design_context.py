"""
design_context.py — Design Context Loader
==========================================
Reads Catalyst Works styleguide files and awesome-design-md
reference files from disk. Returns formatted strings for
injection into CrewAI task descriptions.

Path resolution uses __file__ so it works regardless of
working directory — critical for Docker container execution.

Adding a new task type:
  Add an entry to STYLEGUIDE_MAP pointing to the relevant
  styleguide file(s). No other changes needed.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Base directories — resolved relative to this file for Docker compatibility
_BASE = os.path.dirname(os.path.abspath(__file__))
_DOCS_DIR = os.path.join(_BASE, "..", "docs")


class DesignContextLoader:
    """
    Loads design context for injection into visual crew task descriptions.

    Usage in a crew builder function:
        design_ctx = DesignContextLoader.load("website_build")
        # design_ctx is "" if files missing — crew runs without design layer

    Usage in design agent tasks:
        reference = DesignContextLoader.load_reference("linear")
    """

    # Override these in tests via monkeypatch
    _STYLEGUIDE_DIR: str = os.path.join(_DOCS_DIR, "styleguides")
    _REFERENCES_DIR: str = os.path.join(_DOCS_DIR, "design-references")
    _DECISIONS_DIR: str = os.path.join(_DOCS_DIR, "design-decisions")

    # Maps task_type to list of styleguide filenames to load (in order)
    STYLEGUIDE_MAP: dict = {
        "website_build":          ["styleguide_master.md", "styleguide_websites.md"],
        "3d_website_build":       ["styleguide_master.md", "styleguide_websites.md"],
        "app_build":              ["styleguide_master.md", "styleguide_websites.md"],
        "consulting_deliverable": ["styleguide_master.md", "styleguide_pdf_documents.md"],
        "general_writing":        ["styleguide_master.md", "styleguide_markdown.md"],
        "social_content":         ["styleguide_master.md", "styleguide_linkedin.md"],
        "linkedin_x_campaign":    [
            "styleguide_master.md",
            "styleguide_linkedin.md",
            "styleguide_x_twitter.md",
        ],
        "design_review":          ["styleguide_master.md"],
    }

    @classmethod
    def load(cls, task_type: str) -> str:
        """
        Return formatted design context string for the given task type.
        Returns "" if task_type not in STYLEGUIDE_MAP or files not found.
        Failure is always silent — crews must handle "" gracefully.
        """
        filenames = cls.STYLEGUIDE_MAP.get(task_type)
        if not filenames:
            return ""

        sections = []
        for filename in filenames:
            path = os.path.join(cls._STYLEGUIDE_DIR, filename)
            content = cls._read_file(path)
            if content:
                sections.append(content)

        if not sections:
            return ""

        combined = "\n\n---\n\n".join(sections)
        return (
            "\n\n=== CATALYST WORKS DESIGN SYSTEM ===\n\n"
            + combined
            + "\n\n=== END DESIGN SYSTEM ===\n"
        )

    @classmethod
    def load_reference(cls, reference_name: str) -> str:
        """
        Load a single awesome-design-md reference by name (e.g. 'linear', 'stripe').
        Returns "" if the reference file does not exist.
        """
        # Try exact name first, then with .md extension
        for candidate in [reference_name, f"{reference_name}.md"]:
            path = os.path.join(cls._REFERENCES_DIR, candidate)
            content = cls._read_file(path)
            if content:
                return content

        # Try DESIGN.md inside a subdirectory (some references use this structure)
        path = os.path.join(cls._REFERENCES_DIR, reference_name, "DESIGN.md")
        return cls._read_file(path)

    @classmethod
    def load_index(cls) -> str:
        """Load the design references INDEX.md for agent selection."""
        path = os.path.join(cls._REFERENCES_DIR, "INDEX.md")
        return cls._read_file(path)

    @classmethod
    def load_decision(cls, project_slug: str) -> str:
        """Load a prior design decision for a project. Returns "" if not found."""
        path = os.path.join(cls._DECISIONS_DIR, f"{project_slug}.md")
        return cls._read_file(path)

    @classmethod
    def save_decision(cls, project_slug: str, content: str) -> bool:
        """Save a design decision file. Returns True on success."""
        try:
            os.makedirs(cls._DECISIONS_DIR, exist_ok=True)
            path = os.path.join(cls._DECISIONS_DIR, f"{project_slug}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.warning(f"Could not save design decision for {project_slug}: {e}")
            return False

    @classmethod
    def _read_file(cls, path: str) -> str:
        """Read a file and return its content. Returns "" on any error."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
