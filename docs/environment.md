# Environment (Phase 0)

This project targets two different machines, and it's important to keep
them separate:

1. **The user's actual PC** — where this system is meant to run day to day.
2. **This cloud build/dev container** — where Claude Code on the web built
   and tested Phase 1. It has no GPU and no Ollama, and its network egress
   is restricted by organization policy (see below). It is *not* the
   target runtime.

## 1. Target hardware (user's PC)

| Component | Spec |
|---|---|
| CPU | AMD Ryzen 5 8500G (6 cores / 12 threads) |
| RAM | 16 GB DDR5-5200 (32 GB upgrade planned) |
| GPU | AMD Radeon RX 6600, 8 GB VRAM |
| iGPU | AMD Radeon 740M |
| Storage | NVMe SSD + SATA HDD |
| OS | Windows 11 |

Implications for the design (see also `docs/local-llm.md`):

- **No CUDA.** The RX 6600 is an AMD card; local inference should go
  through Ollama (which supports ROCm on some AMD GPUs) or fall back to
  CPU. The system never assumes CUDA is present.
- **8 GB VRAM / 16 GB RAM** rules out large local models at first. Start
  with small instruction-tuned models (3B-8B class: Qwen2.5, DeepSeek,
  Gemma) and only grow after running the LLM Evaluation Lab
  (`research-os evaluate`) to see what's actually usable.
- Because local capacity is limited, the **cloud fallback path is not
  optional polish — it's load-bearing** for anything beyond fast/cheap
  tasks (spec section 13).

What to check on that PC before relying on local inference:

```powershell
python --version
git --version
gh --version          # optional
docker --version      # optional, not required by Phase 1
ollama --version       # optional; if missing, install from ollama.com
node --version         # optional, not required by this Python project
```

Then, once Ollama is installed:

```powershell
ollama pull qwen2.5:3b-instruct
ollama pull qwen2.5:7b-instruct
research-os models     # shows which tiers are actually reachable
research-os evaluate   # benchmarks whatever is reachable
```

Nothing is installed automatically by this project — the build spec is
explicit that we do not install developer tools speculatively. Install
Ollama and pull models only once you've decided local inference is worth
it for your workflow.

## 2. This build/dev container (what Claude Code on the web actually used)

Captured during Phase 0 of this build:

| Component | Value |
|---|---|
| OS | Linux (container), kernel reported as `Linux 6.18.44-fc-v24` |
| Python | 3.11.15 |
| git | 2.43.0 |
| CPU | 4 logical cores (container limit, not representative of the target PC) |
| RAM | ~15.7 GB available to the container |
| GPU | none (no `nvidia-smi`/`rocm-smi`) |
| Ollama | not installed |
| Docker | present (`/usr/bin/docker`), unused by this project |
| Node.js | present (`/opt/node22`), unused by this project (Python-only stack) |

### Network egress is restricted here

Outbound HTTPS in this container goes through an organization-managed
egress proxy. During Phase 1 development, direct requests to
`export.arxiv.org` (both the arXiv collector's `httpx` calls and the
`WebFetch` tool) were blocked by that proxy policy:

```
CONNECT tunnel failed, response 403
EGRESS_BLOCKED: Access to export.arxiv.org is blocked by the network egress proxy.
```

This is a policy restriction on *this build container*, not a bug in the
collector, and it will not apply on the user's own PC (or most normal
network environments). To still verify the full pipeline end-to-end without
that access, Phase 1 testing used a tiny local HTTP server that serves a
real arXiv Atom API response (genuine, well-known public paper metadata:
arXiv:1706.03762 "Attention Is All You Need" and arXiv:2010.11929 "An Image
is Worth 16x16 Words") on `127.0.0.1`, and pointed the collector at it via
the `ARXIV_BASE_URL` environment variable (see `config/system.yaml`, which
reads `sources.arxiv.base_url` as `${ARXIV_BASE_URL:-http://export.arxiv.org/api/query}`).
That confirmed: parsing, normalization, deduplication, classification,
summarization, scoring, battery-relevance, transfer analysis, and storage
all work against a real arXiv-shaped feed. On the user's PC, simply running
`research-os collect --source arxiv` with no environment override will hit
the real API.

### No local or cloud LLM configured in this container

Neither Ollama nor `ANTHROPIC_API_KEY` was available while building here.
This turned out to be a useful test: it forced every agent's
LLM-unavailable fallback path (spec section 13/44) to run for real, and the
Phase 1 pipeline completed successfully end-to-end using only the
rule-based/heuristic fallbacks — see `research-os status` and the sample
reports in `data/reports/` generated during this build. On a machine with
Ollama running and/or `ANTHROPIC_API_KEY` set, the same commands will
transparently use the LLM path instead.

### Re-confirmed during the Local LLM Benchmark work

A later session in this same kind of container re-checked reachability
before building the local-LLM benchmark kit (`docs/local-llm.md`):
`ollama.com` is blocked by the same egress policy (`EGRESS_BLOCKED` from
`WebFetch`), `export.arxiv.org` is still blocked, and there is still no
`ollama`/`nvidia-smi`/`rocm-smi` binary in the container. Because actually
running Ollama and benchmarking real models requires the target Windows
PC's hardware, that session built and unit-tested the benchmark
tooling (dataset, prompts, scoring, resource probing, report generation)
here with a mocked Ollama backend, and left running it for real —
`research-os evaluate` then `research-os benchmark-apply` — as the next
step on the actual PC. See `docs/local-llm.md` for the full breakdown of
what was verified here versus what is still pending real hardware.
