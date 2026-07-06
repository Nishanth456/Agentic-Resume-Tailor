import os
import json
import subprocess
import sys
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

st.set_page_config(page_title="Resume Tailor Agent", page_icon="📝", layout="wide")

st.title("Resume Tailor Agent")
st.write("An AI agent workflow that uses the Google SDK and an MCP-style tool server to tailor a resume for a target role.")

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

api_key = os.getenv("GOOGLE_API_KEY", "")
if not api_key:
    st.warning("Add GOOGLE_API_KEY to the .env file before running the agent workflow.")


def run_mcp_tools(resume_text: str, job_description: str):
    script = os.path.join(os.path.dirname(__file__), "src", "services", "mcp_server.py")
    proc = subprocess.run(
        [sys.executable, script],
        input=json.dumps({
            "resume_text": resume_text,
            "job_description": job_description
        }),
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or "MCP tool execution failed")
    return proc.stdout.strip()


st.sidebar.header("Workflow")
st.sidebar.write("1. Paste a resume\n2. Paste a job description\n3. The agent uses local MCP tools and Gemini to tailor the result")

resume_text = st.text_area("Resume", height=260, placeholder="Paste your resume text here...")
job_description = st.text_area("Job Description", height=260, placeholder="Paste the target job description here...")

if st.button("Run Agent"):
    if not resume_text.strip() or not job_description.strip():
        st.error("Please provide both a resume and a job description.")
        st.stop()

    if not api_key:
        st.error("GOOGLE_API_KEY is missing.")
        st.stop()

    with st.spinner("Running the agent workflow..."):
        try:
            tool_output = run_mcp_tools(resume_text, job_description)
            prompt = f"""
            You are a career assistant. Use the structured tool output below to tailor the resume.

            Resume:
            {resume_text}

            Job Description:
            {job_description}

            Tool Output:
            {tool_output}

            Produce:
            1. Tailored Bullet Points
            2. Match Summary
            3. Cover Letter Draft
            4. Improvement Notes
            """

            try:
                from google import genai as google_genai

                client = google_genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                )
                content = getattr(response, "text", str(response))
            except Exception:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-3.5-flash")
                response = model.generate_content(prompt)
                content = response.text

            st.markdown(content)
        except Exception as e:
            st.error(f"Agent workflow failed: {e}")
