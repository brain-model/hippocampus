# Configuração

Crie um template de configuração:

```bash
hippo set --generate-template -o hippo.yaml
```

Defina chaves de API de provedores LLM com segurança:

```bash
hippo set --key OPENAI_API_KEY --value sk-...
```

Variáveis de ambiente suportadas:

- `HIPPO_OUTPUT_DIR`: diretório de saída padrão.
- `HIPPO_ENGINE_TIMEOUT_S`: timeout global em segundos.
- `HIPPO_TRACE`: habilita rastreamento detalhado.
