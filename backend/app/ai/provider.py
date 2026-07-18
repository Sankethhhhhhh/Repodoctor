from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str: ...

    @abstractmethod
    def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]: ...


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"

    async def generate(self, prompt: str, system: str = "") -> str:
        import httpx

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, "max_tokens": 2048},
                timeout=60.0,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return str(data["choices"][0]["message"]["content"])

    async def _generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        text = await self.generate(prompt, system)
        yield text

    def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        return self._generate_stream(prompt, system)


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        import httpx

        body: dict[str, object] = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
                timeout=60.0,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return str(data["content"][0]["text"])

    async def _generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        text = await self.generate(prompt, system)
        yield text

    def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        return self._generate_stream(prompt, system)


class OllamaProvider(AIProvider):
    def __init__(self, model: str, base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url

    async def generate(self, prompt: str, system: str = "") -> str:
        import httpx

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=120.0,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return str(data["message"]["content"])

    async def _generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        import httpx

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with (
            httpx.AsyncClient() as client,
            client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": True},
                timeout=120.0,
            ) as response,
        ):
            import json

            async for line in response.aiter_lines():
                if line:
                    data: dict[str, Any] = json.loads(line)
                    if "message" in data:
                        msg = data["message"]
                        if isinstance(msg, dict):
                            content = msg.get("content", "")
                            if isinstance(content, str):
                                yield content

    def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        return self._generate_stream(prompt, system)


class NoOpProvider(AIProvider):
    async def generate(self, _prompt: str, _system: str = "") -> str:
        return "AI remediation is not configured. Set APP_AI_PROVIDER, APP_AI_MODEL, and APP_AI_API_KEY to enable."

    async def _generate_stream(self, _prompt: str, _system: str = "") -> AsyncIterator[str]:
        yield await self.generate(_prompt, _system)

    def generate_stream(self, _prompt: str, _system: str = "") -> AsyncIterator[str]:
        return self._generate_stream(_prompt, _system)


def get_provider() -> AIProvider:
    provider_name = settings.ai_provider.lower()
    model = settings.ai_model
    api_key = settings.ai_api_key

    if provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model, base_url=settings.ai_base_url)
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    if provider_name == "ollama":
        return OllamaProvider(model=model, base_url=settings.ai_base_url or "http://localhost:11434")

    return NoOpProvider()
