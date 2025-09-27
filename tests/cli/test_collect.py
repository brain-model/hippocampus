"""Testes completos para o subcomando 'collect' da CLI.

Consolida todos os testes relacionados ao comando collect:
- Flags básicos (-t, -f, -o)
- Engine flags (--engine, --provider, --model, etc)
- Variantes legacy vs subcommand
- Processamento de arquivos e texto
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.cli.root import main
from core.infrastructure.config.manager import ConfigManager

# === BASIC COLLECT FUNCTIONALITY ===


def test_cli_text_success(tmp_path: Path):
    """Testa collect com input de texto (-t flag)"""
    out_dir = tmp_path / "out"
    code = main(["-t", "See https://example.com", "-o", str(out_dir)])
    assert code == 0
    assert (out_dir / "manifest" / "manifest.json").exists()


def test_cli_file_success(tmp_path: Path, capsys):
    """Testa collect com input de arquivo (-f flag)"""
    p = tmp_path / "doc.md"
    p.write_text("# T\nsee [x](https://ex.com)", encoding="utf-8")
    code = main(["--file", str(p), "-o", str(tmp_path)])
    assert code == 0


def test_cli_missing_required_args():
    """Testa collect sem argumentos obrigatórios"""
    # argparse lança SystemExit(2) para argumentos obrigatórios faltando
    with pytest.raises(SystemExit) as e:
        main(["collect"])
    assert e.value.code == 2


def test_collect_help_flag():
    """Testa collect --help"""
    code = main(["collect", "--help"])
    assert code == 0


# === ENGINE FLAGS AND LLM OVERRIDES ===


def test_collect_engine_llm_overrides_pass(tmp_path: Path, monkeypatch):
    """Testa collect com engine LLM e todos os overrides"""
    # Avoid contacting real LLM by mocking extract
    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent.extract",
        lambda self, text: {"references": []},
    )
    # We don't assert inside pipeline here; just verify exit code and manifest
    out_dir = tmp_path / "out"
    code = main(
        [
            "collect",
            "--engine",
            "llm",
            "--provider",
            "openai",
            "--model",
            "gpt-4o-mini",
            "--temperature",
            "0.7",
            "--max-tokens",
            "1000",
            "--timeout-s",
            "30",
            "--retries",
            "3",
            "--verbose",
            "-t",
            "test text",
            "-o",
            str(out_dir),
        ]
    )
    assert code == 0
    assert (out_dir / "manifest" / "manifest.json").exists()


def test_collect_engine_heuristic_default(tmp_path: Path):
    """Testa que engine padrão é heuristic"""
    out_dir = tmp_path / "out"
    code = main(["collect", "-t", "Simple text", "-o", str(out_dir)])
    assert code == 0
    assert (out_dir / "manifest" / "manifest.json").exists()


# === LEGACY VS SUBCOMMAND VARIANTS ===


def _run(argv):
    """Helper para executar main e verificar código 0"""
    code = main(argv)  # type: ignore[arg-type]
    # em alguns caminhos antigos poderia ser SystemExit(0); aqui garantimos 0
    assert code == 0


@pytest.mark.parametrize("use_subcmd", [False, True])
def test_collect_legacy_and_subcommand_paths(
    tmp_path: Path, use_subcmd: bool, monkeypatch
):
    """Testa compatibilidade entre paths legacy e subcommand"""
    monkeypatch.chdir(tmp_path)
    # configura engine.provider sem chave -> não falha em modo heuristic
    c = ConfigManager(scope="local")
    c.set("engine.provider", "openai")

    # Legacy path: hippo -t "..." (sem subcmd explícito)
    # Subcommand path: hippo collect -t "..."
    args = ["-t", "simple text", "-o", str(tmp_path / "out1")]
    if use_subcmd:
        args = ["collect"] + args
    _run(args)


def test_collect_verbose_flag(tmp_path: Path):
    """Testa collect com flag --verbose"""
    out_dir = tmp_path / "out"
    code = main(
        ["collect", "--verbose", "-t", "Test with verbose output", "-o", str(out_dir)]
    )
    assert code == 0
    assert (out_dir / "manifest" / "manifest.json").exists()


def test_collect_different_file_types(tmp_path: Path):
    """Testa collect com diferentes tipos de arquivo"""
    # Test .txt file
    txt_file = tmp_path / "document.txt"
    txt_file.write_text("Plain text document", encoding="utf-8")

    out_dir = tmp_path / "out_txt"
    code = main(["collect", "-f", str(txt_file), "-o", str(out_dir)])
    assert code == 0
    assert (out_dir / "manifest" / "manifest.json").exists()

    # Test .md file
    md_file = tmp_path / "document.md"
    md_file.write_text("# Markdown\nWith [link](https://example.com)", encoding="utf-8")

    out_dir2 = tmp_path / "out_md"
    code = main(["collect", "-f", str(md_file), "-o", str(out_dir2)])
    assert code == 0
    assert (out_dir2 / "manifest" / "manifest.json").exists()


# === ERROR HANDLING ===


def test_collect_invalid_file_path(capsys):
    """Testa collect com arquivo inexistente"""
    # Arquivo inexistente deve executar mas retornar código de erro
    code = main(["collect", "-f", "/nonexistent/file.txt"])
    # Pipeline executa mas falha no load, retorna 3 (FILE_NOT_FOUND) e exibe erro
    assert code == 3  # ExitCode.FILE_NOT_FOUND
    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_collect_invalid_engine():
    """Testa collect com engine inválido"""
    # argparse deve rejeitar engine inválido
    with pytest.raises(SystemExit):
        main(["collect", "--engine", "invalid_engine", "-t", "test"])


def test_collect_temperature_out_of_range(tmp_path: Path, monkeypatch):
    """Testa collect com temperature extrema (deve funcionar mas ser processada)"""
    # Mock LLM para evitar chamadas reais
    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent.extract",
        lambda self, text: {"references": []},
    )

    out_dir = tmp_path / "out"
    # Temperature muito alta - deve funcionar (validação é no LLM agent)
    code = main(
        [
            "collect",
            "--engine",
            "llm",
            "--provider",
            "openai",
            "--temperature",
            "2.0",
            "-t",
            "test",
            "-o",
            str(out_dir),
        ]
    )
    assert code == 0


# === OUTPUT DIRECTORY TESTS ===


def test_collect_default_output_directory(tmp_path: Path, monkeypatch):
    """Testa que output padrão é ~/.brain-model/hippocampus/buffer/consolidation"""
    # isola HOME para tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))
    # não define -o para usar default
    code = main(["collect", "-t", "Test default output"])
    assert code == 0
    manifest_dir = (
        tmp_path
        / ".brain-model"
        / "hippocampus"
        / "buffer"
        / "consolidation"
        / "manifest"
    )
    assert manifest_dir.exists()
    files = list(manifest_dir.glob("manifest_*.json"))
    assert len(files) == 1


def test_collect_custom_output_directory(tmp_path: Path):
    """Testa output personalizado com -o"""
    custom_out = tmp_path / "my_custom_output"

    code = main(["collect", "-t", "Test custom output", "-o", str(custom_out)])
    assert code == 0
    assert (custom_out / "manifest" / "manifest.json").exists()


def test_collect_uses_env_output_dir_when_set(tmp_path: Path, monkeypatch):
    """Quando HIPPO_OUTPUT_DIR está setado e -o não é passado, usar env dir."""
    # Isola HOME e define HIPPO_OUTPUT_DIR para diretório custom
    monkeypatch.setenv("HOME", str(tmp_path))
    env_out = tmp_path / "env-out"
    monkeypatch.setenv("HIPPO_OUTPUT_DIR", str(env_out))

    code = main(["collect", "-t", "Using env output dir"])
    assert code == 0
    # Como é custom (não é o buffer default), deve ser manifest.json
    assert (env_out / "manifest" / "manifest.json").exists()


def test_collect_cli_output_overrides_env(tmp_path: Path, monkeypatch):
    """A flag -o deve ter precedência sobre HIPPO_OUTPUT_DIR."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HIPPO_OUTPUT_DIR", str(tmp_path / "env-out"))
    cli_out = tmp_path / "cli-out"

    code = main(["collect", "-t", "CLI overrides env", "-o", str(cli_out)])
    assert code == 0
    assert (cli_out / "manifest" / "manifest.json").exists()


# === COMPREHENSIVE ENGINE TESTING ===


def test_collect_all_llm_providers(tmp_path: Path, monkeypatch):
    """Testa collect com diferentes providers LLM"""
    # Mock all LLM providers
    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent.extract",
        lambda self, text: {"references": []},
    )

    providers = ["openai", "gemini", "claude", "deepseek"]

    for provider in providers:
        out_dir = tmp_path / f"out_{provider}"
        code = main(
            [
                "collect",
                "--engine",
                "llm",
                "--provider",
                provider,
                "-t",
                f"Test with {provider}",
                "-o",
                str(out_dir),
            ]
        )
        assert code == 0
        assert (out_dir / "manifest" / "manifest.json").exists()
