# Backlog de Melhorias — PR #1 (feature/llm-multiprovider-config)

Contexto: consolidar as sugestões identificadas na revisão mais recente para execução incremental, com prioridades, dependências e critérios de aceite claros.

## Prioridades

- P0: Alta — consistência funcional/UX ou risco de regressão.
- P1: Média — robustez, manutenibilidade e cobertura.
- P2: Baixa — estilo, observabilidade e documentação.

## Itens

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

1. [P2] Observabilidade discreta no handler

   - Descrição: Adicionar `logger.debug` (ou equivalente) no início de `_handle_provider_errors` com `provider` e `type(e).__name__`, sem poluir a UX padrão.
   - Critérios de aceite:
     - Log nível DEBUG emitido com nome da exceção e provedor.
     - Nenhum `print`; mensagens ao usuário permanecem limpas.

1. [P2] Normalização de DOI

   - Descrição: Em `_normalize_reference_item`, normalizar o DOI antes de compor a URL: `doi = str(doi).strip()` e remoção de espaços internos.
   - Critérios de aceite:
     - `https://doi.org/{doi}` não contém espaços.
     - Testes cobrem DOIs com espaços ou quebras inadvertidas.

1. [P1] Reduzir duplicação de relatório no pipeline

   - Descrição: Centralizar a lógica de relatório entre `build_manifest_from_text` e `build_manifest_from_file` via `_render_report_and_end` para evitar divergências futuras.
   - Critérios de aceite:
     - Código consolidado; divergência de campos entre os caminhos eliminada.
     - Testes de ambos os caminhos passam com os mesmos campos no relatório.

1. [P1] Cobertura de pipeline (não-verbose/report)

   - Descrição: Adicionar testes para validar impressão do resumo no caminho não-verbose e cobertura do `_render_report_and_end` (texto/arquivo, heuristic/llm).
   - Critérios de aceite:
     - Testes de pipeline asseguram que o resumo e relatório aparecem nos fluxos suportados.
     - Linhas previamente descobertas como não cobertas em `pipeline.py` são reduzidas.

1. [P1] Testes de ConfigManager (segurança e precedência)

   - Descrição: Cobrir leitura/escrita, mascaramento de segredos, fallback seguro de keyring e precedência de `get_secret` (local→global→env).
   - Critérios de aceite:
     - Testes confirmam precedência esperada e ausência de vazamento de segredos.
     - Casos de erro (arquivo inválido, ausente) tratados com mensagens claras.

1. [P0] QA Gate pós-mudanças

## Progresso desta PR (atualização)

- [~] P1 — Reduzir duplicação de relatório no pipeline: `_render_report_and_end` já unifica e é usado tanto em texto quanto arquivo; validações adicionais de campos presentes nos dois fluxos permanecem como melhoria de teste.
- [ ] P2 — Observabilidade discreta no handler: ainda pendente adicionar `logger.debug` em `_handle_provider_errors`.
- [ ] P2 — Normalização de DOI: ainda pendente remover espaços internos ao compor URL de DOI.
- [ ] P1 — Cobertura de pipeline (não-verbose/report): adicionar testes específicos para cobertura das linhas faltantes em `pipeline.py`.
- [ ] P1 — Testes de ConfigManager: ampliar cobertura de precedência (local→global→env) e segurança.
 

## Sequenciamento sugerido

1. (P0) Itens 1 e 11 — consistência de relatório e QA gate.
1. (P1) Itens 6, 7 e 3 — eliminar duplicação, cobrir pipeline e robustez do handler.
1. (P2) Itens 4, 5, 9 e 10 — observabilidade, estilo e documentação/PR.
