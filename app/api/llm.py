from typing import Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.models import User
from app.generation.registry import LLMRegistry


class LLMProviderResponse(BaseModel):
    id: str
    label: str
    model: str


class LLMProvidersResponse(BaseModel):
    default: str
    providers: list[LLMProviderResponse]


def create_llm_router(
    llm_registry: LLMRegistry,
    get_current_user: Callable[..., User],
) -> APIRouter:

    router = APIRouter()

    @router.get("/providers", response_model=LLMProvidersResponse)
    def list_providers(
        current_user: User = Depends(get_current_user),
    ):
        return LLMProvidersResponse(
            default=llm_registry.default_id,
            providers=[
                LLMProviderResponse(
                    id=provider.provider_id,
                    label=provider.label,
                    model=provider.model_name,
                )
                for provider in llm_registry.providers
            ],
        )

    return router
