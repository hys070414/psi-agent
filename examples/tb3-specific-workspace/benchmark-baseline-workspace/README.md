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

- `tools/` — 10 universal tools:
  - `bash.py` — shell command execution (120s default timeout)
  - `read.py` — file reading with offset/limit
  - `write.py` — file creation/overwrite
  - `edit.py` — precise string replacement
  - `search.py` — file finding (glob) + content search (grep)
  - `list_dir.py` — directory browsing (flat or recursive)
  - `background_start.py` — launch detached long-running processes
  - `background_stop.py` — terminate a background process by id
  - `fetch.py` — URL retrieval as plain text (HTML stripped)
  - `read_pdf.py` — PDF text extraction (pdftotext / pymupdf / pdfplumber)
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

## Why these 10 tools

| Tool | Why it's universal | Driven by |
|------|-------------------|-----------|
| bash | Atomic shell execution | All TB tasks |
| read | Read file contents | All benchmarks |
| write | Create files / artifacts | TB 2.1/3.0, GAIA |
| edit | Precise string replacement | TB 2.1/3.0 (code modification) |
| search | Find files + grep contents | TB 2.1/3.0 (codebase exploration), GAIA |
| list_dir | Browse directory tree | TB 2.1/3.0 (environment exploration), GAIA |
| background_start | Long-running ML/compile/proof tasks | TB 2.1 (caffe-cifar-10, llm-inference), TB 3.0 (vllm, gpt2-codegolf, takens-embedding) |
| background_stop | Terminate stuck processes | Companion to background_start |
| fetch | Read web documentation / API refs | GAIA (research), TB (general docs) |
| read_pdf | Extract text from PDF files | GAIA (file/multimodal tasks), TB (PDF docs) |

## Run

```bash
psi-agent ai --provider <name> --model <model> --api-key <key> --base-url <url> --session-socket /tmp/ai.sock
psi-agent session --workspace examples/benchmark-baseline-workspace --ai-socket /tmp/ai.sock --channel-socket /tmp/ch.sock
psi-agent channel repl --session-socket /tmp/ch.sock
```
