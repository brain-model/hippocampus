# Uso Rápido

Extrair referências heurísticas de um arquivo Markdown:

```bash
hippo collect -f artigo.md --engine=heuristic --output ./out
```

Validar um manifesto existente:

```bash
hippo set --generate-template -o config.yaml
hippo collect -f artigo.md --config config.yaml --validate-only
```
