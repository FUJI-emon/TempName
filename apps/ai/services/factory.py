import os
import logging
from .fake import FakeLLMService
from .interface import LLMService

logger = logging.getLogger(__name__)

def get_llm_service() -> LLMService:
    """
    Factory function to retrieve LLM service implementation based on LLM_PROVIDER.
    Defaults to OpenRouter if API key is present or LLM_PROVIDER is set to openrouter.
    Falls back gracefully to FakeLLMService if missing key or configured to fake.
    """
    provider = os.getenv("LLM_PROVIDER", "").lower()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if provider == "openrouter" or (not provider and api_key):
        try:
            from .adapters.openrouter import OpenRouterAdapter
            return OpenRouterAdapter()
        except Exception as exc:
            logger.warning(f"Failed to initialize OpenRouterAdapter ({exc}). Falling back to FakeLLMService.")
            return FakeLLMService()
    
    return FakeLLMService()