import json
import os
import re
from typing import Dict, List

from dotenv import load_dotenv

from src.services.gemini_service import GeminiService

load_dotenv()


class ResumeTailorAgent:
    def __init__(self, api_key=None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        self.stop_words = {
            "the", "and", "for", "with", "from", "your", "you", "that", "have", "has",
            "this", "will", "into", "our", "their", "been", "were", "are", "is", "be",
            "of", "to", "in", "on", "a", "an", "or", "as", "it", "can", "using",
            "about", "primary", "key", "keys", "responsibility", "responsibilities",
            "responsible", "skill", "skills", "candidate", "candidates", "experience",
            "experienced", "need", "needs", "required", "requirements", "role", "roles",
            "job", "resume", "team", "teams", "project", "projects", "work", "working",
            "workflows", "system", "systems", "technology", "technologies", "algorithm",
            "algorithms", "enhance", "enhanced", "enhancing", "advanced", "model",
            "models", "application", "applications", "field", "fields", "level", "levels",
            "part", "parts", "specific", "main", "major", "design", "implementation",
            "implement", "designed", "develop", "developed", "development", "building",
            "build", "built", "deliver", "delivered", "delivery", "improve", "improved",
            "improving", "support", "supported", "supporting", "create", "created",
            "creating", "ensure", "ensuring", "across", "including", "include", "we",
            "engineer", "engineers", "around", "solutions", "solution", "problem", "problems"
        }
        self.known_multiword_phrases = {
            "machine learning",
            "data analysis",
            "natural language processing",
            "large language model",
            "large language models",
            "generative ai",
            "agentic ai",
            "deep learning",
            "prompt engineering",
            "api integration",
            "cloud computing",
            "python programming",
        }

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def _normalize_keyword(self, keyword: str) -> str:
        value = re.sub(r"[^a-z0-9]+", " ", keyword.lower()).strip()
        value = re.sub(r"\s+", " ", value)
        if not value:
            return ""
        return value

    def _extract_job_keywords(self, job_description: str) -> List[str]:
        if self.api_key and job_description.strip():
            try:
                prompt = (
                    "You are an expert ATS (Applicant Tracking System) keyword extractor.\n\n"
                    "Extract only the resume-relevant keywords from the following job description that can be used to match a candidate's resume.\n\n"
                    "Include:\n"
                    "- Technical skills (e.g., Python, Java, SQL)\n"
                    "- Programming languages\n"
                    "- Frameworks and libraries (e.g., TensorFlow, React, LangChain)\n"
                    "- Tools and platforms (e.g., Docker, Kubernetes, Git, AWS, Azure)\n"
                    "- Databases (e.g., MySQL, PostgreSQL, MongoDB)\n"
                    "- AI/ML technologies (e.g., Machine Learning, Deep Learning, Generative AI, Large Language Models, RAG)\n"
                    "- Cloud technologies\n"
                    "- Methodologies and concepts (e.g., REST APIs, CI/CD, Object-Oriented Programming, Data Structures, NLP, Computer Vision)\n"
                    "- Relevant certifications or technologies explicitly mentioned\n"
                    "- Important domain-specific terms that candidates commonly list on resumes\n\n"
                    "Rules:\n"
                    "- Prefer complete multi-word phrases over isolated words.\n"
                    "- Preserve the exact wording used in the job description whenever possible.\n"
                    "- Remove duplicates.\n"
                    "- Ignore responsibilities, qualifications, generic action verbs, soft skills, and filler words.\n"
                    "- Do NOT include phrases like 'strong communication', 'problem solving', 'team player', 'work independently', 'responsible for', etc.\n"
                    "- Return the most important keywords that would improve ATS matching.\n"
                    f"Job Description:\n{job_description}"
                )
                response = GeminiService(api_key=self.api_key).generate_tailored_content(prompt)
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned).strip()
                try:
                    parsed = json.loads(cleaned)
                except Exception:
                    parsed = re.findall(r'"([^"]+)"', cleaned)
                if isinstance(parsed, list):
                    keywords = []
                    for item in parsed:
                        normalized = self._normalize_keyword(str(item))
                        if normalized and normalized not in keywords:
                            keywords.append(normalized)
                    if keywords:
                        return keywords[:12]
            except Exception:
                pass

        return self._extract_resume_keywords(job_description, limit=12)

    def _extract_resume_keywords(self, text: str, limit: int = None) -> List[str]:
        if not text:
            return []

        tokens = re.findall(r"[a-z0-9]+", text.lower())
        filtered_tokens = [token for token in tokens if token not in self.stop_words and len(token) >= 2]
        keywords = []

        for phrase in self.known_multiword_phrases:
            if phrase in text.lower() and phrase not in keywords:
                keywords.append(phrase)

        for token in filtered_tokens:
            normalized = self._normalize_keyword(token)
            if normalized and normalized not in keywords:
                keywords.append(normalized)

        if limit is not None:
            return keywords[:limit]
        return keywords

    def analyze_resume_resume(self, resume_text: str, job_description: str) -> Dict[str, object]:
        resume_keywords = self._extract_resume_keywords(resume_text, limit=None)
        job_keywords = self._extract_job_keywords(job_description)
        resume_norms = {self._normalize_keyword(keyword) for keyword in resume_keywords}

        matched_keywords = []
        for keyword in job_keywords:
            normalized = self._normalize_keyword(keyword)
            if not normalized:
                continue
            if normalized in resume_norms:
                matched_keywords.append(normalized)
            elif all(token in resume_norms for token in normalized.split()):
                matched_keywords.append(normalized)

        missing_keywords = []
        for keyword in job_keywords:
            normalized = self._normalize_keyword(keyword)
            if not normalized:
                continue
            if normalized not in resume_norms and not all(token in resume_norms for token in normalized.split()):
                missing_keywords.append(normalized)

        missing_keywords = missing_keywords[:10]

        score = 0
        if job_keywords:
            meaningful_matches = [keyword for keyword in matched_keywords if len(keyword.split()) <= 2]
            score = round((len(meaningful_matches) / max(1, len(job_keywords))) * 100, 1)
            if score > 100:
                score = 100.0

        return {
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "ats_score": score,
            "resume_keywords": resume_keywords,
            "job_keywords": job_keywords,
        }

    def build_tailored_output(self, resume_text: str, job_description: str, analysis: Dict[str, object] = None) -> Dict[str, str]:
        if analysis is None:
            analysis = self.analyze_resume_resume(resume_text, job_description)
        prompt = f"""
You are an expert Executive Resume Writer, ATS Optimization Specialist, and Technical Recruiter with 15+ years of experience hiring for top technology companies.

Your objective is to maximize the resume's ATS score while maintaining complete factual accuracy. Never invent projects, technologies, certifications, experience, responsibilities, or achievements that are not supported by the resume.

==========================
ORIGINAL RESUME
==========================
{resume_text}

==========================
JOB DESCRIPTION
==========================
{job_description}

==========================
ATS ANALYSIS
==========================
Matched Keywords:
{', '.join(analysis['matched_keywords']) or 'None'}

Missing Keywords:
{', '.join(analysis['missing_keywords']) or 'None'}

Current ATS Score:
{analysis['ats_score']}%

==========================
TASK
==========================

Analyze both the resume and the job description like an ATS system followed by a senior recruiter.

Optimize the resume for this specific job.

Prioritize:
1. ATS keyword optimization
2. Technical relevance
3. Recruiter readability
4. Strong action-oriented writing
5. Quantifiable achievements
6. Industry-standard resume language

Whenever possible:
- Naturally incorporate missing technical keywords.
- Reorder experiences according to job relevance.
- Strengthen impact statements.
- Keep every statement truthful.
- Never fabricate information.
- Preserve the candidate's actual experience.

Use STAR/CAR style when rewriting bullet points.

==========================
OUTPUT FORMAT
==========================

Return ONLY valid JSON.

{{
    "ats_summary": {{
        "current_score": "...",
        "estimated_improved_score": "...",
        "match_level": "...",
        "overall_feedback": "..."
    }},

    "tailored_professional_summary": "...",

    "key_skills_to_highlight": [
        "...",
        "...",
        "..."
    ],

    "technical_keywords_added": [
        "...",
        "..."
    ],

    "experience_improvements": [
        {{
            "original": "...",
            "rewritten": "...",
            "reason": "..."
        }}
    ],

    "recommended_resume_bullets": [
        "...",
        "...",
        "...",
        "..."
    ],

    "project_improvements": [
        {{
            "project": "...",
            "improved_description": "..."
        }}
    ],

    "skills_section": {{
        "Programming Languages": [],
        "AI/ML": [],
        "Frameworks": [],
        "Cloud": [],
        "Databases": [],
        "Developer Tools": [],
        "Libraries": [],
        "Other Technologies": []
    }},

    "keyword_gap_analysis": {{
        "matched": [],
        "missing": [],
        "high_priority_missing": [],
        "recommended_additions": []
    }},

    "recruiter_feedback": {{
        "strengths": [],
        "weaknesses": [],
        "top_improvements": []
    }},

    "final_recommendations": [
        "...",
        "...",
        "..."
    ]
}}

Rules:
- Return valid JSON only.
- No markdown.
- No explanations.
- No text outside JSON.
- Never hallucinate experience.
- Rewrite professionally.
- Maximize ATS compatibility.
"""

        return {
            "analysis": json.dumps(analysis, indent=2),
            "prompt": prompt,
        }
