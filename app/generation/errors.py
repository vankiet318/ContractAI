"""
Provider-independent LLM failures. Each client translates its SDK's
exceptions into an LLMError whose message is safe to show to users and
names the provider, e.g. "Gemini has run out of requests ...".
"""

from enum import StrEnum


class LLMErrorCode(StrEnum):
    RATE_LIMITED = "rate_limited"
    REQUEST_TOO_LARGE = "request_too_large"
    CONTEXT_TOO_LONG = "context_too_long"
    AUTH_FAILED = "auth_failed"
    MODEL_NOT_FOUND = "model_not_found"
    INVALID_REQUEST = "invalid_request"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    CONNECTION_FAILED = "connection_failed"
    BLOCKED = "blocked"
    EMPTY_RESPONSE = "empty_response"
    UNKNOWN = "unknown"


_MESSAGES = {
    LLMErrorCode.RATE_LIMITED: (
        "{provider} has run out of requests for now (rate limit or quota "
        "reached). Please wait a moment and try again, or switch to "
        "another model."
    ),
    LLMErrorCode.REQUEST_TOO_LARGE: (
        "This request exceeds {provider}'s token limit per minute. Please "
        "wait a moment, ask a shorter question, or switch to another model."
    ),
    LLMErrorCode.CONTEXT_TOO_LONG: (
        "The question and document context are too long for {provider}. "
        "Please ask a shorter question or switch to another model."
    ),
    LLMErrorCode.AUTH_FAILED: (
        "{provider} rejected the API key. Please ask the administrator to "
        "check the {provider} API key and model access."
    ),
    LLMErrorCode.MODEL_NOT_FOUND: (
        "The configured {provider} model was not found. Please ask the "
        "administrator to check the model name."
    ),
    LLMErrorCode.INVALID_REQUEST: (
        "{provider} rejected the request. Please try again or switch to "
        "another model."
    ),
    LLMErrorCode.UNAVAILABLE: (
        "{provider} is temporarily unavailable or overloaded. Please try "
        "again in a few minutes or switch to another model."
    ),
    LLMErrorCode.TIMEOUT: (
        "{provider} took too long to respond. Please try again."
    ),
    LLMErrorCode.CONNECTION_FAILED: (
        "Could not connect to {provider}. Please check the server's network "
        "connection and try again."
    ),
    LLMErrorCode.BLOCKED: (
        "{provider} blocked this answer with its safety filters. Please "
        "rephrase your question."
    ),
    LLMErrorCode.EMPTY_RESPONSE: (
        "{provider} returned an empty answer. Please try again."
    ),
    LLMErrorCode.UNKNOWN: (
        "{provider} failed to generate an answer. Please try again or "
        "switch to another model."
    ),
}


class LLMError(Exception):

    def __init__(self, provider: str, code: LLMErrorCode):
        self.provider = provider
        self.code = code
        self.user_message = _MESSAGES[code].format(provider=provider)
        super().__init__(self.user_message)
