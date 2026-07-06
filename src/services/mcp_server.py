import json
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resume-tailor-tools")

STOP_WORDS = {
    "the", "and", "for", "with", "from", "your", "you", "that", "have", "this",
    "will", "into", "our", "their", "been", "were", "are", "is", "be", "of", "to",
    "in", "on", "a", "an", "or", "as", "it", "can", "using", "build", "develop",
    "team", "work", "projects", "based", "across", "role", "job", "resume"
}


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


@mcp.tool()
def extract_resume_skills(resume_text: str) -> str:
    """Extract likely technical and professional skills from a resume."""
    text = _clean_text(resume_text).lower()
    known_skills = [
        "python", "java", "javascript", "typescript", "react", "node", "sql",
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "api", "rest",
        "machine learning", "deep learning", "llm", "data analysis", "pandas",
        "numpy", "tableau", "power bi", "spark", "streamlit", "fastapi", "flask",
        "testing", "agile", "scrum", "linux", "devops", "ci/cd"
    ]
    found = [skill for skill in known_skills if skill in text]
    return json.dumps({"skills": found[:12]})


@mcp.tool()
def extract_job_keywords(job_description: str) -> str:
    """Extract likely keywords from a job description."""
    text = _clean_text(job_description).lower()
    words = re.findall(r"[a-z0-9+#./-]{2,}", text)
    filtered = []
    for word in words:
        if word in STOP_WORDS or len(word) < 3:
            continue
        if word not in filtered:
            filtered.append(word)
    return json.dumps({"keywords": filtered[:20]})


@mcp.tool()
def rewrite_bullets(resume_text: str, job_description: str) -> str:
    """Create a few tailored resume bullet suggestions based on resume and job context."""
    resume = _clean_text(resume_text)
    job = _clean_text(job_description)
    bullets = []

    if "python" in job.lower() or "python" in resume.lower():
        bullets.append("Developed Python-based solutions and automated repetitive workflows to improve reliability and delivery speed.")
    if "data" in job.lower() or "analysis" in job.lower():
        bullets.append("Analyzed structured data and translated findings into clear recommendations for stakeholders and product teams.")
    if "ai" in job.lower() or "machine learning" in job.lower():
        bullets.append("Applied AI and machine learning techniques to build practical prototypes and improve decision-making processes.")
    if "team" in job.lower() or "collaborat" in job.lower():
        bullets.append("Collaborated with cross-functional teams to deliver projects on time while maintaining quality and clear communication.")

    if not bullets:
        bullets.append("Delivered high-impact work by combining technical execution, problem-solving, and strong collaboration.")

    return json.dumps({"suggested_bullets": bullets[:4]})


if __name__ == "__main__":
    mcp.run(transport="stdio")
