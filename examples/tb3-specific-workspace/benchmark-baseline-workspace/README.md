# benchmark-baseline workspace

A minimal psi-agent workspace designed as the **common baseline** across all four
benchmark evaluation lines: TB 2.1, TB 3.0, tau2, and GAIA.

## Design principle

The initial Skills/Tools Setup is **identical** for all four benchmarks. This ensures:

- No per-benchmark tool/skill configuration drift
- Baseline (HaiTun Base) and experimental (HaiTun Full) differ only in skills,
  not in core tools
- Cross-benchmark ablation comparisons are not confounded by tool differences

## Structure

- `tools/` — 11 universal tools:
  - `bash.py` — shell command execution (fresh `bash -lc` per call; 120s default timeout; output truncated)
  - `read.py` — file reading with offset/limit
  - `write.py` — file creation/overwrite
  - `edit.py` — precise string replacement
  - `search.py` — file finding (glob, supports `**`) + content search (regex)
  - `list_dir.py` — directory browsing (flat or recursive)
  - `background_start.py` — launch detached long-running processes (auto-captures stdout/stderr to a log file, returns `log_path`)
  - `background_stop.py` — terminate a background process by id (also defines `background_list`)
  - `fetch.py` — URL retrieval; main article extracted as Markdown (binary refused, output capped)
  - `read_pdf.py` — PDF text extraction (pdftotext / pymupdf / pdfplumber; `force_ocr=True` for scanned PDFs via tesseract)
- `skills/_universal/SKILL.md` — cross-benchmark working discipline (always-on)
- `systems/system.py` — minimal system prompt builder + context compaction

## What's deliberately excluded

- **Domain skills** (cryptanalysis, ml-inference, etc.) — TB2-specific, would
  contaminate other benchmarks
- **Web search tool** — GAIA needs it, but TB3 prohibits task-specific search;
  GAIA gets it from its adapter instead. `fetch` is included for reading
  general documentation, but `_universal` skill explicitly prohibits using it
  to search for task-specific solutions.
- **Benchmark-specific prompt sections** — no container-isolation mentions,
  no multi-turn-user instructions; those come from the benchmark adapter/framework

## How each benchmark uses this workspace

| Benchmark | Tools used from this workspace | Additional tools from adapter |
|-----------|-------------------------------|-------------------------------|
| TB 2.1 | bash, read, write, edit, search, list_dir, background_start/stop | none |
| TB 3.0 | bash, read, write, edit, search, list_dir, background_start/stop | none (verifier runs separately) |
| tau2 | (mostly unused — agent converses via adapter) | tau2 domain API tools |
| GAIA | bash, read, write, edit, search, list_dir, fetch, read_pdf | web_search (from GAIA adapter) |

## Why these tools

| Tool | Why it's universal | Driven by |
|------|-------------------|-----------|
| bash | Fresh per-call shell execution (cwd/env/venv do not persist; chain with `&&`) | All TB tasks |
| read | Read file contents | All benchmarks |
| write | Create files / artifacts | TB 2.1/3.0, GAIA |
| edit | Precise string replacement | TB 2.1/3.0 (code modification) |
| search | Glob file finding (supports `**`) + regex content search | TB 2.1/3.0 (codebase exploration), GAIA |
| list_dir | Browse directory tree | TB 2.1/3.0 (environment exploration), GAIA |
| background_start | Long-running ML/compile/proof tasks (auto-captures output to log file) | TB 2.1 (caffe-cifar-10, llm-inference), TB 3.0 (vllm, gpt2-codegolf, takens-embedding) |
| background_stop | Terminate stuck processes | Companion to background_start |
| background_list | Inspect which background processes are alive | Companion to background_start |
| fetch | Read web documentation / API refs as Markdown | GAIA (research), TB (general docs) |
| read_pdf | Extract text from PDF files (incl. OCR fallback for scanned PDFs) | GAIA (file/multimodal tasks), TB (PDF docs) |

## Run

```bash
psi-agent ai --provider <name> --model <model> --api-key <key> --base-url <url> --session-socket /tmp/ai.sock
psi-agent session --workspace examples/benchmark-baseline-workspace --ai-socket /tmp/ai.sock --channel-socket /tmp/ch.sock
psi-agent channel repl --session-socket /tmp/ch.sock
```
