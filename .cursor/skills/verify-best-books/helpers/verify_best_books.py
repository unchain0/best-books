#!/usr/bin/env python3
"""Verification harness for the best-books CLI.

Agent-facing helper. Invoke via:
  uv run python .cursor/skills/verify-best-books/helpers/verify_best_books.py <command>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_ROOT = Path(__file__).resolve().parents[1] / "evidence"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _evidence_dir(run_id: str | None = None) -> Path:
    d = EVIDENCE_ROOT / (run_id or _run_id())
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cmd_doctor(args: argparse.Namespace) -> int:
    out_dir = _evidence_dir(args.run_id)
    lines: list[str] = []
    rc = 0

    py = sys.version_info
    lines.append(f"python={py.major}.{py.minor}.{py.micro}")
    if (py.major, py.minor) != (3, 13):
        lines.append("FAIL: require Python 3.13")
        rc = 1
    else:
        lines.append("ok: python 3.13")

    os.chdir(REPO_ROOT)
    try:
        from scripts.libgen import DownloadResult, Libgen  # noqa: F401
        from scripts.scraper import Scraper, run_scraper  # noqa: F401
        from scripts.utils import BookInfo, filter_results, slugify  # noqa: F401

        lines.append(f"ok: imports (repo_root={REPO_ROOT})")
    except Exception as e:
        lines.append(f"FAIL: import error: {type(e).__name__}: {e}")
        rc = 1

    for label, cmd in (
        ("ruff", ["uv", "run", "ruff", "check", "."]),
        ("mypy", ["uv", "run", "mypy", "."]),
    ):
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        lines.append(f"$ {' '.join(cmd)}")
        lines.append(proc.stdout or "")
        lines.append(proc.stderr or "")
        lines.append(f"exit={proc.returncode}")
        if proc.returncode != 0:
            rc = 1
            lines.append(f"FAIL: {label}")
        else:
            lines.append(f"ok: {label}")

    text = "\n".join(lines).rstrip() + "\n"
    _write(out_dir / "doctor.txt", text)
    print(text, end="")
    print(f"evidence={out_dir / 'doctor.txt'}")
    return rc


def cmd_offline(args: argparse.Namespace) -> int:
    out_dir = _evidence_dir(args.run_id)
    cmd = [
        "uv",
        "run",
        "pytest",
        "-m",
        "not network and not slow",
        "-v",
        "--tb=short",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    body = (
        f"$ {' '.join(cmd)}\n"
        f"{proc.stdout}\n{proc.stderr}\nexit={proc.returncode}\n"
    )
    _write(out_dir / "pytest-offline.txt", body)
    print(body, end="")
    print(f"evidence={out_dir / 'pytest-offline.txt'}")
    return proc.returncode


def cmd_scrape_lists(args: argparse.Namespace) -> int:
    """Drive production Scraper list discovery against best-books.dev.

    Does not download books. Does not write under the user's books/.
    """
    out_dir = _evidence_dir(args.run_id)
    lists: list[tuple[str, str]] = []
    book_counts: list[dict[str, object]] = []

    # Isolate cwd side effects: Scraper setup_logger writes under logs/.
    # _get_all_lists / _get_books_from_list only HTTP + parse (no books/ mkdir).
    with tempfile.TemporaryDirectory(prefix="best-books-verify-") as tmp:
        tmp_path = Path(tmp)
        prev = Path.cwd()
        try:
            os.chdir(tmp_path)
            from scripts.scraper import Scraper

            scraper = Scraper()
            try:
                lists = scraper._get_all_lists()
                sample = lists[: max(0, args.max_lists)]
                for title, url in sample:
                    books = scraper._get_books_from_list(url)
                    book_counts.append(
                        {
                            "title": title,
                            "url": url,
                            "book_count": len(books),
                            "sample": [
                                {"title": b.title, "author": b.author}
                                for b in books[:3]
                            ],
                        }
                    )
            except Exception as e:
                body = f"error={type(e).__name__}: {e}\n"
                _write(out_dir / "scrape-lists.txt", body)
                print(body, end="")
                print(f"evidence={out_dir / 'scrape-lists.txt'}")
                return 2
        finally:
            os.chdir(prev)

    payload = {
        "base_url": "https://www.best-books.dev/",
        "list_count": len(lists),
        "sampled": book_counts,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    _write(out_dir / "scrape-lists.json", text)

    ok = len(lists) > 0 and all(int(x["book_count"]) > 0 for x in book_counts)
    summary = (
        f"list_count={len(lists)}\n"
        f"sampled={len(book_counts)}\n"
        f"ok={ok}\n"
        f"evidence={out_dir / 'scrape-lists.json'}\n"
    )
    _write(out_dir / "scrape-lists.txt", summary + text)
    print(summary, end="")
    print(text, end="")
    return 0 if ok else 1


def cmd_libgen_search(args: argparse.Namespace) -> int:
    """Drive production Libgen.search_title for one known book. Network."""
    out_dir = _evidence_dir(args.run_id)
    os.chdir(REPO_ROOT)
    from scripts.libgen import Libgen

    libgen = Libgen(title=args.title, author=args.author)
    try:
        results = libgen.search_title()
    except Exception as e:
        body = f"error={type(e).__name__}: {e}\n"
        _write(out_dir / "libgen-search.txt", body)
        print(body, end="")
        print(f"evidence={out_dir / 'libgen-search.txt'}")
        return 2

    rows = []
    for book in results[:5]:
        rows.append(
            {
                "title": getattr(book, "title", None),
                "author": getattr(book, "author", None),
                "extension": getattr(book, "extension", None),
            }
        )
    payload = {
        "query_title": libgen.title,
        "query_author": libgen.author,
        "result_count": len(results),
        "sample": rows,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    _write(out_dir / "libgen-search.json", text)
    ok = len(results) > 0
    summary = f"result_count={len(results)}\nok={ok}\nevidence={out_dir / 'libgen-search.json'}\n"
    _write(out_dir / "libgen-search.txt", summary + text)
    print(summary, end="")
    print(text, end="")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="verify-best-books harness")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_run_id(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--run-id",
            default=None,
            help="evidence subdirectory name",
        )

    p_doctor = sub.add_parser("doctor", help="read-only health check")
    add_run_id(p_doctor)
    p_doctor.set_defaults(func=cmd_doctor)

    p_offline = sub.add_parser("offline", help="CI-equivalent offline pytest")
    add_run_id(p_offline)
    p_offline.set_defaults(func=cmd_offline)

    p_lists = sub.add_parser(
        "scrape-lists", help="live best-books.dev list+book parse (no download)"
    )
    add_run_id(p_lists)
    p_lists.add_argument("--max-lists", type=int, default=1)
    p_lists.set_defaults(func=cmd_scrape_lists)

    p_libgen = sub.add_parser("libgen-search", help="live Libgen title search")
    add_run_id(p_libgen)
    p_libgen.add_argument("--title", default="Python Crash Course")
    p_libgen.add_argument("--author", default="Eric Matthes")
    p_libgen.set_defaults(func=cmd_libgen_search)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
