import src.agents.resume_tailor_agent as resume_agent_module
from src.agents.resume_tailor_agent import ResumeTailorAgent


def test_ats_score_and_keyword_extraction():
    agent = ResumeTailorAgent()
    resume_text = """
    Experienced Python developer with expertise in APIs, data analysis, and cloud deployments.
    Built dashboards, automated pipelines, and collaborated with product teams.
    """
    job_description = """
    We are hiring a Python engineer with experience in APIs, Azure, machine learning, and data analysis.
    """

    result = agent.analyze_resume_resume(resume_text, job_description)

    assert result["ats_score"] >= 0
    assert result["ats_score"] <= 100
    assert "python" in result["matched_keywords"]
    assert "api" in result["matched_keywords"]
    assert "azure" in result["missing_keywords"]


def test_keyword_extraction_ignores_generic_terms():
    agent = ResumeTailorAgent()
    resume_text = """
    Experienced in machine learning and NLP for agentic AI systems.
    """
    job_description = """
    We need a candidate with expertise in agentic AI, machine learning, and NLP.
    The primary responsibilities are about design and implementation.
    """

    result = agent.analyze_resume_resume(resume_text, job_description)

    assert "about" not in result["matched_keywords"]
    assert "about" not in result["missing_keywords"]
    assert "primary" not in result["matched_keywords"]
    assert "primary" not in result["missing_keywords"]
    assert "key" not in result["matched_keywords"]
    assert "key" not in result["missing_keywords"]
    assert "design" not in result["matched_keywords"]
    assert "design" not in result["missing_keywords"]
    assert "agentic ai" in result["matched_keywords"]


def test_ats_score_uses_meaningful_keywords_only():
    agent = ResumeTailorAgent()
    resume_text = "Experienced in machine learning and NLP."
    job_description = "We need expertise in machine learning and NLP."

    result = agent.analyze_resume_resume(resume_text, job_description)

    assert result["ats_score"] == 100.0


def test_extracts_meaningful_keywords_not_loose_phrases():
    agent = ResumeTailorAgent()
    resume_text = "Worked on machine learning, NLP, and large language models."
    job_description = "We need expertise in machine learning, NLP, and large language models for generative AI."

    result = agent.analyze_resume_resume(resume_text, job_description)

    assert "machine learning" in result["matched_keywords"]
    assert "nlp" in result["matched_keywords"]
    assert "large language models" in result["matched_keywords"]
    assert "machine learning generative" not in result["matched_keywords"]
    assert "language models generative" not in result["matched_keywords"]


def test_uses_llm_keywords_for_job_description(monkeypatch):
    class FakeGeminiService:
        def __init__(self, api_key):
            self.api_key = api_key

        def generate_tailored_content(self, prompt):
            return '["machine learning", "generative ai", "llm", "nlp", "python"]'

    monkeypatch.setattr(resume_agent_module, "GeminiService", FakeGeminiService)

    agent = ResumeTailorAgent(api_key="fake-key")
    resume_text = "I have Python and NLP experience."
    job_description = "We need a machine learning engineer with generative ai and llm skills."

    result = agent.analyze_resume_resume(resume_text, job_description)

    assert "machine learning" in result["job_keywords"]
    assert "generative ai" in result["job_keywords"]
    assert "llm" in result["job_keywords"]
    assert "nlp" in result["job_keywords"]


def test_filters_generic_terms_and_matches_shared_tokens():
    agent = ResumeTailorAgent()
    resume_text = "Built Python and API solutions for data analysis."
    job_description = "We need a Python engineer with primary responsibilities around design and implementation for API and data analysis."

    result = agent.analyze_resume_resume(resume_text, job_description)

    assert "python" in result["matched_keywords"]
    assert "api" in result["matched_keywords"]
    assert "data analysis" in result["matched_keywords"]
    assert "primary" not in result["job_keywords"]
    assert "responsibilities" not in result["job_keywords"]
    assert "design" not in result["job_keywords"]
    assert "implementation" not in result["job_keywords"]
