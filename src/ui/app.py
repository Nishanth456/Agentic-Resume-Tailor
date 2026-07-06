import zipfile
from xml.etree import ElementTree as ET

import streamlit as st

from src.agents.adk_resume_workflow import ResumeWorkflowOrchestrator
from src.agents.resume_tailor_agent import ResumeTailorAgent


def read_uploaded_resume(uploaded_file) -> str:
    if uploaded_file.name.endswith(".docx"):
        with zipfile.ZipFile(uploaded_file) as archive:
            xml_data = archive.read("word/document.xml")
            root = ET.fromstring(xml_data)
            namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for paragraph in root.findall(".//w:p", namespace):
                parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
                text = "".join(parts).strip()
                if text:
                    paragraphs.append(text)
            return "\n".join(paragraphs)

    return uploaded_file.getvalue().decode("utf-8", errors="ignore")


def build_fallback_resume_output(analysis) -> str:
    matched = analysis["matched_keywords"][:6]
    missing = analysis["missing_keywords"][:6]
    return f"""
## Recommended Resume Summary
Focus on your strongest technical experience first and mirror the employer's language around {', '.join(matched) if matched else 'the target role'}.

## Suggested Bullet Points
- Built reliable solutions that improved delivery speed and operational consistency.
- Applied data-focused methods to turn complex information into actionable insights.
- Collaborated with cross-functional teams to ship high-quality outcomes.
- Strengthened technical impact by aligning work with role-specific requirements.

## ATS Improvement Notes
- Add the missing keywords: {', '.join(missing) if missing else 'none'}.
- Keep the wording concise and measurable.
- Tailor the summary and bullets to the exact job description.
"""


def main() -> None:
    st.set_page_config(page_title="Resume Tailor Agent", page_icon="📝", layout="wide")

    st.title("Resume Tailor Agent")
    st.write("Upload your resume, paste a job description, and receive an ATS-aware tailored result.")

    agent = ResumeTailorAgent()
    workflow = ResumeWorkflowOrchestrator()

    with st.sidebar:
        st.header("Workflow")
        st.write("1. Upload resume as a text file")
        st.write("2. Paste a job description")
        st.write("3. Review ATS match score and tailored content")

    uploaded_file = st.file_uploader("Upload Resume File", type=["txt", "md", "docx"], help="Upload your resume as a text file")
    job_description = st.text_area(
        "Job Description",
        height=220,
        placeholder="Paste the target job description here...",
    )

    if st.button("Run Agent", type="primary"):
        if not uploaded_file:
            st.error("Please upload a resume file.")
            st.stop()

        if not job_description.strip():
            st.error("Please provide a job description.")
            st.stop()

        with st.spinner("Analyzing resume and generating tailored output..."):
            try:
                resume_text = read_uploaded_resume(uploaded_file)
                analysis = agent.analyze_resume_resume(resume_text, job_description)
                workflow_result = workflow.run(resume_text, job_description, analysis=analysis)
                content = workflow_result["content"]

                st.subheader("ATS Match Overview")
                col1, col2, col3 = st.columns(3)
                col1.metric("ATS Score", f"{analysis['ats_score']}%")
                col2.metric("Matched Keywords", len(analysis["matched_keywords"]))
                col3.metric("Missing Keywords", len(analysis["missing_keywords"]))

                st.subheader("Matched Keywords")
                st.write(", ".join(analysis["matched_keywords"][:15]) or "No strong matches found")

                st.subheader("Missing Keywords")
                st.write(", ".join(analysis["missing_keywords"][:15]) or "No missing keywords found")

                st.subheader("Tailored Output")
                st.markdown(content)
            except Exception as e:
                st.error(f"Agent workflow failed: {e}")


if __name__ == "__main__":
    main()
