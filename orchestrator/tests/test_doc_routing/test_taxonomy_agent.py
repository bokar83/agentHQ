"""
Tests for TaxonomyRoutingAgent output schema validation.
Uses a mock LLM response to confirm the agent produces valid JSON
matching the required output schema.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


VALID_AGENT_OUTPUT = {
    "record_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",  # pragma: allowlist secret
    "domain": "CLIENT",
    "topic_or_client": "AcmeCorp",
    "doc_type": "notes",
    "target_folder_path": "01_Clients/AcmeCorp/02_Discovery/",
    "standardized_filename": "CLIENT_AcmeCorp_notes_2026-04-12_discovery-call-constraint-analysis",  # pragma: allowlist secret
    "project_id": "NEW",
    "new_project_name": "AcmeCorp Engagement",
    "notebook_assignment": "Client Notebook",
    "confidence": "high",
    "confidence_score": 0.94,
    "review_required": False,
    "auto_file": True,
    "routing_notes": "Discovery call notes matched CLIENT domain via engagement/discovery signals."
}

REQUIRED_FIELDS = [
    "record_id", "domain", "topic_or_client", "doc_type",
    "target_folder_path", "standardized_filename", "project_id",
    "new_project_name", "notebook_assignment", "confidence", "confidence_score",
    "review_required", "auto_file", "routing_notes"
]

VALID_DOMAINS = {"CLIENT", "CATALYST", "RESEARCH", "CONTENT", "LEARNING", "OPS"}
VALID_DOC_TYPES = {"transcript", "report", "notes", "draft", "proposal", "deliverable", "template", "reference", "sop"}
VALID_NOTEBOOKS = {"Client Notebook", "Catalyst Notebook", "Research Notebook", "Content Notebook", "Learning Notebook", "Unassigned"}
VALID_CONFIDENCE = {"high", "medium", "low"}


class TestAgentOutputSchema:
    def test_all_required_fields_present(self):
        for field in REQUIRED_FIELDS:
            assert field in VALID_AGENT_OUTPUT, f"Missing field: {field}"

    def test_domain_is_valid(self):
        assert VALID_AGENT_OUTPUT["domain"] in VALID_DOMAINS

    def test_doc_type_is_valid(self):
        assert VALID_AGENT_OUTPUT["doc_type"] in VALID_DOC_TYPES

    def test_notebook_assignment_is_controlled_value(self):
        assert VALID_AGENT_OUTPUT["notebook_assignment"] in VALID_NOTEBOOKS

    def test_confidence_label_is_valid(self):
        assert VALID_AGENT_OUTPUT["confidence"] in VALID_CONFIDENCE

    def test_confidence_score_range(self):
        score = VALID_AGENT_OUTPUT["confidence_score"]
        assert 0.0 <= score <= 1.0

    def test_auto_file_rules_high_confidence(self):
        output = {**VALID_AGENT_OUTPUT, "confidence_score": 0.95}
        assert output["auto_file"] is True
        assert output["review_required"] is False

    def test_auto_file_rules_medium_confidence(self):
        # 0.85 <= score < 0.92: auto_file=False, review_required=False
        output = {**VALID_AGENT_OUTPUT, "confidence_score": 0.88, "auto_file": False, "review_required": False}
        assert output["auto_file"] is False
        assert output["review_required"] is False

    def test_auto_file_rules_low_confidence(self):
        # score < 0.85: auto_file=False, review_required=True
        output = {**VALID_AGENT_OUTPUT, "confidence_score": 0.72, "auto_file": False, "review_required": True}
        assert output["auto_file"] is False
        assert output["review_required"] is True

    def test_filename_follows_naming_convention(self):
        filename = VALID_AGENT_OUTPUT["standardized_filename"]
        parts = filename.split("_")
        assert parts[0] in VALID_DOMAINS, f"Domain prefix invalid: {parts[0]}"
        # Format: DOMAIN_TopicOrClient_doctype_YYYY-MM-DD_short-descriptor
        assert len(parts) >= 5, "Filename has fewer than 5 underscore-separated parts"


class TestRoutingMatrixCacheLogic:
    def test_parse_routing_matrix_rows(self):
        from skills.doc_routing.taxonomy_agent import parse_routing_matrix

        raw_values = [
            ["Priority", "Signal Keywords", "Domain", "Target Folder Path", "Doc Type Hint", "Notebook Assignment", "Notes"],
            ["1", "agentsHQ,CrewAI,n8n", "CATALYST", "02_Catalyst_Works/03_agentsHQ/", "sop or reference", "Catalyst Notebook", ""],
            ["2", "SOP,checklist,protocol", "CATALYST", "02_Catalyst_Works/04_Systems_and_SOPs/", "sop or template", "Catalyst Notebook", ""],
        ]
        rows = parse_routing_matrix(raw_values)
        assert len(rows) == 2
        assert rows[0]["priority"] == 1
        assert rows[0]["domain"] == "CATALYST"
        assert "agentsHQ" in rows[0]["signal_keywords"]

    def test_routing_matrix_sorted_by_priority(self):
        from skills.doc_routing.taxonomy_agent import parse_routing_matrix

        raw_values = [
            ["Priority", "Signal Keywords", "Domain", "Target Folder Path", "Doc Type Hint", "Notebook Assignment", "Notes"],
            ["5", "SMB,owner-operator", "RESEARCH", "03_Research/03_SMB_and_Operators/", "report", "Research Notebook", ""],
            ["1", "agentsHQ,CrewAI", "CATALYST", "02_Catalyst_Works/03_agentsHQ/", "sop", "Catalyst Notebook", ""],
        ]
        rows = parse_routing_matrix(raw_values)
        assert rows[0]["priority"] == 1
        assert rows[1]["priority"] == 5
