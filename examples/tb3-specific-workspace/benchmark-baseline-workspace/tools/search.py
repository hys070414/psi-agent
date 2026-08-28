"""Search tool — find files by name pattern or search file contents."""

from __future__ import annotations

import asyncio
import shutil


async def tool(pattern: str, mode: str = "content", path: str = ".", max_results: int = 50) -> str:
    """Search for files by name or search file contents.

    In "files" mode, uses find to locate files matching a glob pattern.
    In "content" mode, uses grep -rn to search for a pattern inside files.

    Args:
        pattern: In "files" mode, a glob pattern (e.g. "*.py", "**/*.json").
                  In "content" mode, a grep pattern (regex or literal string).
        mode: "files" to find files by name, "content" to grep file contents.
        path: Directory to search in (default: current directory).
        max_results: Maximum number of result lines to return.

    Returns:
        Matching file paths (files mode) or grep output (content mode),
        or an error message.
    """
    bash = shutil.which("bash")
    if not bash:
        return "[Error] bash not found on PATH"

    if mode == "files":
        cmd = f"find '{path}' -type f -name '{pattern}' 2>/dev/null | head -{max_results}"
    elif mode == "content":
        cmd = f"grep -rn -- '{pattern}' '{path}' 2>/dev/null | head -{max_results}"
    else:
        return f"[Error] Unknown mode: {mode}. Use 'files' or 'content'."

    process = await asyncio.create_subprocess_exec(
        bash,
        "-lc",
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
    except TimeoutError:
        process.kill()
        await process.communicate()
        return f"[Error] Search timed out: {pattern}"

    result = stdout.decode(errors="replace").strip()
    return result or "(no matches)"
