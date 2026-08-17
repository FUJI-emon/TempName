import os
from dotenv import load_dotenv
from .fake import FakeLLMService
from .interface import LLMService


def get_llm_service() -> LLMService:
    load_dotenv(override=True)
    provider = os.getenv("LLM_PROVIDER")
    if not provider:
        if os.getenv("OPENROUTER_API_KEY"):
            provider = "openrouter"
        else:
            provider = "fake"
    provider = provider.lower()

    if provider == "openrouter":
        from .adapters.openrouter import OpenRouterAdapter
        return OpenRouterAdapter()
    elif provider == "fake":
        return FakeLLMService()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")