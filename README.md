# Hippocampus

Knowledge acquisition pipelines with Clean Architecture.

- Source: `core/`
- Resources: `core/resources/prompts`, `core/resources/templates`
- Schemas: `core/resources/schemas/manifest.schema.json`
- CLI: `hippo` (or `hippocampus` for compatibility)

## Install & Setup

```bash
make setup
uv sync
```

## CLI Overview

```bash
uv run hippo -h
```

Subcommands:

- `collect`: Build a manifest from text or file
- `set`: Configure Hippocampus (local/global scopes)

Legacy usage without subcommands (e.g., `hippo -f ...`) is still supported and internally routed to `collect`.

## Collect

Run collection from text or file:

```bash
uv run hippo collect -h
uv run hippo collect -t "See Fuster (2003). https://doi.org/10.1126/science.1893226" -o ./hippo-out
uv run hippo collect -f document.pdf -o ./hippo-out
cat ./hippo-out/manifest/manifest.json
```

LLM engine usage:

```bash
# Provide secrets via keyring (preferred)
uv run hippo set api.openai.key='sk-...'
uv run hippo set api.gemini.key='...'       # or export GOOGLE_API_KEY
uv run hippo set api.claude.key='...'       # or export ANTHROPIC_API_KEY
uv run hippo set api.deepseek.key='...'     # or export DEEPSEEK_API_KEY

# Run with LLM engine (examples)
uv run hippo collect --engine llm --provider openai  --model gpt-4o-mini       -t "Fuster 2003" -o ./hippo-out
uv run hippo collect --engine llm --provider gemini  --model gemini-1.5-flash  -t "Fuster 2003" -o ./hippo-out
uv run hippo collect --engine llm --provider claude  --model claude-3-5-sonnet -t "Fuster 2003" -o ./hippo-out
uv run hippo collect --engine llm --provider deepseek --model deepseek-chat     -t "Fuster 2003" -o ./hippo-out \
  --base-url https://api.deepseek.com/v1
```

Engine flags (overrides):

```text
--engine {heuristic,llm}   Select engine (default: heuristic)
--provider NAME            LLM provider: openai|gemini|claude|deepseek
--model NAME               LLM model name (e.g., gpt-4o-mini)
--temperature FLOAT        Sampling temperature
--max-tokens INT           Max output tokens
--timeout-s INT            Request timeout in seconds
--base-url URL             Base URL (OpenAI-compatible providers)
--retries INT              Retry attempts for LLM calls
```

### LangGraph engine (experimental)

The graph orchestrator runs a minimal flow (classify → extract → consolidate) that can be enabled via `--engine llm-graph`. It reuses the LLM configuration (provider/model/etc.) and falls back to heuristics when exceptions occur.

Enable and run:

```bash
# Use the graph-backed extractor (UI shows mode=llm)
uv run hippo collect --engine llm-graph -t "See Fuster (2003) https://example.com" -o ./hippo-out

# Verbose mode displays phases and aggregated timings
uv run hippo collect --engine llm-graph -f ./document.txt -o ./hippo-out --verbose
```

Notes:

- In this mode, the pipeline uses an adapter that calls `GraphOrchestrator`, while preserving the CLI output/report.
- The final report includes provider/model and tokens when the underlying LLM path runs; heuristics are used as safe fallback.
- Metrics are aggregated by the graph and surfaced as `total_latency_ms` and `total_tokens` internally.

### Config provenance (verbose)

In verbose mode, the CLI shows where each engine parameter came from:

```text
begin=llm | source=text | format=text
engine: model(cli)=gemini-1.5-flash, provider(cli)=gemini, temperature(local)=0.2, max_tokens(local)=128, timeout_s(local)=60
```

Format: `key(source)=value` where `source` is one of `cli`, `local`, `global`, or `default`.

### LLM metrics

When using `--engine llm` (or `llm-graph`), the report displays provider/model and token usage; latency may also be shown when available:

```text
📊 Collect Report
• Mode: llm
• URLs: 0 | Citations: 1 | Total: 1
• Time: 10309 ms
• Manifest: <id>
• Processed: <timestamp>
• Engine: gemini/gemini-1.5-flash
• Tokens: prompt=260, completion=71
• LLM Latency: 10281 ms
```

### Prompts & Templates

Prompts are versioned under `core/resources/prompts/`:

- `extract_references_en.md`
- `classify_reference_type_en.md`
- `consolidate_manifest_en.md`

Templates used by the CLI live under `core/resources/templates/`.

### Engine Flags (Graph)

