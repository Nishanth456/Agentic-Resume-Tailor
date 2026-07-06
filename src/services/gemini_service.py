import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class GeminiService:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")

    def generate_tailored_content(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is missing")

        try:
            from google import genai as google_genai

            client = google_genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
            )
            return getattr(response, "text", str(response))
        except Exception:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(prompt)
            return response.text
