"""Search tool — find files by name pattern or search file contents."""

from __future__ import annotations

import re
from pathlib import Path

import anyio


async def search(pattern: str, mode: str = "content", path: str = ".", max_results: int = 50) -> str:
    """Search for files by name or search file contents.

    In "files" mode, uses ``pathlib.Path.glob`` to locate files matching a
    glob pattern (supports ``**`` for recursive matching, e.g. ``**/*.py``).
    In "content" mode, searches file contents with a regex (falls back to
    literal matching if the pattern is not valid regex).

    Args:
        pattern: In "files" mode, a glob pattern.
                  In "content" mode, a regex or literal string.
        mode: "files" to find files by name, "content" to grep file contents.
        path: Directory to search in (default: current directory).
        max_results: Maximum number of result lines to return.

    Returns:
        Matching file paths (files mode) or grep-style output (content mode),
        or an error message.
    """
    base = anyio.Path(path)
    if not await base.exists():
        return f"[Error] Path not found: {path}"
    if not await base.is_dir():
        return f"[Error] Not a directory: {path}"

    base_fs = Path(str(base))

    if mode == "files":
        return _search_files(base_fs, pattern, max_results)
    if mode == "content":
        return _search_content(base_fs, pattern, max_results)
    return f"[Error] Unknown mode: {mode}. Use 'files' or 'content'."


def _search_files(base: Path, pattern: str, max_results: int) -> str:
    results: list[str] = []
    try:
        for candidate in base.glob(pattern):
            if candidate.is_file():
                results.append(candidate.relative_to(base).as_posix())
                if len(results) >= max_results:
                    break
    except (OSError, ValueError) as exc:
        return f"[Error] Invalid glob pattern {pattern!r}: {exc}"
    return "\n".join(results) or "(no matches)"


def _search_content(base: Path, pattern: str, max_results: int) -> str:
    try:
        regex = re.compile(pattern)
    except re.error:
        regex = re.compile(re.escape(pattern))

    results: list[str] = []
    for candidate in base.rglob("*"):
        if not candidate.is_file():
            continue
        try:
            if candidate.stat().st_size > 5 * 1024 * 1024:
                continue
        except OSError:
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                rel = candidate.relative_to(base).as_posix()
                results.append(f"{rel}:{i}:{line}")
                if len(results) >= max_results:
                    return "\n".join(results)
    return "\n".join(results) or "(no matches)"
