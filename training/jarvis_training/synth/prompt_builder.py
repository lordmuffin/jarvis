"""Build the grounding prompts for Gemini synthetic data generation.

The system prompt is the integrity boundary of the entire training set. Its job
is to lock Gemini 2.5 Pro into the role of a synthesis engine over the user's
observed vault text, never an author of new personas, preferences, or facts.

This module never calls any API. It only constructs strings. The Step 1.2 gate
requires the user to review the rendered system prompt (see render_for_review)
before any Gemini client implementation is wired up.
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

from jarvis_training.intents import (
    INTENT_DEFINITIONS,
    INTENT_ORDER,
    INTENT_SCHEMA_VERSION,
    Intent,
)
from jarvis_training.synth.vault_loader import VaultChunk


# Loose cap; the actual cap is Gemini's context window and the practical desire
# to keep one prompt focused on patterns relevant to one target intent.
MAX_CHUNKS_PER_BATCH = 40
MAX_CHARS_PER_CHUNK = 1_500


SYSTEM_PROMPT_TEMPLATE = dedent("""\
    You are a synthesis engine for an offline personal AI assistant's intent-router
    training set. You produce JSONL records, one per line, no markdown fences.

    ## HARD CONSTRAINTS (non-negotiable; violations cause training to be discarded)

    1. You are NOT an author. You are a pattern-extractor and reformulator.
    2. Every record MUST be grounded in patterns observable in the VAULT CHUNKS
       supplied in the user message. If a pattern cannot be observed there, do
       not produce records that depend on it.
    3. Do NOT invent personas, preferences, relationships, projects, people,
       places, deadlines, or facts. Do NOT extrapolate from one observed pattern
       into adjacent ones.
    4. The `text` field of each record is what an incoming event might LOOK LIKE
       (an email subject + body snippet, a calendar entry's title, a manual
       paste, a notification text). Vary surface form heavily; do not paraphrase
       the same observed phrasing 50 ways.
    5. Cite the vault chunk you grounded each record in via `vault_source_chunk_id`.
       This must be one of the chunk_ids in the user message — chunk_ids the
       validator can resolve. Dangling ids cause the row to be dropped.
    6. The `rationale` field is one sentence in English explaining why this
       text → this intent. Used by the human reviewer; do not write boilerplate.

    ## INTENT SCHEMA (version {schema_version} — case-sensitive)

    {intent_block}

    ## OUTPUT FORMAT

    JSONL — one record per line. No surrounding array, no markdown fences, no
    leading prose. Each record:

      {{"text": "...", "intent": "<one of the seven>", "rationale": "...", "vault_source_chunk_id": "<id>"}}

    No trailing commas. UTF-8. If you cannot produce a grounded record, omit it
    rather than padding.
""")


USER_PROMPT_TEMPLATE = dedent("""\
    TARGET_INTENT: {target_intent}
    TARGET_COUNT: {target_count}

    The user wants {target_count} new records labeled `{target_intent}`, grounded
    in the vault chunks below.

    Variation requirements:
      * vary length: some 1-line subjects, some multi-paragraph bodies.
      * vary source channels in tone (email vs calendar entry vs notification
        snippet vs manual paste). The classifier sees the same `text` field
        regardless of channel, but the surface form should look like real events.
      * do NOT cluster records around any single chunk. Spread groundings.

    ## VAULT CHUNKS

    {chunks_block}

    Produce exactly {target_count} JSONL records. Begin output on the next line.
""")


@dataclass(frozen=True)
class PromptBatch:
    system_prompt: str
    user_prompt: str
    target_intent: Intent
    target_count: int
    chunk_ids: tuple[str, ...]


def _render_intent_block() -> str:
    lines = []
    for intent in INTENT_ORDER:
        lines.append(f"- `{intent.value}` — {INTENT_DEFINITIONS[intent]}")
    return "\n".join(lines)


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 1].rstrip() + "…"


def _render_chunks_block(chunks: list[VaultChunk]) -> str:
    bits = []
    for c in chunks:
        heading = c.heading or "(preamble)"
        body = _truncate(c.text, MAX_CHARS_PER_CHUNK)
        bits.append(
            f"--- chunk_id={c.chunk_id} source={c.source_path} heading={heading!r}\n{body}"
        )
    return "\n\n".join(bits)


def build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        schema_version=INTENT_SCHEMA_VERSION,
        intent_block=_render_intent_block(),
    )


def build_batch(
    target_intent: Intent,
    target_count: int,
    vault_chunks: list[VaultChunk],
) -> PromptBatch:
    """Construct one PromptBatch for one Gemini call.

    The caller is responsible for slicing the full vault into the chunks list it
    passes in. Typically: pre-shuffle the vault by chunk_id, take MAX_CHUNKS_PER_BATCH
    per call, rotate the window across calls so different chunks ground different
    batches.
    """
    if target_count < 1:
        raise ValueError("target_count must be >= 1")
    if not vault_chunks:
        raise ValueError("vault_chunks must not be empty — synthesis is grounding-only")
    if len(vault_chunks) > MAX_CHUNKS_PER_BATCH:
        vault_chunks = vault_chunks[:MAX_CHUNKS_PER_BATCH]

    system = build_system_prompt()
    user = USER_PROMPT_TEMPLATE.format(
        target_intent=target_intent.value,
        target_count=target_count,
        chunks_block=_render_chunks_block(vault_chunks),
    )
    return PromptBatch(
        system_prompt=system,
        user_prompt=user,
        target_intent=target_intent,
        target_count=target_count,
        chunk_ids=tuple(c.chunk_id for c in vault_chunks),
    )


def render_for_review() -> str:
    """Produce the prompt-review artifact the user reads before unblocking 1.2.

    No vault data here — just the system prompt skeleton and the user prompt
    template, so the review focuses on the rules, not on any specific batch.
    """
    return (
        "# ===== SYSTEM PROMPT =====\n\n"
        + build_system_prompt()
        + "\n\n# ===== USER PROMPT TEMPLATE (per-call) =====\n\n"
        + USER_PROMPT_TEMPLATE
    )
