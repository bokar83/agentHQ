from orchestrator.saver import get_drive_subfolder


def test_research_report_routes_correctly():
    assert get_drive_subfolder("research_report") == "deliverables/research"

def test_social_content_routes_correctly():
    assert get_drive_subfolder("social_content") == "deliverables/social"

def test_hunter_task_routes_correctly():
    assert get_drive_subfolder("hunter_task") == "leads"

def test_unknown_task_routes_to_deliverables():
    assert get_drive_subfolder("unknown_type_xyz") == "deliverables"

def test_consulting_routes_correctly():
    assert get_drive_subfolder("consulting_deliverable") == "deliverables/consulting"

def test_code_task_routes_correctly():
    assert get_drive_subfolder("code_task") == "deliverables/code"

def test_website_build_routes_correctly():
    assert get_drive_subfolder("website_build") == "deliverables/websites"
