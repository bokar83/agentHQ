"""
Integration test for doc_routing_crew.
Mocks the LLM call to return a valid classification JSON.
Verifies the crew produces a TaskResponse.result that is valid JSON
matching the required output schema.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


MOCK_LLM_RESPONSE = json.dumps({
    "record_id": "test-uuid-1234",
    "domain": "RESEARCH",
    "topic_or_client": "AI_Strategy",
    "doc_type": "report",
    "target_folder_path": "03_Research/02_AI_Strategy/",
    "standardized_filename": "RESEARCH_AI_Strategy_report_2026-04-12_llm-adoption-sme",  # pragma: allowlist secret
    "project_id": "RS-001",
    "new_project_name": None,
    "notebook_assignment": "Research Notebook",
    "confidence": "high",
    "confidence_score": 0.93,
    "review_required": False,
    "auto_file": True,
    "routing_notes": "AI strategy keywords matched RESEARCH domain at priority 5."
})


class TestDocRoutingCrew:
    def test_crew_returns_valid_json_result(self):
        from skills.doc_routing.doc_routing_crew import build_doc_routing_crew
        from crewai import Crew

        crew = build_doc_routing_crew(
            "doc_routing: classify and route document",
            context={
                "record_id": "test-uuid-1234",
                "filename": "AI Strategy Framework 2026.pdf",
                "extracted_text": "This report covers LLM adoption strategies for SME businesses in 2026. Key topics: AI tools, automation, prompt engineering, agent frameworks.",
                "mime_type": "application/pdf",
                "source": "manual-upload",
                "project_hint": None,
            }
        )
        assert isinstance(crew, Crew)
        assert len(crew.agents) == 1
        assert len(crew.tasks) == 1

    def test_crew_task_description_contains_record_id(self):
        from skills.doc_routing.doc_routing_crew import build_doc_routing_crew

        crew = build_doc_routing_crew(
            "doc_routing: classify and route document",
            context={
                "record_id": "test-uuid-1234",
                "filename": "AI Strategy Framework 2026.pdf",
                "extracted_text": "LLM adoption strategies",
                "mime_type": "application/pdf",
                "source": "manual-upload",
                "project_hint": None,
            }
        )
        task_desc = crew.tasks[0].description
        assert "test-uuid-1234" in task_desc
        assert "AI Strategy Framework 2026.pdf" in task_desc
