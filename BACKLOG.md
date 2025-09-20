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

1. [P1] Robustez no handler ao acessar `cfg.provider`

   - Descrição: Em `LangChainExtractionAgent.extract`, no `except`, proteger o acesso a `cfg.provider` para evitar `UnboundLocalError` se a falha ocorrer antes da inicialização de `cfg`.
   - Critérios de aceite:
     - Uso de `provider = getattr(locals().get("cfg"), "provider", None)` antes de `_handle_provider_errors`.
     - Teste que simula erro precoce confirma ausência de `UnboundLocalError` e caminho genérico de erro preservado.

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

1. [P2] Atualizar descrição do PR

   - Descrição: Aplicar corpo de `/tmp/pr-1-description.txt` via `gh pr edit 1 --body-file` e validar no PR.
   - Critérios de aceite:
     - PR atualizado com seções de Features, Fixes, Refactor e Notas.
     - Links/formatos renderizam corretamente na UI do GitHub.

1. [P2] Revisar README/CHANGELOG

   - Descrição: Ajustar README/CHANGELOG com as novidades (proveniência do engine, DeepSeek `base_url`, notas de segurança e exemplos de configuração).
   - Critérios de aceite:
     - Exemplos de uso atualizados; referência a variáveis de ambiente por provedor.
     - Seções de versionamento coerentes com 0.4.0.

1. [P0] QA Gate pós-mudanças

   - Descrição: Executar `make lint && make test`, assegurar cobertura ≥ 90% e checks do PR verdes.
   - Critérios de aceite:
     - Lint sem erros; testes verdes; cobertura ≥ 90%.
     - Comentário/resumo rápido no PR com as mudanças adicionais.

## Sequenciamento sugerido

1. (P0) Itens 1 e 11 — consistência de relatório e QA gate.
1. (P1) Itens 6, 7 e 3 — eliminar duplicação, cobrir pipeline e robustez do handler.
1. (P2) Itens 4, 5, 9 e 10 — observabilidade, estilo e documentação/PR.
