from typing import Any, Iterator

import groq

from app.generation.base import LLM, ConversationTurn
from app.generation.errors import LLMError, LLMErrorCode

PROVIDER_NAME = "Groq"


class GroqClient(LLM):
    """
    Chat completions on Groq (OpenAI-compatible API), e.g. gpt-oss-120b.

    gpt-oss is a reasoning model: its reasoning tokens count against
    max_output_tokens, and are left out of the answer text.
    """

    def __init__(
        self,
        model_name: str,
        system_instruction: str,
        api_key: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
        reasoning_effort: str | None = "medium",
    ):
        self.client = groq.Groq(api_key=api_key)

        self.model_name = model_name
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.reasoning_effort = reasoning_effort

    def generate(
        self,
        prompt: str,
        history: list[ConversationTurn] | None = None,
    ) -> str:

        try:
            response = self.client.chat.completions.create(
                **self._request_options(prompt, history),
            )
        except Exception as error:
            raise translate_error(error) from error

        text = response.choices[0].message.content if response.choices else None

        if not text:
            raise LLMError(PROVIDER_NAME, LLMErrorCode.EMPTY_RESPONSE)

        return text

    def generate_stream(
        self,
        prompt: str,
        history: list[ConversationTurn] | None = None,
    ) -> Iterator[str]:

        has_text = False

        try:
            stream = self.client.chat.completions.create(
                **self._request_options(prompt, history),
                stream=True,
            )

            for chunk in stream:
                text = chunk.choices[0].delta.content if chunk.choices else None

                if text:
                    has_text = True
                    yield text
        except Exception as error:
            raise translate_error(error) from error

        if not has_text:
            raise LLMError(PROVIDER_NAME, LLMErrorCode.EMPTY_RESPONSE)

    def _request_options(
        self,
        prompt: str,
        history: list[ConversationTurn] | None,
    ) -> dict[str, Any]:

        options: dict[str, Any] = {
            "model": self.model_name,
            "messages": self._build_messages(prompt, history or []),
            "temperature": self.temperature,
            "max_completion_tokens": self.max_output_tokens,
        }

        # Only reasoning models accept these; leave them unset otherwise.
        if self.reasoning_effort:
            options["reasoning_effort"] = self.reasoning_effort
            options["include_reasoning"] = False

        return options

    def _build_messages(
        self,
        prompt: str,
        history: list[ConversationTurn],
    ) -> list[dict[str, str]]:

        messages = [{"role": "system", "content": self.system_instruction}]

        for turn in history:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})

        messages.append({"role": "user", "content": prompt})

        return messages


def translate_error(error: Exception) -> LLMError:
    return LLMError(PROVIDER_NAME, classify_error(error))


def classify_error(error: Exception) -> LLMErrorCode:

    # APITimeoutError subclasses APIConnectionError, so check it first.
    if isinstance(error, groq.APITimeoutError):
        return LLMErrorCode.TIMEOUT

    if isinstance(error, groq.APIConnectionError):
        return LLMErrorCode.CONNECTION_FAILED

    if isinstance(error, groq.RateLimitError):
        return LLMErrorCode.RATE_LIMITED

    if isinstance(error, (groq.AuthenticationError, groq.PermissionDeniedError)):
        return LLMErrorCode.AUTH_FAILED

    if isinstance(error, groq.NotFoundError):
        return LLMErrorCode.MODEL_NOT_FOUND

    if not isinstance(error, groq.APIStatusError):
        return LLMErrorCode.UNKNOWN

    # Groq answers 413 when one request is bigger than the account's
    # tokens-per-minute limit.
    if error.status_code == 413:
        return LLMErrorCode.REQUEST_TOO_LARGE

    if error_code(error) == "context_length_exceeded":
        return LLMErrorCode.CONTEXT_TOO_LONG

    if error.status_code == 504:
        return LLMErrorCode.TIMEOUT

    if error.status_code >= 500:
        return LLMErrorCode.UNAVAILABLE

    if error.status_code >= 400:
        return LLMErrorCode.INVALID_REQUEST

    return LLMErrorCode.UNKNOWN


def error_code(error: groq.APIStatusError) -> str | None:
    # Body is {"error": {"message": ..., "type": ..., "code": ...}}.
    body = error.body

    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        body = body["error"]

    if isinstance(body, dict):
        return body.get("code")

    return None
