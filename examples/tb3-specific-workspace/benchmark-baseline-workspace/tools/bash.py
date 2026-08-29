"""Bash tool for executing shell commands."""

from __future__ import annotations

import asyncio
import os
import shutil

import anyio


async def _find_bash() -> str | None:
    if os.name == "nt":
        candidates: list[anyio.Path] = []
        git = shutil.which("git")
        if git:
            git_root = (await anyio.Path(git).resolve()).parents[1]
            candidates.extend([git_root / "bin" / "bash.exe", git_root / "usr" / "bin" / "bash.exe"])
        candidates.extend(
            [
                anyio.Path("C:/Program Files/Git/bin/bash.exe"),
                anyio.Path("C:/Program Files/Git/usr/bin/bash.exe"),
                anyio.Path("D:/Program Files/Git/bin/bash.exe"),
                anyio.Path("D:/Program Files/Git/usr/bin/bash.exe"),
            ]
        )
        for candidate in candidates:
            if await candidate.is_file():
                return str(candidate)

    return shutil.which("bash")


DEFAULT_MAX_OUTPUT_CHARS = 12000
"""Hard cap on characters returned by a single bash call (guards the context window)."""


async def bash(command: str, timeout_seconds: int = 120, max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS) -> str:
    """Execute a shell command and return its output.

    Each call spawns a fresh ``bash -lc`` subprocess, so shell state (working
    directory, exported variables, activated venvs) does NOT persist across
    calls — chain dependent steps with ``&&`` inside one command.

    Args:
        command: The shell command to execute.
        timeout_seconds: Maximum seconds to wait for the command to complete.
        max_output_chars: Maximum characters of combined stdout/stderr to return.
            Longer output is truncated to a head+tail window with a note.

    Returns:
        Combined stdout and stderr output, with exit code appended on failure.
    """
    bash = await _find_bash()
    if not bash:
        return (
            "[Error] bash executable was not found on PATH. Install Git Bash, WSL, or bash before using this workspace."
        )

    process = await asyncio.create_subprocess_exec(
        bash,
        "-lc",
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
    except TimeoutError:
        process.kill()
        await process.communicate()
        return f"[Error] Command timed out after {timeout_seconds}s: {command}"

    out = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace")
    combined = (out + err).rstrip()

    if len(combined) > max_output_chars:
        head = max_output_chars // 2
        tail = max_output_chars - head
        combined = (
            combined[:head]
            + f"\n... [output truncated: {len(combined)} chars total, showing first {head} and last {tail}] ...\n"
            + combined[-tail:]
        )

    if process.returncode != 0:
        combined += f"\n[Exit code: {process.returncode}]"

    return combined or "(no output)"
