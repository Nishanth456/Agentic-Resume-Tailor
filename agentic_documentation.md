# Agentic Workflow Documentation

This document explains the backend architecture and how the AI agentic workflow operates within the Resume Tailoring Application.

## System Architecture Overview

The backend is built with **FastAPI** (`main.py`) which exposes REST endpoints to the frontend. The core logic of the application revolves around "Agents" and "Services" that orchestrate interactions with Large Language Models (LLMs) to analyze, score, and rewrite resumes.

### Key Components

1. **`main.py`**: The API Gateway and Controller.
2. **`src/agents/resume_tailor_agent.py`**: The primary intelligence engine (Single-Agent Pattern).
3. **`src/services/gemini_service.py`**: The LLM interface wrapper.
4. **`src/agents/adk_resume_workflow.py`**: The multi-agent orchestrator pattern (using Google ADK).

---

## The Primary Agentic Workflow

When a user submits a resume and a job description to the `/api/analyze` endpoint, the following workflow is triggered:

### 1. Ingestion (`main.py`)
- The backend receives the resume file (PDF or DOCX) and the job description text.
- Text is extracted from the uploaded document using `pdfplumber` or `docx2txt`.

### 2. Analysis Phase (`ResumeTailorAgent.analyze_resume_resume`)
This is where the agent performs its analytical reasoning.
- **Job Keyword Extraction**: The agent makes an LLM call (`gemini.generate_tailored_content`) with a strict prompt to extract multi-word technical skills from the job description, ignoring generic soft skills.
- **Resume Keyword Extraction**: The agent uses natural language processing (regex/token matching) to parse the resume text and see which job keywords are actually present.
- **ATS Scoring**: The agent calculates an ATS match score based on the ratio of matched vs. missing keywords.

### 3. Prompt Engineering & Synthesis (`ResumeTailorAgent.build_tailored_output`)
- Instead of relying on a conversational chat structure, the agent dynamically constructs a highly structured, system-level prompt.
- It injects the `analysis` data (matched/missing keywords), the original resume, and the job description into the prompt.
- It instructs the LLM to adopt multiple personas: *Executive Resume Writer*, *ATS Optimization Specialist*, and *Technical Recruiter*.
- It mandates a strict **JSON-only** output schema to guarantee that the frontend can parse the data into individual UI cards (e.g., `experience_improvements`, `feedback_box`, etc.).

### 4. LLM Generation & Output (`GeminiService`)
- The constructed prompt is sent to the LLM (currently `gemini-3.5-flash` to bypass quota limits on older models) via the `GeminiService`.
- `main.py` receives the response, strips out any potential markdown blocks (e.g., ` ```json ` wrappers that LLMs sometimes add), and sends the clean, structured JSON back to the frontend to render the beautiful UI.

---

## Alternative Multi-Agent Architecture (`adk_resume_workflow.py`)

While the primary flow relies on a single, highly-optimized agent prompt (which is faster and uses fewer API calls), the codebase also supports a complex **Multi-Agent Orchestrator** pattern using the Google Agent Development Kit (ADK).

If enabled, this workflow operates via specialized sub-agents:

1. **Analysis Agent**: 
   - *Persona*: Expert resume analyst.
   - *Task*: Focuses purely on extracting keywords, finding gaps, and generating an ATS score. It passes its structured findings forward.
   
2. **Synthesis Agent**: 
   - *Persona*: Senior career strategist.
   - *Task*: Takes the output of the Analysis Agent and focuses entirely on rewriting the bullet points and providing strategic career feedback.

3. **Orchestrator**:
   - Manages the state between these agents. It ensures that the Synthesis Agent waits for the Analysis Agent to finish before starting its work, chaining their thoughts together to produce a comprehensive final output.

## Quota & API Management

Because AI agents can consume API quotas rapidly (especially when making multiple calls per request for extraction and generation), the backend is optimized to:
1. **Cache Analysis**: The ATS analysis is calculated once and passed forward, preventing duplicate LLM calls.
2. **SDK Graceful Degradation**: `GeminiService` is built to try the newest `google.genai` SDK first, and seamlessly falls back to the deprecated `google.generativeai` SDK if necessary.
