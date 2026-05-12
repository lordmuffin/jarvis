"""Walk a vault directory, read *.md, chunk by heading, strip Obsidian wikilinks.

Every chunk carries a deterministic chunk_id (sha256 of source-relative path + the
post-wikilink-strip text). The chunk_id is what later stages cite as
`vault_source_chunk_id` — the validator uses it to drop dangling-chunk records.

This module does NOT read frontmatter, follow links, or interpret Dataview/Templater
syntax. It is intentionally simple: anything fancier becomes a maintenance trap and
silently changes the input distribution to MobileBERT.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


# [[Target]] or [[Target|Display text]] — both forms preserved.
WIKILINK_RE = re.compile(r"\[\[([^\[\]|\n]+)(?:\|([^\[\]\n]+))?\]\]")

# ATX-style headings (1-6 '#'s followed by space). Setext headings (=== / ---)
# are not used in this vault per convention; if needed later, extend here.
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class VaultChunk:
    """One heading-bounded block of vault text.

    chunk_id is stable across runs: same content at the same path → same id.
    """

    chunk_id: str
    source_path: str  # POSIX path relative to vault_root
    heading: str | None  # heading text, or None for the pre-first-heading preamble
    text: str  # post-wikilink-strip body, including the heading line itself
    link_targets: tuple[str, ...]  # in-order, may contain duplicates


def _strip_wikilinks(text: str) -> tuple[str, tuple[str, ...]]:
    """Return (clean_text, link_targets_in_order)."""
    targets: list[str] = []

    def _sub(m: re.Match[str]) -> str:
        target = m.group(1).strip()
        display = m.group(2)
        targets.append(target)
        return (display.strip() if display else target)

    clean = WIKILINK_RE.sub(_sub, text)
    return clean, tuple(targets)


def _chunk_id_for(source_path: str, text: str) -> str:
    h = hashlib.sha256()
    h.update(source_path.encode("utf-8"))
    h.update(b"\n")
    h.update(text.encode("utf-8"))
    return h.hexdigest()[:16]


def iter_chunks(vault_root: Path) -> Iterator[VaultChunk]:
    """Yield one VaultChunk per heading block in each .md file under vault_root.

    Files are read in sorted path order for determinism. Empty blocks (e.g. two
    headings with nothing between them) are skipped.
    """
    vault_root = vault_root.resolve()
    if not vault_root.is_dir():
        raise NotADirectoryError(f"vault_root does not exist or is not a dir: {vault_root}")

    for md in sorted(vault_root.rglob("*.md")):
        rel = md.relative_to(vault_root).as_posix()
        raw = md.read_text(encoding="utf-8", errors="replace")
        yield from _chunks_for_file(rel, raw)


def _chunks_for_file(rel_path: str, raw: str) -> Iterator[VaultChunk]:
    # Build a list of (offset, heading_text_or_None) cut points.
    cuts: list[tuple[int, str | None]] = [(0, None)]
    for m in HEADING_RE.finditer(raw):
        cuts.append((m.start(), m.group(2).strip()))
    cuts.append((len(raw), None))

    for i in range(len(cuts) - 1):
        start_pos, heading = cuts[i]
        end_pos, _ = cuts[i + 1]
        body = raw[start_pos:end_pos].strip()
        if not body:
            continue
        clean, targets = _strip_wikilinks(body)
        yield VaultChunk(
            chunk_id=_chunk_id_for(rel_path, clean),
            source_path=rel_path,
            heading=heading,
            text=clean,
            link_targets=targets,
        )


def collect_chunk_ids(vault_root: Path) -> set[str]:
    """Helper for validate.py: the set of all valid chunk_ids in the vault."""
    return {c.chunk_id for c in iter_chunks(vault_root)}
