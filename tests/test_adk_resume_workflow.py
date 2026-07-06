from src.agents.adk_resume_workflow import ResumeWorkflowOrchestrator


def test_workflow_falls_back_without_api_key():
    orchestrator = ResumeWorkflowOrchestrator(api_key="")
    result = orchestrator.run(
        "Experienced Python developer with API and cloud experience.",
        "We need a Python engineer with Azure and API experience.",
        analysis={
            "matched_keywords": ["python", "api"],
            "missing_keywords": ["azure"],
            "ats_score": 67.0,
        },
    )

    assert result["source"] == "fallback"
    assert "Recommended Resume Summary" in result["content"]
    assert "azure" in result["content"]


def test_workflow_includes_mcp_context():
    orchestrator = ResumeWorkflowOrchestrator(api_key="")
    result = orchestrator.run(
        "Experienced Python developer with API and cloud experience.",
        "We need a Python engineer with Azure and API experience.",
        analysis={
            "matched_keywords": ["python", "api"],
            "missing_keywords": ["azure"],
            "ats_score": 67.0,
        },
    )

    assert "MCP" in result["content"]
    assert "python" in result["content"].lower()
