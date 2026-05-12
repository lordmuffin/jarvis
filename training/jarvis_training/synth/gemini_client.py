"""Concrete JsonlClient backed by the google-genai SDK (Gemini 2.5 Pro).

Cleared the Step 1.2 prompt-review gate. The system prompt this client passes to
Gemini is produced by prompt_builder.build_system_prompt() — see
docs/prompt-review-1.2.txt for the artifact the user signed off on.

The class deliberately avoids any retry-with-backoff logic that could mask a
broken prompt (silent fallbacks are how this architecture dies — brief §
"Working Rules"). If the SDK raises, we surface it. The caller (generate.py)
is idempotent across runs, so a crashed call leaves a partial raw file the
next run picks up from.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass


DEFAULT_MODEL = "gemini-2.5-pro"
ENV_API_KEY = "JARVIS_CLOUD_LLM_API_KEY"
ENV_PROVIDER = "JARVIS_CLOUD_LLM_PROVIDER"


class GeminiConfigError(RuntimeError):
    """Raised when required env config is missing — never silently fall back."""


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str
    model: str = DEFAULT_MODEL
    temperature: float = 0.8
    max_output_tokens: int = 8192

    @classmethod
    def from_env(cls) -> GeminiSettings:
        provider = os.environ.get(ENV_PROVIDER, "gemini").lower()
        if provider != "gemini":
            raise GeminiConfigError(
                f"{ENV_PROVIDER}={provider!r} but only 'gemini' is wired in 1.2. "
                "Add an alternate adapter or change {ENV_PROVIDER}."
            )
        key = os.environ.get(ENV_API_KEY)
        if not key:
            raise GeminiConfigError(f"{ENV_API_KEY} is not set")
        return cls(api_key=key)


class GeminiClient:
    """Concrete implementation of generate.JsonlClient."""

    def __init__(self, settings: GeminiSettings | None = None) -> None:
        self._settings = settings or GeminiSettings.from_env()
        # Import lazily so test environments without google-genai installed can
        # still import the module (e.g. ruff/pytest CI without the gemini extra).
        try:
            from google import genai  # type: ignore[import-not-found]
        except ImportError as e:
            raise GeminiConfigError(
                "google-genai is not installed. Run: pip install -e \".[gemini]\""
            ) from e
        self._genai = genai
        self._client = genai.Client(api_key=self._settings.api_key)

    def generate_jsonl(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Iterable[dict]:
        """Single Gemini call. Parses the response text line-by-line as JSONL.

        Malformed lines are silently dropped here — generate.py's outer loop
        decides what to do when a batch produces nothing usable.
        """
        from google.genai import types  # type: ignore[import-not-found]

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self._settings.temperature,
            max_output_tokens=self._settings.max_output_tokens,
        )
        response = self._client.models.generate_content(
            model=self._settings.model,
            contents=user_prompt,
            config=config,
        )
        text = getattr(response, "text", None) or ""
        return list(_parse_jsonl_robust(text))


def _parse_jsonl_robust(text: str) -> Iterator[dict]:
    """Yield dicts from a string that's mostly JSONL.

    Tolerates: surrounding markdown fences (```json ... ```), blank lines,
    leading/trailing whitespace per line. Drops any line we can't parse.
    """
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Strip markdown fences if the model emitted them despite instructions.
        if line.startswith("```"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            yield obj
