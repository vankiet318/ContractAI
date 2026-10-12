import httpx
import groq
import pytest
from google.genai import errors as gemini_errors

from app.generation import gemini_client, groq_client
from app.generation.errors import LLMErrorCode
from app.generation.registry import LLMProvider, LLMRegistry, UnknownProviderError

REQUEST = httpx.Request("POST", "https://api.example.com")


def gemini_error(code: int, status: str, message: str = "") -> Exception:
    body = {"error": {"code": code, "status": status, "message": message}}
    error_type = gemini_errors.ServerError if code >= 500 else gemini_errors.ClientError
    return error_type(code, body)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (gemini_error(429, "RESOURCE_EXHAUSTED"), LLMErrorCode.RATE_LIMITED),
        (
            gemini_error(400, "INVALID_ARGUMENT", "API key not valid."),
            LLMErrorCode.AUTH_FAILED,
        ),
        (gemini_error(403, "PERMISSION_DENIED"), LLMErrorCode.AUTH_FAILED),
        (gemini_error(404, "NOT_FOUND"), LLMErrorCode.MODEL_NOT_FOUND),
        (
            gemini_error(
                400,
                "INVALID_ARGUMENT",
                "The input token count exceeds the maximum number of tokens allowed.",
            ),
            LLMErrorCode.CONTEXT_TOO_LONG,
        ),
        (gemini_error(400, "INVALID_ARGUMENT"), LLMErrorCode.INVALID_REQUEST),
        (gemini_error(503, "UNAVAILABLE"), LLMErrorCode.UNAVAILABLE),
        (gemini_error(504, "DEADLINE_EXCEEDED"), LLMErrorCode.TIMEOUT),
        (httpx.ReadTimeout("slow"), LLMErrorCode.TIMEOUT),
        (httpx.ConnectError("down"), LLMErrorCode.CONNECTION_FAILED),
        (ValueError("bug"), LLMErrorCode.UNKNOWN),
    ],
)
def test_gemini_errors_are_classified(error, expected):
    assert gemini_client.classify_error(error) == expected


def groq_error(error_type, status: int, code: str | None = None) -> Exception:
    body = {"error": {"message": "x", "type": "x", "code": code}}
    response = httpx.Response(status, request=REQUEST, json=body)
    return error_type("x", response=response, body=body)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (groq_error(groq.RateLimitError, 429), LLMErrorCode.RATE_LIMITED),
        (groq_error(groq.AuthenticationError, 401), LLMErrorCode.AUTH_FAILED),
        (groq_error(groq.NotFoundError, 404), LLMErrorCode.MODEL_NOT_FOUND),
        (groq_error(groq.APIStatusError, 413), LLMErrorCode.REQUEST_TOO_LARGE),
        (
            groq_error(groq.BadRequestError, 400, "context_length_exceeded"),
            LLMErrorCode.CONTEXT_TOO_LONG,
        ),
        (groq_error(groq.BadRequestError, 400), LLMErrorCode.INVALID_REQUEST),
        (groq_error(groq.InternalServerError, 503), LLMErrorCode.UNAVAILABLE),
        (groq.APITimeoutError(request=REQUEST), LLMErrorCode.TIMEOUT),
        (groq.APIConnectionError(request=REQUEST), LLMErrorCode.CONNECTION_FAILED),
    ],
)
def test_groq_errors_are_classified(error, expected):
    assert groq_client.classify_error(error) == expected


def test_error_message_names_the_provider():
    error = groq_client.translate_error(groq_error(groq.RateLimitError, 429))

    assert error.user_message.startswith("Groq has run out of requests")


def provider(provider_id: str) -> LLMProvider:
    return LLMProvider(provider_id, provider_id.title(), "model", object())


def test_registry_falls_back_when_default_is_not_configured():
    registry = LLMRegistry([provider("groq")], default_id="gemini")

    assert registry.get(None).provider_id == "groq"


def test_registry_rejects_unconfigured_provider():
    registry = LLMRegistry([provider("gemini")], default_id="gemini")

    with pytest.raises(UnknownProviderError):
        registry.get("groq")


def test_registry_needs_at_least_one_provider():
    with pytest.raises(RuntimeError):
        LLMRegistry([], default_id="gemini")
