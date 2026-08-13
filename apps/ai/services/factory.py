import os
from .fake import FakeLLMService
from .interface import LLMService


def get_llm_service() -> LLMService:
    provider = os.getenv("LLM_PROVIDER", "fake")
    if provider == "fake":
        return FakeLLMService()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")