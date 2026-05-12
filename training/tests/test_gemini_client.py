"""Tests for the Gemini client adapter.

Network calls are NOT exercised — we'd need the SDK installed and an API key.
We test:
  - The robust JSONL parser handles the cases Gemini commonly emits.
  - GeminiSettings.from_env() surfaces missing config rather than falling back.
"""

from __future__ import annotations

import os

import pytest

from jarvis_training.synth.gemini_client import (
    GeminiConfigError,
    GeminiSettings,
    _parse_jsonl_robust,
)


def test_parse_clean_jsonl():
    text = (
        '{"text":"a","intent":"draft.email","rationale":"r","vault_source_chunk_id":"x"}\n'
        '{"text":"b","intent":"dismiss","rationale":"r","vault_source_chunk_id":"x"}\n'
    )
    out = list(_parse_jsonl_robust(text))
    assert len(out) == 2
    assert out[0]["intent"] == "draft.email"


def test_parse_strips_markdown_fences():
    text = (
        "```json\n"
        '{"text":"a","intent":"draft.email","rationale":"r","vault_source_chunk_id":"x"}\n'
        "```\n"
    )
    out = list(_parse_jsonl_robust(text))
    assert len(out) == 1


def test_parse_tolerates_blank_lines_and_whitespace():
    text = (
        '\n   \n'
        '   {"text":"a","intent":"dismiss","rationale":"r","vault_source_chunk_id":"x"}   \n'
        '\n'
    )
    out = list(_parse_jsonl_robust(text))
    assert len(out) == 1


def test_parse_drops_malformed_lines():
    text = (
        'not json\n'
        '{"text":"a","intent":"dismiss","rationale":"r","vault_source_chunk_id":"x"}\n'
        '{half-json\n'
    )
    out = list(_parse_jsonl_robust(text))
    assert len(out) == 1


def test_parse_drops_top_level_arrays_and_strings():
    text = (
        '"just a string"\n'
        '[1,2,3]\n'
        '{"text":"a","intent":"dismiss","rationale":"r","vault_source_chunk_id":"x"}\n'
    )
    out = list(_parse_jsonl_robust(text))
    assert len(out) == 1


def test_settings_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("JARVIS_CLOUD_LLM_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_CLOUD_LLM_PROVIDER", raising=False)
    with pytest.raises(GeminiConfigError, match="JARVIS_CLOUD_LLM_API_KEY"):
        GeminiSettings.from_env()


def test_settings_wrong_provider_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JARVIS_CLOUD_LLM_API_KEY", "test-key")
    monkeypatch.setenv("JARVIS_CLOUD_LLM_PROVIDER", "openai")
    with pytest.raises(GeminiConfigError, match="only 'gemini' is wired"):
        GeminiSettings.from_env()


def test_settings_happy_path(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JARVIS_CLOUD_LLM_API_KEY", "test-key")
    monkeypatch.setenv("JARVIS_CLOUD_LLM_PROVIDER", "gemini")
    s = GeminiSettings.from_env()
    assert s.api_key == "test-key"
    assert s.model == "gemini-2.5-pro"


def test_settings_defaults_provider_to_gemini(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JARVIS_CLOUD_LLM_API_KEY", "test-key")
    monkeypatch.delenv("JARVIS_CLOUD_LLM_PROVIDER", raising=False)
    s = GeminiSettings.from_env()
    assert s.api_key == "test-key"
