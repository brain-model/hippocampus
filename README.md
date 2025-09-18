# Hippocampus

Clean architecture for knowledge acquisition pipelines.

- Source code package: `core/`
- Resources: `resources/prompts`, `resources/templates`
- Schemas: `resources/schemas/manifest.schema.json`
- CLI entrypoint: `hippocampus` (ou via módulo `python -m core.cli.root`)

Commit 0 contains only non-Python artifacts to set up
project structure and packaging configuration.

Quickstart (MVP - text only):

```bash
make setup
uv run python -m core.cli.root --help
uv run python -m core.cli.root -t "See Fuster (2003). https://doi.org/10.1126/science.1893226" -o ./hippo-out
cat ./hippo-out/manifest/manifest.json
```

Alternatively, with Make target:

```bash
make run ARGS='-t "See Fuster (2003). https://doi.org/10.1126/science.1893226" -o ./hippo-out'
```

Sample output (`hippo-out/manifest/manifest.json`):

```json
{
    "manifestVersion": "1.0.0",
    "status": "Awaiting Consolidation",
    "sourceDocument": { "sourceType": "text", "sourceFormat": "text" },
    "knowledgeIndex": { "references": [ { "referenceType": "web_link" } ] },
    "manifestId": "...",
    "processedAt": "..."
}
```

CI locally:

```bash
make ci
```
