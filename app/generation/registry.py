from dataclasses import dataclass

from app.generation.base import LLM


class UnknownProviderError(Exception):

    def __init__(self, provider_id: str):
        super().__init__(f"Unknown or unconfigured LLM provider: {provider_id}")
        self.provider_id = provider_id


@dataclass(frozen=True)
class LLMProvider:
    provider_id: str
    label: str
    model_name: str
    llm: LLM


class LLMRegistry:
    """
    The LLM providers that have an API key configured; users pick one of
    them per query.
    """

    def __init__(self, providers: list[LLMProvider], default_id: str):
        if not providers:
            raise RuntimeError(
                "No LLM provider configured: set GEMINI_API_KEY or GROQ_API_KEY"
            )

        self._providers = {
            provider.provider_id: provider
            for provider in providers
        }

        # Fall back to the first configured provider when the preferred
        # default has no API key.
        self.default_id = (
            default_id
            if default_id in self._providers
            else providers[0].provider_id
        )

    @property
    def providers(self) -> list[LLMProvider]:
        return list(self._providers.values())

    @property
    def default(self) -> LLMProvider:
        return self._providers[self.default_id]

    def get(self, provider_id: str | None) -> LLMProvider:
        if provider_id is None:
            return self.default

        try:
            return self._providers[provider_id]
        except KeyError:
            raise UnknownProviderError(provider_id) from None
