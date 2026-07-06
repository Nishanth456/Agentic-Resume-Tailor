# Resume Tailor Agent

A structured AI-powered resume tailoring app with ATS keyword scoring, file-based resume input, and a modular developer-friendly codebase.

## Project Structure
- src/agents: resume analysis and tailoring logic
- src/services: Gemini and MCP service integrations
- src/ui: Streamlit interface
- tests: validation and regression tests

## Features
- upload a resume file
- paste a job description
- get ATS keyword scoring
- review matched and missing keywords
- generate tailored resume content with Gemini

## Setup
1. Create a Python environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a .env file from .env.example and add your Google API key:
   ```bash
   GOOGLE_API_KEY=your_key_here
   ```
4. Run the app:
   ```bash
   streamlit run main.py
   ```

## Notes
This version now includes an ADK-style orchestration layer that separates the analysis and generation stages so the experience is easier to extend into a richer multi-agent workflow.
