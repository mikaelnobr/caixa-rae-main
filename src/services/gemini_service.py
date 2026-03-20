import json
import time
from typing import Any, Dict

from google import genai
from google.genai import types

from src.models.constants import GEMINI_SCHEMA


class GeminiService:
    """
    Serviço para interagir com a API do Google Gemini.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, prompt: str) -> Dict[str, Any]:
        """
        Chama a API Gemini com retry em caso de rate limit (429).
        """
        for d in [15, 30, 60]:  # retry delays
            try:
                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GEMINI_SCHEMA,
                        temperature=0.1,
                    ),
                )
                return json.loads(res.text)
            except Exception as e:
                if "429" in str(e):
                    time.sleep(d)
                    continue
                raise e
        else:
            raise RuntimeError("Gemini API: número máximo de tentativas atingido.")
