# PR #4 — Review Summary (Pendências não implementadas)

Este relatório consolida apenas o que permaneceu pendente após as rodadas de review e ajustes aplicados.

## Escopo já aplicado no PR #4

- URLs corrigidas em `pyproject.toml` e `mkdocs.yml` para `brain-model`.
- Hardening de supply-chain: actions fixadas por SHA em `pr-validation.yml`, `ci.yml` e `release.yml` (inclui Codecov e upload-artifact).
- Pipeline de release: padronização de `python -m pip install` no smoke.
- PR Validation fortalecido: fetch base antes do diff, Bandit único com JSON e artifact.

## Pendências (ainda não implementadas)

- [P1] Cobertura unitária adicional do validador
  - Ações: ampliar casos para `manifestVersion` ausente/semver inválido/major <1 e >=2, confirmando mensagens determinísticas.
  - Aceite: cobertura de `core/application/validation.py` ≥ 90% e mensagens estáveis.
- [P2] Evolução da heurística de extração JSON (LLM)
  - Ações: avaliar fenced JSON ```json
    { ... }
    ``` ou sentinelas; adaptar `_extract_json_from_content` ou documentar guidelines de prompt.
  - Aceite: testes para JSON misto/saídas irregulares.
- [P2] Consistência de idioma (PT/EN)
  - Ações: alinhar headings/exemplos e definir guia de estilo mínimo.
- [P2] Robustez do secret scan (advisory)
  - Ações: considerar gitleaks ou regexes mais estritos, mantendo check não-bloqueante.
- [P2] Cache do ambiente (CI)
  - Ações: avaliar cache para `setup-python`/`setup-uv` sem afetar reprodutibilidade.

## Observações

- O `BACKLOG.md` foi atualizado para conter apenas os itens acima.
- Qualquer nova pendência identificada em revisão subsequente deve ser adicionada ao `BACKLOG.md` com prioridade e critérios de aceite claros.
