import json
import time
from typing import Any, Dict

from google import genai
from google.genai import types

from src.models.constants import GEMINI_SCHEMA


def call_gemini(api_key: str, prompt: str) -> Dict[str, Any]:
    """Chama a API Gemini com retry em caso de rate limit (429)."""
    client = genai.Client(api_key=api_key)
    for d in [2, 4, 8]:
        try:
            res = client.models.generate_content(
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
    raise RuntimeError("Gemini API: número máximo de tentativas atingido.")
