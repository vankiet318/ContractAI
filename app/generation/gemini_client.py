from typing import Iterator

import httpx
from google import genai
from google.genai import errors, types
from google.genai.chats import Chat

from app.generation.base import LLM, ConversationTurn
from app.generation.errors import LLMError, LLMErrorCode

PROVIDER_NAME = "Gemini"

BLOCKED_FINISH_REASONS = {
    types.FinishReason.SAFETY,
    types.FinishReason.RECITATION,
    types.FinishReason.BLOCKLIST,
    types.FinishReason.PROHIBITED_CONTENT,
    types.FinishReason.SPII,
}


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

        try:
            response = self._create_chat(history).send_message(prompt)
        except Exception as error:
            raise translate_error(error) from error

        if is_blocked(response):
            raise LLMError(PROVIDER_NAME, LLMErrorCode.BLOCKED)

        if not response.text:
            raise LLMError(PROVIDER_NAME, LLMErrorCode.EMPTY_RESPONSE)

        return response.text

    def generate_stream(
        self,
        prompt: str,
        history: list[ConversationTurn] | None = None,
    ) -> Iterator[str]:

        has_text = False
        last_chunk = None

        try:
            for chunk in self._create_chat(history).send_message_stream(prompt):
                last_chunk = chunk

                if chunk.text:
                    has_text = True
                    yield chunk.text
        except Exception as error:
            raise translate_error(error) from error

        # A safety stop can come after some text was already streamed;
        # report it rather than saving a silently truncated answer.
        if last_chunk is not None and is_blocked(last_chunk):
            raise LLMError(PROVIDER_NAME, LLMErrorCode.BLOCKED)

        if not has_text:
            raise LLMError(PROVIDER_NAME, LLMErrorCode.EMPTY_RESPONSE)

    def _create_chat(
        self,
        history: list[ConversationTurn] | None,
    ) -> Chat:

        return self.client.chats.create(
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


def is_blocked(response: types.GenerateContentResponse) -> bool:
    feedback = response.prompt_feedback

    if feedback is not None and feedback.block_reason:
        return True

    return any(
        candidate.finish_reason in BLOCKED_FINISH_REASONS
        for candidate in response.candidates or []
    )


def translate_error(error: Exception) -> LLMError:
    return LLMError(PROVIDER_NAME, classify_error(error))


def classify_error(error: Exception) -> LLMErrorCode:

    if isinstance(error, httpx.TimeoutException):
        return LLMErrorCode.TIMEOUT

    if isinstance(error, httpx.TransportError):
        return LLMErrorCode.CONNECTION_FAILED

    if not isinstance(error, errors.APIError):
        return LLMErrorCode.UNKNOWN

    status = error.status or ""
    message = (error.message or "").lower()

    # Free-tier quota and per-minute limits both arrive as 429.
    if error.code == 429 or status == "RESOURCE_EXHAUSTED":
        return LLMErrorCode.RATE_LIMITED

    # An invalid key comes back as 400 INVALID_ARGUMENT, so check the
    # message before treating 400 as a malformed request.
    if (
        error.code in (401, 403)
        or status in ("UNAUTHENTICATED", "PERMISSION_DENIED")
        or "api key" in message
    ):
        return LLMErrorCode.AUTH_FAILED

    if error.code == 404:
        return LLMErrorCode.MODEL_NOT_FOUND

    if error.code == 504 or status == "DEADLINE_EXCEEDED":
        return LLMErrorCode.TIMEOUT

    if error.code >= 500:
        return LLMErrorCode.UNAVAILABLE

    if "token" in message and ("exceed" in message or "limit" in message):
        return LLMErrorCode.CONTEXT_TOO_LONG

    if error.code >= 400:
        return LLMErrorCode.INVALID_REQUEST

    return LLMErrorCode.UNKNOWN
