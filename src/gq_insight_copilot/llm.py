from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Return model text for a prompt."""
        ...


@dataclass
class LocalLLMClient:
    """A deterministic placeholder that keeps offline tests repeatable."""

    def complete(self, prompt: str) -> str:
        return json.dumps({"mode": "local", "received_prompt_chars": len(prompt)})


@dataclass
class OpenAIClient:
    model: str = "gpt-4o-mini"

    def complete(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the llm extra: pip install -e '.[llm]'") from exc

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", self.model),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert UX research synthesis assistant. Return only valid JSON. "
                        "Every claim must be grounded in the provided evidence candidates."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


def get_client(provider: str) -> LLMClient:
    if provider == "openai":
        return OpenAIClient()
    if provider == "local":
        return LocalLLMClient()
    raise ValueError(f"Unknown provider: {provider}")
