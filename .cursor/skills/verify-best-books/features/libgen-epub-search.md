# Libgen EPUB search

Prove a single book title resolves to one or more EPUB records on Libgen through production `Libgen.search_title` (filtered to `extension=epub`, then author-flexible `filter_results`).

## Sub-features

- `search-known-title` finds results for a popular book.
- `author-filter` applies surname matching without dropping all hits when formats differ.

## How to get to it (user POV)

- During `main.py`, each book constructs `Libgen(mirror="gl", title=…, author=…)` and calls `search_title()` before `download`.
- Developers can also run `scripts/libgen.py` as `__main__` for a single hard-coded title.

## Driving it with verify_best_books.py

Preconditions:

- Doctor passed.
- Outbound HTTPS to Libgen mirrors works. Mirrors frequently reset connections.

- **Search.** Run `uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py libgen-search --title "Python Crash Course" --author "Eric Matthes" --run-id libgen-demo`.
- **Proof on success.** Exit code `0`. `evidence/libgen-demo/libgen-search.json` shows `result_count > 0` and sample rows with `title` / `author`.
- **Proof on environment failure.** Exit code `2` with `error=…` in `libgen-search.txt`. Report as environment failure, not a product regression, unless a valid HTML response is clearly misparsed.

## Gotchas

- CI excludes this path (`not network and not slow`). Green CI never proves this feature.
- Default product mirror in `Scraper._download_book` is `gl`; `Libgen` default init mirror is `li`. The helper uses the class default unless you change the script. Note which mirror you hit when filing failures.
- Do not download EPUBs in this feature. Download belongs to full-download-run.
