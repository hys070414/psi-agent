---
name: _universal
description: "Universal working discipline that applies to every task across all benchmarks (always loaded)."
---
# Universal working discipline

Applies to every task regardless of domain or benchmark.

## Orientation
- Before deep reasoning, take a quick inventory of the environment. List files,
  check what tools and resources exist, read any provided instructions or README.
- Do not finish without at least one concrete action.
- Read the task's own provided sources, checkers, and interfaces before assuming
  textbook behaviour — implementations often diverge from canonical ones.

## Understand the task contract
- Read the task description carefully. Extract: the goal, required deliverables,
  constraints, and how success is measured.
- Match the expected output format exactly: the same command, paths, function
  signatures, and output format the evaluator will use. No private helper flags
  or alternative entry points.
- Never edit test harnesses, graders, or provided runners — those are restored
  at grading time. Fix YOUR work, not the checker.
- If the task names a specific output path, place the deliverable there. Drafting
  or iterating under a temporary path is fine, but the final version must live at
  the exact location the evaluator expects. Before declaring done, verify the
  deliverable exists at the correct path and is the version you validated.

## Verify before declaring done
- "It runs" is not success, and neither is "my own sanity check passed". Before
  finishing, reproduce the evaluator's judgement locally.
- Find and read the provided test/checker file (e.g. `tests/test_*.py`, a
  `verify.sh`, or the grader's own description). Extract the exact inputs, cases,
  and pass condition. Do NOT make up your own test cases — a self-built harness
  of invented samples that always "passes" is the #1 false-positive trap.
- Run the evaluator's own check against your work. If the evaluator compares
  bytes or numbers, diff your output against expected values at the evaluator's
  tolerance. If the evaluator runs commands, run those exact commands and check
  exit codes and stdout.
- Test every case the evaluator provides, each in isolation. Stop when enough is
  enough — once the evaluator's own cases pass, finalize rather than inventing
  extra cases or re-running a passing suite.
- If you genuinely cannot run the check, say so and test as close to the
  evaluator's real cases as possible rather than guessing.

## Shell hygiene
- The bash tool runs each command in a **fresh `bash -lc` subprocess**: working
  directory, exported environment variables, and activated venvs do **not** persist
  across calls. Chain dependent steps in one command with `&&` (e.g.
  `cd /path && python train.py`).
- Probe for missing tools up front and fall back (e.g. od/stat/python3) rather
  than repeatedly retrying an absent utility.
- To write a multi-line file, do NOT use a `cat <<'EOF' ... EOF` heredoc, and do
  NOT paste a large multi-line block in one command. Safer patterns:
    - **Large file (>20 lines)**: base64-encode the content and decode in place:
      `printf '%s' '<base64>' | base64 -d > /path/out`. One command, no escaping.
    - **Short file**: build line-by-line with appends, each its own command:
      `: > /path/out` then `printf '%s\n' 'line1' >> /path/out`.

## Long-running processes
- For commands that exceed the 120s bash timeout (ML training, model inference,
  compilation, proof checking), use `background_start` to launch them detached.
- `background_start` returns a `log_path` (under `<workspace>/.psi/background/<id>.log`);
  the process's stdout+stderr are **auto-appended** to that file. Poll progress by
  reading the log file (`read <log_path>`) instead of blocking the bash tool.
- Use `background_list` to check which background processes are still alive, and
  `background_stop` to terminate a stuck or finished one — don't let a dead process
  consume your entire budget.
- For very long tasks (estimated >10 min expert time), start the longest-running
  step early in the background and work on other parts while it runs.

## External resources and compliance
- `fetch` retrieves web pages as plain text — use it for reading documentation,
  API references, or general reference material.
- Do NOT use `fetch` (or any other tool) to search for or retrieve task-specific
  solutions, hints, leaderboards, or published answers for the current task.
  That is cheating and invalidates the evaluation.
- If a task provides files in formats you cannot read with the basic tools
  (PDFs, images, spreadsheets), use `read_pdf` for PDF text extraction.
- Probe for available system tools up front: `which python3 && which pip && which gcc`
  etc. Knowing what's installed saves repeated failures.

## Budget
- Commit to an implementation early; reserve most of the budget for writing,
  building, and debugging. If the same approach fails repeatedly, switch
  strategy rather than retrying minor variations.
- Don't let setup eat the budget. A slow install/compile should be ONE foreground
  command that runs to completion (chain a `&& echo __DONE__` marker), not a
  background job you poll across many empty turns — UNLESS it genuinely exceeds
  the 120s timeout, in which case use `background_start`.
- Watch the clock: if verification passes and you have spent a large share of
  the budget, finalize now rather than polishing.
