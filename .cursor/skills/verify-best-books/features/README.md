# best-books verification map

Maintained source for verifying user-facing behavior of the best-books downloader.

## Baseline preconditions

- Repo root checkout with `uv` on `PATH`.
- `uv sync --locked --group dev` completed.
- Doctor exits 0.
- Prefer disposable evidence run ids. Never point a full `main.py` run at a `books/` tree the user still needs.

## Driving conventions

- Every command goes through `uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py …` unless a feature file shows a literal `main.py` full-run recipe.
- Keep marker filters and flag values exact.
- Record exit code and the evidence path the helper prints.

## Proof and skip reporting

- Offline proof is doctor + `offline`.
- Live scrape proof needs `scrape-lists.json` with `list_count > 0` and sampled `book_count > 0`.
- Live Libgen proof needs `libgen-search.json` with `result_count > 0`, or an explicit environment failure (`exit=2` with connection error text).
- Do not report a skipped network feature as verified via offline tests.

## Features

- [Offline unit gates](./offline-unit-gates.md) CI-equivalent proof with no network.
- [List catalog scrape](./list-catalog-scrape.md) best-books.dev list and book parsing via production `Scraper`.
- [Libgen EPUB search](./libgen-epub-search.md) single-title Libgen search via production `Libgen`.
- [Full download run](./full-download-run.md) real `main.py` path in a disposable cwd (manual, expensive).
