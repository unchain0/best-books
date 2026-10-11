# Live Libgen search

Opt-in proof that Libgen title search returns book objects for a known title. Manual only; not part of default CI.

## Sub-features

- `search-known-title` finds at least one result for a popular book.
- `search-missing-title` returns an empty list for nonsense input.

## How to get to it (user POV)

- User runs the downloader; each book triggers a Libgen title search before EPUB download.

## Driving it with uv/pytest

Preconditions:

- Outbound HTTPS to Libgen mirrors works from this machine.
- Accept that mirrors often reset connections; treat connection errors as environment failure, not product regression, unless the client code clearly mishandles a valid response.

- Action: run network-marked libgen tests. Command: `uv run pytest -m network tests/test_libgen.py -v`. Expect: exit 0 when the mirror is up; on `ConnectionResetError` / `RequestException` to libgen hosts, record skip/environment failure rather than changing product code without evidence of a logic bug.

## Gotchas

- CI deliberately excludes this feature via `-m "not network and not slow"`.
- Never unmark these tests to "get CI green" without replacing them with mocked unit coverage.
