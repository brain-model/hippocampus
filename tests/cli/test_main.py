"""Testes para funcionalidades principais da CLI.

Inclui:
- Help principal (main --help)
- Error handling e comandos inválidos
- Exception propagation
- Dispatch de subcomandos
"""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import patch

import pytest

from core.cli.root import main

# === MAIN HELP FUNCTIONALITY ===


def test_cli_help_runs():
    """Testa main --help"""
    # `main --help` imprime help com Rich e retorna 0
    code = main(["--help"])  # type: ignore[arg-type]
    assert code == 0


def test_cli_no_args_shows_help():
    """Testa que sem argumentos mostra help"""
    code = main([])
    assert code == 0


def test_main_help_long_flag():
    """Testa variações do help flag"""
    code = main(["-h"])  # type: ignore[arg-type]
    assert code == 0


# === INVALID COMMANDS AND ERROR HANDLING ===


def test_cli_invalid_command():
    """Testa comando inválido (retorna 0 e mostra help)"""
    # O CLI retorna 0 e mostra o help para comando inválido
    code = main(["invalidcmd"])
    assert code == 0


def test_main_unknown_command_error_handling(monkeypatch):
    """Testa tratamento de comando desconhecido (exibe help e retorna 0)"""
    # Redirecionar stdout para capturar saída
    captured_stdout = StringIO()

    with (
        patch.object(sys, "stdout", captured_stdout),
        patch.object(sys, "argv", ["hippo", "unknown_command"]),
    ):
        result = main()

    # Comando desconhecido mostra help e retorna 0 (não é tratado como erro)
    assert result == 0

    # Verificar que o help foi exibido
    captured_output = captured_stdout.getvalue()
    assert "Hippocampus — Help" in captured_output
    assert "Commands: collect, set" in captured_output


def test_main_exception_handling(monkeypatch):
    """Testa que exceções nos subcomandos propagam normalmente"""

    # Mock que sempre lança exceção
    def mock_cmd_collect(*args, **kwargs):
        raise RuntimeError("Unexpected error")

    with (
        patch.object(sys, "argv", ["hippo", "collect", "test"]),
        patch("core.cli.root._cmd_collect", mock_cmd_collect),
    ):
        # Exceções devem propagar normalmente (não há tratamento global)
        with pytest.raises(RuntimeError, match="Unexpected error"):
            main()


# === SUBCOMMAND DISPATCH ===


def test_main_collect_dispatch():
    """Testa que 'collect' é despachado corretamente"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        code = main(["collect", "--help"])
        assert code == 0
        mock_collect.assert_called_once_with(["--help"])


def test_main_set_dispatch():
    """Testa que 'set' é despachado corretamente"""
    with patch("core.cli.root._cmd_set") as mock_set:
        mock_set.return_value = 0

        code = main(["set", "--help"])
        assert code == 0
        mock_set.assert_called_once_with(["--help"])


# === LEGACY COMPATIBILITY ===


def test_main_legacy_flags_dispatch_to_collect():
    """Testa que flags legacy são despachados para collect"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        # -t flag should be treated as collect
        code = main(["-t", "test text"])
        assert code == 0
        mock_collect.assert_called_once_with(["-t", "test text"])


def test_main_legacy_file_flag_dispatch():
    """Testa que -f flag é despachado para collect"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        # -f flag should be treated as collect
        code = main(["-f", "test.txt"])
        assert code == 0
        mock_collect.assert_called_once_with(["-f", "test.txt"])


# === HELP MIXED WITH SUBCOMMANDS ===


def test_main_help_with_subcommand():
    """Testa help misturado com subcomando"""
    # Se há -h em qualquer lugar, deve mostrar main help
    code = main(["collect", "-h", "some", "args"])
    assert code == 0


def test_main_help_flag_precedence():
    """Testa precedência do help flag"""
    # Help flag deve ter precedência sobre outros argumentos
    code = main(["invalid", "--help", "more", "args"])
    assert code == 0


# === ERROR CASES FROM SUBCOMMANDS ===


def test_collect_error_propagation():
    """Testa que erros do collect são propagados"""
    # Missing required args should cause SystemExit
    with pytest.raises(SystemExit):
        main(["collect"])  # No -t or -f provided


def test_set_error_propagation():
    """Testa que erros do set são propagados"""
    code = main(["set"])  # No arguments
    assert code == 1  # set returns 1 for missing args


# === COMPREHENSIVE DISPATCH TESTING ===


def test_main_argv_none_uses_sys_argv():
    """Testa que argv=None usa sys.argv"""
    original_argv = sys.argv
    try:
        sys.argv = ["hippo", "--help"]
        code = main(None)
        assert code == 0
    finally:
        sys.argv = original_argv


def test_main_empty_argv_list():
    """Testa que lista vazia mostra help"""
    code = main([])
    assert code == 0


def test_main_whitespace_handling():
    """Testa handling de argumentos com espaços"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        code = main(["-t", "text with spaces"])
        mock_collect.assert_called_once_with(["-t", "text with spaces"])
        assert code == 0


# === INTEGRATION WITH SUBCOMMAND LOGIC ===


def test_main_preserves_subcommand_return_codes():
    """Testa que códigos de retorno dos subcomandos são preservados"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 42  # Custom return code

        code = main(["collect", "-t", "test"])
        assert code == 42


def test_main_handles_subcommand_exceptions():
    """Testa handling de exceções dos subcomandos"""
    with patch("core.cli.root._cmd_set") as mock_set:
        mock_set.side_effect = ValueError("Custom error")

        with pytest.raises(ValueError, match="Custom error"):
            main(["set", "key=value"])


# === ARGUMENT PROCESSING EDGE CASES ===


def test_main_single_dash_argument():
    """Testa argumento com dash único"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        code = main(["-t", "-"])  # - as text input
        mock_collect.assert_called_once_with(["-t", "-"])
        assert code == 0


def test_main_double_dash_handling():
    """Testa handling de argumentos após --"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        code = main(["-t", "test", "--", "extra", "args"])
        # Should pass all args to collect
        mock_collect.assert_called_once_with(["-t", "test", "--", "extra", "args"])
        assert code == 0


def test_main_multiple_help_flags():
    """Testa múltiplos help flags"""
    code = main(["-h", "--help", "-h"])
    assert code == 0  # Should still work


# === COMMAND LINE INTERFACE ROBUSTNESS ===


def test_main_case_sensitive_commands():
    """Testa que comandos são case-sensitive"""
    # 'Collect' != 'collect', mas devido à backward compatibility com -t,
    # ainda é interpretado como collect command
    with pytest.raises(
        SystemExit
    ):  # argparse rejeita 'Collect' como argumento inválido
        main(["Collect", "-t", "test"])


def test_main_partial_command_matching():
    """Testa que não há partial matching de comandos"""
    # 'col' should not match 'collect', mas devido à backward compatibility com -t,
    # ainda é interpretado como collect command
    with pytest.raises(SystemExit):  # argparse rejeita 'col' como argumento inválido
        main(["col", "-t", "test"])


def test_main_special_characters_in_args():
    """Testa caracteres especiais nos argumentos"""
    with patch("core.cli.root._cmd_collect") as mock_collect:
        mock_collect.return_value = 0

        # Test various special characters
        special_text = "Text with special chars: !@#$%^&*(){}[]|\\:;\"'<>?,./"
        code = main(["-t", special_text])
        mock_collect.assert_called_once_with(["-t", special_text])
        assert code == 0
