# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Added (Unreleased)

- Planning for Phase 4: LLM multi-provider (OpenAI, Gemini, Claude, DeepSeek), config manager with `hippocampus set`, YAML apply, CLI templates with emojis.

## [0.3.0] - 2025-09-18

### Added (0.3.0)

- Multi-format loaders: Markdown, LaTeX, PDF (via `pypdf`).
- Loader registry with automatic selection by file extension.
- File-based pipeline `build_manifest_from_file` and CLI `--file` option.
- Tests for loaders/registry/CLI with coverage ≥ 90% (subsequently improved to 100% for loaders).

### Changed (0.3.0)

- Simplified PDF loader to assume `pypdf` available; removed optional dependency checks.
- Updated `TODO.md` marking Phase 3 as complete; inserted Phase 4 planning.

## [0.2.0] - 2025-09-17

### Added (0.2.0)

- MVP text pipeline: `build_manifest_from_text`, heuristic extractor, JSON writer.
- CLI `--text` with output directory handling and `--verbose` error reporting.
- JSON Schema validation (Draft-07) using centralized `MANIFEST_SCHEMA_PATH`.
- Module and function docstrings across the codebase.

### Changed (0.2.0)

- Resources reorganized under `core/resources/{prompts,templates,schemas}`.
- Makefile targets for format, lint, and tests; coverage gate ≥ 90%.

## [0.1.0] - 2025-09-16

### Added (0.1.0)

- Initial scaffold with Clean Architecture under `core/`.
- Domain contracts and manifest types.
- Packaging via `pyproject.toml` with console script `hippocampus`.
- Initial tests and CI setup groundwork.

[Unreleased]: https://example.com/compare/0.3.0...HEAD
[0.3.0]: https://example.com/compare/0.2.0...0.3.0
[0.2.0]: https://example.com/compare/0.1.0...0.2.0
