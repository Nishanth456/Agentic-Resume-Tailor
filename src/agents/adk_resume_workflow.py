import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


class ResumeWorkflowOrchestrator:
    """A lightweight ADK-style orchestration wrapper for the resume workflow."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")

    def run(self, resume_text: str, job_description: str, analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        analysis = analysis or {}
        matched = analysis.get("matched_keywords", []) or []
        missing = analysis.get("missing_keywords", []) or []
        score = analysis.get("ats_score", 0)

        try:
            from src.services.mcp_server import extract_job_keywords, extract_resume_skills

            skill_payload = json.loads(extract_resume_skills(resume_text))
            keyword_payload = json.loads(extract_job_keywords(job_description))
            mcp_context = (
                f"MCP context: skills={', '.join(skill_payload.get('skills', [])) or 'none'}; "
                f"job_keywords={', '.join(keyword_payload.get('keywords', [])) or 'none'}"
            )
        except Exception:
            mcp_context = "MCP context: unavailable"

        summary = (
            "Focus on your strongest technical experience first and mirror the employer's "
            f"language around {', '.join(matched[:4]) if matched else 'the target role'}."
        )
        bullets = [
            "Built reliable solutions that improved delivery speed and operational consistency.",
            "Applied data-focused methods to turn complex information into actionable insights.",
            "Collaborated with cross-functional teams to ship high-quality outcomes.",
            "Strengthened technical impact by aligning work with role-specific requirements.",
        ]

        content = f"""## Recommended Resume Summary
{summary}

## Suggested Bullet Points
- {bullets[0]}
- {bullets[1]}
- {bullets[2]}
- {bullets[3]}

## ATS Improvement Notes
- Add the missing keywords: {', '.join(missing[:6]) if missing else 'none'}.
- Keep the wording concise and measurable.
- Tailor the summary and bullets to the exact job description.
- Current ATS match score: {score}%.
- {mcp_context}
"""

        if not self.api_key:
            return {"source": "fallback", "content": content, "analysis": analysis}

        try:
            from google.adk.agents import LlmAgent, SequentialAgent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types

            analysis_agent = LlmAgent(
                name="analysis_agent",
                model="gemini-3.5-flash",
                instruction=(
                    "You are an expert resume analyst. Read the resume and job description "
                    "and produce a concise ATS-focused summary with keywords and gaps."
                ),
            )
            synthesis_agent = LlmAgent(
                name="synthesis_agent",
                model="gemini-3.5-flash",
                instruction=(
                    "You are a senior career strategist. Turn the analysis into a polished "
                    "resume tailoring response with a summary, bullet points, and improvement notes."
                ),
            )
            workflow_agent = SequentialAgent(
                name="resume_tailor_workflow",
                description="Orchestrates resume analysis and tailored output generation.",
                sub_agents=[analysis_agent, synthesis_agent],
            )

            session_service = InMemorySessionService()
            runner = Runner(
                agent=workflow_agent,
                app_name="resume_tailor_app",
                session_service=session_service,
                auto_create_session=True,
            )
            prompt = (
                "You are part of a resume tailoring workflow.\n\n"
                f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}\n\n"
                f"ATS Analysis:\n- Score: {score}%\n- Matched Keywords: {', '.join(matched)}\n"
                f"- Missing Keywords: {', '.join(missing)}\n"
            )
            message = types.Content(parts=[types.Part(text=prompt)])
            assembled_output = []
            for event in runner.run(user_id="demo", session_id="resume-session", new_message=message):
                content_block = getattr(getattr(event, "content", None), "parts", None) or []
                for part in content_block:
                    text = getattr(part, "text", None)
                    if text:
                        assembled_output.append(text)
            if assembled_output:
                return {"source": "adk", "content": "\n".join(assembled_output), "analysis": analysis}
        except Exception:
            pass

        try:
            from src.services.gemini_service import GeminiService

            prompt = (
                "You are a senior career strategist. Produce a polished, ATS-aware "
                "resume tailoring response.\n\n"
                f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}\n\n"
                f"ATS Analysis:\n- Score: {score}%\n- Matched Keywords: {', '.join(matched)}\n"
                f"- Missing Keywords: {', '.join(missing)}\n"
                f"- MCP Context: {mcp_context}\n"
            )
            generated = GeminiService(api_key=self.api_key).generate_tailored_content(prompt)
            return {"source": "gemini", "content": generated, "analysis": analysis}
        except Exception:
            return {"source": "fallback", "content": content, "analysis": analysis}
