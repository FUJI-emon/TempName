import os
from .fake import FakeLLMService
from .interface import LLMService


def get_llm_service() -> LLMService:
    provider = os.getenv("LLM_PROVIDER", "fake").lower()
    if provider == "fake":
        return FakeLLMService()
    elif provider == "openrouter":
        from .adapters.openrouter import OpenRouterAdapter
        return OpenRouterAdapter()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")