import os
from openai import OpenAI
from typing import Literal

LLMModel = Literal["gpt-4o", "gpt-4.1-mini", "gpt-4.1-nano"]

class LLMClient:
    def __init__(self, model: LLMModel = "gpt-4.1-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def chat(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            if not response.choices:
                raise RuntimeError("Brak odpowiedzi z LLM (choices == []).")

            content = response.choices[0].message.content.strip()
            if not content or not content.strip():
                raise RuntimeError("LLM zwrócił pustą odpowiedź.")

            return content

        except Exception as e:
            raise RuntimeError(f"❌ Błąd LLM ({self.model}): {e}")