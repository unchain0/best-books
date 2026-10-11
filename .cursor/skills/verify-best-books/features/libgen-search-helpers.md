# Libgen search helpers

Prove pure helper behavior used when filtering Libgen results: author/title formatting and flexible author matching.

## Sub-features

- `get-author-title` normalizes casing and ampersands.
- `filter-results` matches by surname fragments and falls back when nothing matches.

## How to get to it (user POV)

- User never calls these directly. They run inside Libgen search before download.
- Developers exercise them through `tests/test_libgen.py` utility cases.

## Driving it with uv/pytest

Preconditions:

- Offline baseline ready.

- Action: run helper tests only. Command: `uv run pytest tests/test_libgen.py::TestUtilsFunctions -q`. Expect: all passed, exit 0.
- Action: run slugify tests. Command: `uv run pytest tests/test_scraper.py::TestSlugify -q`. Expect: all passed, exit 0.

## Gotchas

- These tests must stay free of network I/O. If a helper test starts calling Libgen, mark it `network` and move the proof to the live feature file.
