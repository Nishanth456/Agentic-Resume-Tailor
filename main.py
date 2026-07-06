import os
import zipfile
from xml.etree import ElementTree as ET
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.agents.adk_resume_workflow import ResumeWorkflowOrchestrator
from src.agents.resume_tailor_agent import ResumeTailorAgent

app = FastAPI(title="Resume Tailor API")

agent = ResumeTailorAgent()
workflow = ResumeWorkflowOrchestrator()


def read_uploaded_resume(file: UploadFile, content: bytes) -> str:
    filename = file.filename or ""
    if filename.endswith(".docx"):
        import io
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
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

    return content.decode("utf-8", errors="ignore")


@app.post("/api/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if not resume:
        raise HTTPException(status_code=400, detail="Resume file is required")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required")

    try:
        content = await resume.read()
        resume_text = read_uploaded_resume(resume, content)
        
        analysis = agent.analyze_resume_resume(resume_text, job_description)
        output_data = agent.build_tailored_output(resume_text, job_description, analysis)
        
        from src.services.gemini_service import GeminiService
        gemini = GeminiService(api_key=agent.api_key)
        
        try:
            generated_content = gemini.generate_tailored_content(output_data["prompt"])
            cleaned_content = generated_content.strip()
            if cleaned_content.startswith("```"):
                import re
                cleaned_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned_content).strip()
        except Exception as e:
            cleaned_content = '{"error": "Failed to generate AI response: ' + str(e) + '"}'
        
        return {
            "status": "success",
            "ats_score": analysis.get("ats_score", 0),
            "matched_keywords": analysis.get("matched_keywords", []),
            "missing_keywords": analysis.get("missing_keywords", []),
            "content": cleaned_content
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Ensure static directory exists
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
