# best-books verification map

Maintained source for verifying user-facing behavior of the best-books downloader CLI.

## Baseline preconditions

- Python 3.13 and `uv` available.
- `uv sync --locked --group dev` completed in the repo root.
- Working directory is the repo root.
- Do not point verification at a real `books/` tree the user cares about. Use a disposable directory when a download proof is required.
- Prefer offline recipes. Live Libgen and best-books.dev calls are flaky from CI and shared networks.

## Driving conventions

- Run every command through `uv run`.
- Treat pytest marker filters as part of the command contract.
- Capture exit code and the short test summary line.
- A deselected network test is not evidence that Libgen search works.

## Proof and skip reporting

- Offline proof is the CI marker run plus doctor.
- Network proof must show a live request path and a non-empty or intentionally empty result with the remote reachable.
- Report unreachable Libgen or best-books.dev with the exception text; do not retry endlessly.

## Features

- [Offline unit gates](./offline-unit-gates.md) covers CI-equivalent lint-free unit proof.
- [Libgen search helpers](./libgen-search-helpers.md) covers pure author/title filtering without the network.
- [Live Libgen search](./live-libgen-search.md) covers opt-in network search (manual only).
