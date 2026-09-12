# Local LLM

## Backend

Phase 1 implements one local backend: **Ollama**, via its HTTP API
(`research_os/models/local.py`, `OllamaAdapter`). llama.cpp and vLLM are
named in the spec as future backends behind the same `ProviderAdapter`
interface — not implemented yet, to avoid building against backends this
project hasn't validated a need for (spec section 61: don't overengineer).
Adding one later means writing one adapter class; nothing else changes.

## Why Ollama first, on this hardware

Target PC: Ryzen 5 8500G, RX 6600 8 GB VRAM, 16 GB RAM (see
`docs/environment.md`), no CUDA. Ollama runs on Windows, has the widest
model selection of the three named backends, and handles CPU fallback
automatically when a model doesn't fit in VRAM — important since 8 GB is
tight for anything beyond ~7-8B-parameter quantized models.

## Installing and checking

```powershell
# https://ollama.com/download
ollama --version
ollama pull qwen2.5:3b-instruct
ollama pull qwen2.5:7b-instruct
research-os models     # shows [available]/[unavailable] per tier
```

`OllamaAdapter.is_available()` just checks `GET /api/tags` with a 3s
timeout — it does not try to guess whether a specific model is pulled.
An unpulled model will fail at generate-time with `ModelUnavailableError`,
which the gateway treats the same as "Ollama not running": fall back to
the next tier.

## Model selection policy (spec section 9)

Do not assume a large model will run well on 8 GB VRAM. The intended
workflow is:

1. Pull one or two small candidates (Qwen2.5 3B/7B-instruct are the
   starting defaults in `config/models.yaml`; DeepSeek and Gemma are also
   worth trying).
2. Run `research-os evaluate` (`research_os/evaluation/lab.py`) to measure
   latency/output quality on the same fixed sample tasks used for cloud
   models.
3. Update `config/models.yaml` tiers based on what actually performs
   acceptably — never hardcode a model choice in Python.

## What happens with no local model at all

Every stage that would call a `local_*` tier fails over to its configured
cloud tier (`config/models.yaml` `fallback`), and if no cloud key is
configured either, every agent has a deterministic non-LLM fallback (see
`docs/architecture.md`). The pipeline was verified to run this way during
Phase 1 development, in an environment with neither Ollama nor a cloud key
available — see `docs/environment.md`.
