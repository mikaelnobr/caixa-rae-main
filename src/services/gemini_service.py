import json
import time
from typing import Any, Dict

import google.generativeai as genai

from src.models.constants import GEMINI_SCHEMA


def call_gemini(api_key: str, prompt: str) -> Dict[str, Any]:
    """Chama a API Gemini com retry em caso de rate limit (429)."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    for d in [2, 4, 8]:
        try:
            res = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
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
