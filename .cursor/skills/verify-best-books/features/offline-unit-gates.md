# Offline unit gates

Prove the same offline quality gates CI runs before merge: imports, ruff, mypy, and pytest without network or slow download tests.

## Sub-features

- `doctor-toolchain` confirms Python 3.13, imports, ruff, and mypy.
- `pytest-offline` runs the CI marker expression.

## How to get to it (user POV)

- A developer pushes to GitHub and the CI workflow runs lint, offline pytest, and typecheck.
- A local agent runs the same gates before pushing.

## Driving it with verify_best_books.py

Preconditions:

- Repo root is the shell cwd for uv workspace resolution.
- `uv sync --locked --group dev` succeeded.

- **Doctor.** Run `uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py doctor --run-id offline-demo`. Exit code `0`. `evidence/offline-demo/doctor.txt` contains `ok: python 3.13`, `ok: imports`, `ok: ruff`, and `ok: mypy`.
- **Offline tests.** Run `uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py offline --run-id offline-demo`. Exit code `0`. `evidence/offline-demo/pytest-offline.txt` shows zero failed tests and deselected `network`/`slow` items.
- **Proof.** Both evidence files exist after the commands return. The pytest summary line reports only passes among selected tests.

## Gotchas

- Tests that call Libgen or best-books.dev must carry `@pytest.mark.network` or `@pytest.mark.slow`. Unmarked live tests run under this gate and fail when mirrors reset connections.
- Do not treat this feature as proof that Libgen or the site still respond.
