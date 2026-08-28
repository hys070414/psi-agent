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

- `tools/` — 5 universal tools:
  - `bash.py` — shell command execution (120s default timeout)
  - `read.py` — file reading with offset/limit
  - `write.py` — file creation/overwrite
  - `edit.py` — precise string replacement
  - `search.py` — file finding (glob) + content search (grep)
- `skills/_universal/SKILL.md` — cross-benchmark working discipline (always-on)
- `systems/system.py` — minimal system prompt builder + context compaction

## What's deliberately excluded

- **Domain skills** (cryptanalysis, ml-inference, etc.) — TB2-specific, would
  contaminate other benchmarks
- **Web search tool** — GAIA needs it, but TB3 prohibits task-specific search;
  GAIA gets it from its adapter instead
- **Benchmark-specific prompt sections** — no container-isolation mentions,
  no multi-turn-user instructions; those come from the benchmark adapter/framework

## How each benchmark uses this workspace

| Benchmark | Tools used from this workspace | Additional tools from adapter |
|-----------|-------------------------------|-------------------------------|
| TB 2.1 | bash, read, write, edit, search | none |
| TB 3.0 | bash, read, write, edit, search | none (verifier runs separately) |
| tau2 | (unused — agent converses via adapter) | tau2 domain API tools |
| GAIA | bash, read, write, search | web_search (from GAIA adapter) |

## Run

```bash
psi-agent ai --provider <name> --model <model> --api-key <key> --base-url <url> --session-socket /tmp/ai.sock
psi-agent session --workspace examples/benchmark-baseline-workspace --ai-socket /tmp/ai.sock --channel-socket /tmp/ch.sock
psi-agent channel repl --session-socket /tmp/ch.sock
```
