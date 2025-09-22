# Backlog de Melhorias — PRs #2 e #3

Contexto: consolidar as sugestões identificadas nas revisões de PRs para execução incremental, com prioridades, dependências e critérios de aceite claros.

## Prioridades

- P0: Alta — consistência funcional/UX ou risco de regressão.
- P1: Média — robustez, manutenibilidade e cobertura.
- P2: Baixa — estilo, observabilidade e documentação.

## Itens

1. [P2] Normalização de DOI

   - Descrição: ✅ **CONCLUÍDO no PR #3** — Em `_normalize_reference_item`, normalizar o DOI antes de compor a URL: `doi = str(doi).strip()` e remoção de espaços internos.
   - Critérios de aceite:

     - ✅ `https://doi.org/{doi}` não contém espaços.
     - ✅ Testes cobrem DOIs com espaços ou quebras inadvertidas.
     - ✅ README contém nota sobre normalização e exemplo.

1. [P2] Observabilidade discreta no handler

   - Descrição: Adicionar `logger.debug` (ou equivalente) no início de `_handle_provider_errors` com `provider` e `type(e).__name__`, sem poluir a UX padrão.
   - Critérios de aceite:

     - Log nível DEBUG emitido com nome da exceção e provedor (sem vazar segredos ou payloads).
     - Nenhum `print`; mensagens ao usuário permanecem limpas.

1. [P1] Cobertura unitária adicional no validador

   - Descrição: Reforçar testes em `tests/application/` para `core/application/validation.py` cobrindo casos edge e mensagens determinísticas.
   - Critérios de aceite:

     - Testes unitários diretos para `manifestVersion` ausente, formato inválido (não `x.y.z`), major < 1 e major >= 2.
     - Validar agregação determinística de mensagens (ordem estável) e localização `<root>` quando aplicável.
     - Cobertura do módulo `validation.py` >= 90%.

1. [P2] Heurística de extração JSON no agente LLM

   - Descrição: Documentar no README ou evoluir a heurística de `_extract_json_from_content` para ser mais robusta contra conteúdos irregulares.
   - Critérios de aceite:

     - README documenta limitações do fallback entre primeiro `{` e último `}`.
     - Alternativamente: implementar sentinelas no prompt ou exigir bloco fenced JSON (backlog futuro).
     - Testes cobrem cenários de JSON misto com texto extra.

1. [P2] Consistência de idioma (PT/EN)

   - Descrição: Padronizar idioma de mensagens do CLI/agent com as seções correspondentes do README (consistência PT/EN por contexto).
   - Critérios de aceite:

     - Headings e exemplos alinhados por seção.
     - Mensagens de erro do agente e CLI seguem o mesmo idioma da documentação correspondente.
     - Guia de estilo documentado para contribuições futuras.

1. [P0] Unificar relatório no pipeline de arquivo

   - Descrição: Em `build_manifest_from_file`, reutilizar `_render_report_and_end` e incluir métricas LLM (`provider`, `model`, `tokens`, `llm_latency_ms`) quando `engine="llm"`.
   - Critérios de aceite:

     - O caminho de arquivo chama `_render_report_and_end` (mesmo que texto).
     - Quando `engine=llm`, o relatório exibe `provider`, `model`, `tokens` (se disponíveis) e `llm_latency_ms`.
     - Testes validam a presença/consistência dos campos no relatório.

1. [P1] Sumário no modo verbose (texto)

   - Descrição: Em `build_manifest_from_text` (ramo verbose), emitir o sumário renderizado (ou remover a chamada morta a `render_template(_TPL_SUMMARY, ...)`).
   - Critérios de aceite:

     - O sumário é impresso no modo verbose (via `line(...)` ou `summary_panel(...)`).
     - Alternativamente, a chamada morta é removida; a decisão fica registrada no PR.
     - Teste de snapshot/saída cobre o comportamento escolhido.

