# Solução de Problemas

- Erro de timeout: aumente `--timeout` ou `HIPPO_ENGINE_TIMEOUT_S`.
- Rate limit do provedor: reduza a frequência, verifique limites no dashboard.
- Falha ao carregar PDF: verifique a instalação do `pypdf` (instalação completa inclui essa dependência). Reinstale o pacote ou execute `uv sync`.
- Para ajuda detalhada, rode `hippo --help`.
