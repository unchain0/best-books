# List catalog scrape

Prove the downloader can discover every book list on best-books.dev and parse title/author pairs from a list page, using the production `Scraper` methods the full run calls before any Libgen download.

## Sub-features

- `discover-lists` fetches the home page and collects `/list/…` button links.
- `parse-list-books` reads `collection-item-2` rows into `BookInfo` values with UTF-8 titles and authors.

## How to get to it (user POV)

- User runs `uv run python main.py`. The first visible steps are the performance banner and "Buscando listas de livros…", then per-list progress.
- There is no separate CLI subcommand; list discovery is the first phase of the full run.

## Driving it with verify_best_books.py

Preconditions:

- Doctor passed.
- Outbound HTTPS to `https://www.best-books.dev/` works.

- **Scrape one list sample.** Run `uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py scrape-lists --max-lists 1 --run-id lists-demo`. Exit code `0`.
- **Proof.** `evidence/lists-demo/scrape-lists.json` has `list_count > 0`. The first sampled entry has `book_count > 0` and a `sample` array of `{title, author}` objects with non-empty strings. Console summary prints `ok=True`.
- **Widen (optional).** Rerun with `--max-lists 3` when checking multiple categories.

## Gotchas

- Site markup classes (`button-2`, `collection-item-2`, `heading-5`, `text-block-8`) are the selectors. A redesign breaks this feature and the product together.
- The helper must not create `books/` in the repo. If you see a new `books/` under the repo root after this command, treat it as a harness bug.
- Connection failures are environment failures. Capture the exception text; do not loop retries without a product-level reason.