1. [P2] Documentação de normalização de DOI

   - Descrição: ✅ **CONCLUÍDO no PR #3** — Adicionar seção curta no `README.md` explicando a normalização de DOI (remoção de espaços internos e `strip()`), com exemplo antes/depois.
   - Critérios de aceite:

     - ✅ Seção presente em `README.md` com exemplo prático.
     - ✅ Alinhado ao comportamento do `_normalize_reference_item`.

1. [P0] QA Gate pós-mudanças

## Progresso desta PR (atualização)

### PR #2 (LangGraph/LLM)

- [~] P1 — Reduzir duplicação de relatório no pipeline: `_render_report_and_end` já unifica texto e arquivo; faltam testes assegurando os mesmos campos (incluindo `llm-graph`).
- [ ] P2 — Observabilidade discreta no handler: ainda pendente adicionar `logger.debug` em `_handle_provider_errors` sem vazar segredos.

### PR #3 (Validação Robusta) — FINALIZADO ✅

- [x] P2 — Normalização de DOI: ✅ **CONCLUÍDO** — normalização implementada, testada e documentada no README.
- [x] P2 — Mensagens de ImportError: ✅ **CONCLUÍDO** — atualizadas para empacotamento atual em `langchain_agent.py`.
- [x] P1 — Provider validation: ✅ **CONCLUÍDO** — `_resolve_api_key` valida provider antes de acessar env_map.
- [x] P1 — ValueError handling: ✅ **CONCLUÍDO** — `_handle_provider_errors` propaga ValueError explicitamente.
- [x] P1 — Testes robustos: ✅ **CONCLUÍDO** — adicionados `test_validation_messages.py`, `test_doi_normalization.py`, `test_model_creation.py`.
- [~] P1 — Cobertura unitária adicional no validador: ✅ casos básicos cobertos; podem ser expandidos para edge cases específicos (majors <1 e >=2).
- [~] P2 — Heurística de extração JSON: ✅ documentada no README; evolução para sentinelas/fenced JSON fica para backlog futuro.
- [~] P2 — Consistência de idioma: ✅ README melhorado; padronização completa pode ser refinada.

### Novas Melhorias Incrementais (Revisão Final PR #3)

1. [P1] Cobertura edge cases manifestVersion

   - Descrição: Expandir testes unitários para casos específicos de `manifestVersion` com majors fora do range suportado.
   - Critérios de aceite:
     - Testes diretos para majors `<1` e `>=2` em `test_manifest_version.py`.
     - Validar mensagens de erro específicas para incompatibilidade.
     - Cobertura de `validation.py` >= 90%.

2. [P2] Evolução da heurística JSON

   - Descrição: Migrar extração JSON para fenced blocks ou sentinelas no prompt LLM como melhoria de robustez.
   - Critérios de aceite:
     - Implementar estratégia alternativa para `_extract_json_from_content`.
     - Testes cobrindo cenários de JSON misto com texto extra.
     - Documentar nova abordagem no README.

3. [P2] Logs DEBUG discretos

   - Descrição: Adicionar observabilidade discreta em `_handle_provider_errors` sem poluir UX.
   - Critérios de aceite:
     - `logger.debug` com provider e tipo de exceção (sem vazar segredos).
     - Configuração de logging nivel DEBUG para troubleshooting.
     - Mensagens ao usuário permanecem limpas.

### Pendências gerais

- [ ] P1 — Cobertura de pipeline (não-verbose/report): adicionar testes específicos (heuristic/llm/llm-graph) e validar métricas do grafo no relatório.
- [ ] P1 — Testes de ConfigManager: ampliar cobertura de precedência (local→global→env) e segurança.

## Sequenciamento sugerido

1. (P0) Itens 1 e 8 — consistência de relatório e QA gate.
1. (P1) Itens 6, 7 e 3 — eliminar duplicação, cobrir pipeline (incluindo llm-graph) e robustez do handler.
1. (P2) Itens 4, 5 e 9 — observabilidade, normalização/documentação.
