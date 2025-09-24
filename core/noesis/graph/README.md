# LangGraph/LLM — Orquestrador do Grafo (Fase 5)

Este módulo define um grafo mínimo (classify → extract → consolidate) para orquestrar a extração com LLM, reutilizando a configuração e provedores da Fase 4, com fallback heurístico opcional.

## Nós e Contratos

- Classify: recebe texto e produz `classifications: List[Classification]`.
- Extract: recebe texto + `classifications` e produz `extractions: List[Extraction]`.
- Consolidate: recebe `classifications` + `extractions` e gera `{ "references": [...], "metrics": { ... } }` compatível com `manifest.schema.json`.

Tipos em `types.py`:

- `Classification`: `{ kind, confidence, span? }`.
- `Extraction`: referência normalizada (campos `referenceType`, `rawString`, `sourceFormat`, `sourcePath`, `details`).
- `NodeResult`: envelope com `classifications`/`extractions` e `metrics`.
- `GraphConfig`: `enabled`, `use_fallback`, `timeout_s`, `retries`.

## Métricas

Cada nó preenche `metrics` com latência e uso de tokens (quando aplicável). O orquestrador agrega:

- `total_latency_ms`: soma das latências dos nós
- `total_tokens`: soma por chave (`prompt`, `completion`)
- `nodes`: métricas individuais (`classify`, `extract`, `consolidate`)

Exemplo:

```json
{
  "references": [ ... ],
  "metrics": {
    "total_latency_ms": 153,
    "total_tokens": { "prompt": 260, "completion": 71 },
    "nodes": {
      "classify": { "latency_ms": 2, "tokens": {"prompt":0,"completion":0} },
      "extract":  { "latency_ms": 150, "tokens": {"prompt":260,"completion":71} },
      "consolidate": { "latency_ms": 1, "tokens": {"prompt":0,"completion":0} }
    }
  }
}
```

## Flags

- Engine: `engine=llm-graph` (ou env `HIPPO_USE_LANGGRAPH=1`).
- Fallback: controlado por config/env.

## Aceite da Fase

- Orquestrador funcional com nós mínimos e contratos estáveis.
- Integração opt-in no pipeline/CLI.
- Testes unitários dos nós e teste e2e do grafo.

## Fluxo & Comportamento

Fluxo: `classify → extract → consolidate`.

- `classify`: heurística leve por URL (regex) e marcas básicas.
- `extract`: usa `LangChainExtractionAgent` quando habilitado (config Fase 4). Implementa retries (`retries + 1` tentativas). Em `TimeoutError`:
  - `use_fallback=True`: usa heurística; mantém execução.
  - `use_fallback=False`: propaga `TimeoutError`.
  Outras exceções seguem a mesma política de fallback.
- `consolidate`: normaliza para `knowledgeIndex.references` compatível com o schema.

## Exemplos Rápidos

Via pipeline/CLI (adaptador mantém UI de `llm`):

```bash
uv run hippo collect --engine llm-graph -t "See Fuster (2003) https://example.com"
uv run hippo collect --engine llm-graph -f ./document.txt --verbose
```
