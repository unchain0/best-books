# Full download run

Prove the real user entrypoint `uv run python main.py` scrapes all lists and downloads EPUBs into `books/`. Expensive, network-heavy, and disk-heavy. Manual only.

## Sub-features

- `banner-and-config` shows the Rich banner and detected worker counts.
- `parallel-lists` creates per-list folders under `books/<slug>/`.
- `epub-write` writes non-empty `.epub` files or skips existing ones.
- `summary` prints final stats and points at `books/` and `logs/`.

## How to get to it (user POV)

- From the repo docs: install with `uv sync`, then `uv run python main.py` with no arguments.
- The process runs until every list finishes or the user hits Ctrl+C.

## Driving it with main.py

Preconditions:

- Explicit human or task request for a full end-to-end download proof.
- Disposable empty directory as cwd (never the live repo if `books/` already has user data).
- Gigabytes free and stable network. Expect a long runtime.

- **Isolate cwd.** Run `WORKDIR=$(mktemp -d /tmp/best-books-full-XXXX) && cd "$WORKDIR"`.
- **Launch.** Run `uv run --directory <repo-root> python <repo-root>/main.py`.
- **Observe start.** stdout shows `Best Books Downloader`, performance config lines, and list discovery counts.
- **Proof (partial acceptable).** After at least one list completes, `ls books/*/*.epub` shows one or more non-empty files. `logs/download_*.log` exists under the disposable cwd. Capture `find books -name '*.epub' | head` and `du -sh books` into `evidence/<run-id>/full-run-tree.txt`.
- **Stop early if needed.** Ctrl+C. Scraper prints partial stats. Keep evidence; delete only the disposable workdir after copying proof out.

## Gotchas

- No dry-run flag exists. The command always intends real downloads.
- Re-running against an existing `books/` skips existing epubs (`already_existed`) and still hammers Libgen for missing titles.
- Never kill by process name. Kill only the PID you started.
- Copy proof out of the disposable workdir before deleting it. Cleanup must not eat evidence under `.cursor/skills/verify-best-books/evidence/`.
