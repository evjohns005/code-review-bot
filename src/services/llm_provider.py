"""LLM service for managing LLM calls with retries and fallback mechanisms."""

import asyncio
from dataclasses import dataclass

from system.logs import logger
from config.settings import settings
from agent.prompts import load_system_prompt
from anthropic import AsyncAnthropic, DefaultAioHttpClient

_client: AsyncAnthropic | None = None

def get_anthropic_client(api_key: str) -> AsyncAnthropic:
    global _client
    if _client is None:
        # Optional performance enhancement with http_client
        _client = AsyncAnthropic(
            api_key=api_key,
            http_client=DefaultAioHttpClient(),
        )

    return _client


@dataclass(frozen=True)
class ClaudeModelConfig:
    name: str
    max_tokens: int

# Class-level variable containing all available LLM models
MODELS: dict[str, ClaudeModelConfig] = {
    "claude-sonnet-4-5": ClaudeModelConfig(name="claude-sonnet-4-5", max_tokens=settings.MAX_TOKENS),
    "claude-opus-4-6": ClaudeModelConfig(name="claude-opus-4-6", max_tokens=settings.MAX_TOKENS),
    "claude-haiku-4-5": ClaudeModelConfig(name="claude-haiku-4-5", max_tokens=settings.MAX_TOKENS),
}

class LLMService:
    def __init__(self):
        self.client = get_anthropic_client(settings.ANTHROPIC_API_KEY)
        self.fallback_order = [settings.DEFAULT_LLM_MODEL] + [
            m for m in MODELS if m != settings.DEFAULT_LLM_MODEL
        ]

    async def call(self, user_message: str) -> str:
        system = load_system_prompt()
        for model_name in self.fallback_order:
            cfg = MODELS[model_name]
            for attempt in range(settings.MAX_LLM_CALL_RETRIES):
                try:
                    message = await self.client.messages.create(
                        model=cfg.name,
                        max_tokens=cfg.max_tokens,
                        system=system,
                        messages=[{"role": "user", "content": user_message}]
                    )
                    return message.content[0].text
                except Exception as e:
                    logger.warning(
                        "model_failed",
                        model=model_name,
                        attempt=attempt + 1,
                        error=str(e)
                        )
                logger.error("model_exhausted_retries", model=model_name)
        raise RuntimeError("All models failed after retries")

llm_service = LLMService()



