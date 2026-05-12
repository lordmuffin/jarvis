"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_vault(tmp_path: Path) -> Path:
    """A tiny vault with two markdown files and a few headings + wikilinks.

    Returns the vault root path.
    """
    (tmp_path / "Areas" / "Work").mkdir(parents=True)
    (tmp_path / "Areas" / "Work" / "standup.md").write_text(
        """# Standup notes

Yesterday I worked on [[Auth refactor|the auth refactor]].
Blocked on [[Bob]] for the schema review.

## Today

Push the [[draft PR]] and ping [[Bob|@bob]] for review.

## Blockers

None.
""",
        encoding="utf-8",
    )
    (tmp_path / "Areas" / "Personal" / "Family.md").parent.mkdir(parents=True)
    (tmp_path / "Areas" / "Personal" / "Family.md").write_text(
        """Mom's birthday is in [[March]]. Email reminder set.

# Recurring chores

- water plants every [[Sunday]]
- laundry

# Random


""",
        encoding="utf-8",
    )
    return tmp_path
