from google import genai
from google.genai import types

from app.generation.base import LLM, ConversationTurn


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

    def generate(
        self,
        prompt: str,
        history: list[ConversationTurn] | None = None,
    ) -> str:

        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
            history=self._build_chat_history(history) if history else [],
        )

        response = chat.send_message(prompt)

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text

    def _build_chat_history(
        self,
        history: list[ConversationTurn],
    ) -> list[types.Content]:

        contents = []

        for turn in history:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=turn.question)],
                )
            )
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text=turn.answer)],
                )
            )

        return contents