Exemplo com grafo e flags específicas:

```bash
uv run hippo collect --engine llm-graph -t "See Fuster (2003)" -o ./hippo-out \
  --graph-timeout 60 --graph-retries 2 \
  --graph-backoff-base 0.1 --graph-backoff-max 2.0 --graph-jitter 0.05
```

### Graph Config (flags/env)

The graph path supports basic configuration via environment variables (defaults shown):

- `HIPPO_GRAPH_FALLBACK=1` controls heuristic fallback on errors/timeouts (1/0)
- `HIPPO_GRAPH_TIMEOUT_S=60` per-node timeout (seconds)
- `HIPPO_GRAPH_RETRIES=0` number of retry attempts (integer)
- `HIPPO_GRAPH_BACKOFF_BASE_S=0.1`, `HIPPO_GRAPH_BACKOFF_MAX_S=2.0`, `HIPPO_GRAPH_JITTER_S=0.05`

Note: quando `--engine llm-graph` é usado, overrides do engine no CLI (`--provider`, `--model`, `--base-url`, etc.) são respeitados pelo extrator LLM subjacente. O relatório final exibe provider/model do passo LLM quando aplicável e mostra "Graph Total"/"Graph Tokens" como métricas agregadas.

Retry/backoff: ambos os caminhos (LLM direto e grafo) utilizam política centralizada de retries com backoff exponencial e jitter por padrão.

Make targets:

```bash
make run ARGS='collect -t "See ..." -o ./hippo-out'   # uses python -m core.cli.root
make hippo ARGS='collect -t "See ..." -o ./hippo-out' # uses hippo command (via uv)
make hippo-install                                     # install CLI globally (~/.local/bin)
```

## Configuration (Config Manager)

Generate a YAML template and apply settings (including secrets):

```bash
uv run hippo set --generate-template -o hippo.yaml
uv run hippo set --file hippo.yaml                # merge by default
uv run hippo set --file hippo.yaml --reset        # replace entirely
uv run hippo set engine.model=gpt-4o-mini         # single entry
uv run hippo set api.openai.key=sk-...            # secret (masked in output)
```

Template (`config_apply.yaml.j2`):

```yaml
# Hippocampus configuration (sample)
engine:
    provider: openai  # openai | gemini | claude | deepseek
    model: gpt-4o-mini
    temperature: 0.2
    max_tokens: 2048
    timeout_s: 60
    # base_url: https://api.deepseek.com/v1  # only for OpenAI-compatible providers

api:
    openai:
        key: ""
    gemini:
        key: ""
    claude:
        key: ""
    deepseek:
        key: ""
```

Supported Keys:

- Engine:
  - `engine.provider`
  - `engine.model`
  - `engine.temperature`
  - `engine.max_tokens`
  - `engine.timeout_s`
  - `engine.base_url`
  - `engine.retries`
- Secrets:
  - `api.openai.key`
  - `api.gemini.key`
  - `api.claude.key`
  - `api.deepseek.key`

Secrets storage:

- Prefer system keyring (service: `hippocampus`, user: `<provider>.api_key:<scope>`)
- Fallback: secured JSON (chmod 600) in chosen scope
  - Local: `./.hippo/config.json`
  - Global: `${XDG_CONFIG_HOME:-~/.config}/hippocampus/config.json`

How to read in code:

```python
from core.infrastructure.config.manager import ConfigManager

def get_secret_anyscope(provider: str):
        for scope in ("local", "global"):
                val = ConfigManager(scope).get_secret(provider)
                if val:
                        return val
        return None

api_key = get_secret_anyscope("openai")
```

DeepSeek (OpenAI‑compatible):

- Set `engine.provider: deepseek`, `engine.base_url: https://api.deepseek.com/v1`, and `api.deepseek.key` (in keyring/fallback).
- The client will be initialized as OpenAI‑compatible using `base_url` when LLM integration is wired into the CLI pipeline (Phase 4/6).

### Config precedence

- Engine parameters: CLI overrides > local config > global config. Defaults are applied when missing.
- Secrets (API keys): keyring lookup (local → global) > environment variables. Use `hippo set api.<provider>.key=...` to store in keyring.

### Security notes

- Do not commit plaintext keys to source control or dotfiles. Prefer keyring via `hippo set`.
- If you have exposed a key in logs or files (e.g., environment file), rotate it immediately in the provider console.
- Fallback JSON secret storage uses strict permissions and is scoped (local/global). Keep backups secure.

## Local CI

```bash
make ci
```
