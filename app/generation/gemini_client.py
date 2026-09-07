from google import genai
from google.genai import types

from app.generation.base import LLM


class GeminiClient(LLM):

    def __init__(
        self,
        model_name: str,
        system_instruction: str,
        api_key: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
    ):
        self.client = (
            genai.Client(api_key=api_key)
            if api_key
            else genai.Client()
        )

        self.model_name = model_name
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def generate(self, prompt: str) -> str:

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text