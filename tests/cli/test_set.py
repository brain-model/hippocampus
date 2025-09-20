"""Testes completos para o subcomando 'set' da CLI.

Consolida todos os testes relacionados ao comando set:
- Generate template (--generate-template)
- Apply YAML files (--file, --merge, --reset)
- Key-value pairs (key=value)
- Scopes (--local, --global)
- Help e UI detalhada
"""

from __future__ import annotations

from pathlib import Path
from core.cli.root import main


def _run_ok(argv):
    """Helper para executar main e verificar código 0"""
    code = main(argv)  # type: ignore[arg-type]
    assert code == 0


# === GENERATE TEMPLATE FUNCTIONALITY ===

def test_set_generate_template_stdout(monkeypatch, tmp_path: Path, capsys):
    """Testa generate template para stdout"""
    monkeypatch.chdir(tmp_path)
    code = main(["set", "--generate-template"])  # type: ignore[arg-type]
    assert code == 0
    out = capsys.readouterr().out
    assert "Hippocampus configuration (sample)" in out
    assert "engine:" in out


def test_set_generate_template_to_file(monkeypatch, tmp_path: Path, capsys):
    """Testa generate template para arquivo (-o)"""
    monkeypatch.chdir(tmp_path)
    out_file = tmp_path / "sample.yaml"
    code = main(["set", "--generate-template", "-o", str(out_file)])  # type: ignore[arg-type]
    assert code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Hippocampus configuration (sample)" in content
    msg = capsys.readouterr().out
    assert "local set: template=" in msg


# === YAML FILE APPLICATION ===

def test_set_file_apply_yaml_merge_and_reset(monkeypatch, tmp_path: Path):
    """Testa aplicação de YAML com merge e reset"""
    monkeypatch.chdir(tmp_path)
    cfg_yaml1 = tmp_path / "cfg1.yaml"
    cfg_yaml1.write_text(
        """
engine:
  model: gpt-4o-mini
api:
  openai:
    key: sk-test-123
""".strip(),
        encoding="utf-8",
    )
    # apply first
    assert main(["set", "--file", str(cfg_yaml1)]) == 0  # type: ignore[arg-type]

    # config file exists and contains engine.model (secret not present)
    cfg_path = tmp_path / ".hippo" / "config.json"
    data = cfg_path.read_text(encoding="utf-8")
    assert "gpt-4o-mini" in data
    assert "sk-test-123" not in data

    # test merge behavior
    cfg_yaml2 = tmp_path / "cfg2.yaml"
    cfg_yaml2.write_text("engine:\n  provider: openai\n", encoding="utf-8")
    assert main(["set", "--file", str(cfg_yaml2), "--merge"]) == 0  # type: ignore[arg-type]

    data_after_merge = cfg_path.read_text(encoding="utf-8")
    assert "gpt-4o-mini" in data_after_merge  # original model preserved
    assert "openai" in data_after_merge       # new provider added

    # test reset behavior
    assert main(["set", "--file", str(cfg_yaml2), "--reset"]) == 0  # type: ignore[arg-type]

    data_after_reset = cfg_path.read_text(encoding="utf-8")
    assert "gpt-4o-mini" not in data_after_reset  # original model removed
    assert "openai" in data_after_reset           # only new config


def test_set_generate_template_and_apply_reset_merge(tmp_path, monkeypatch):
    """Testa workflow completo: generate -> modify -> apply"""
    monkeypatch.chdir(tmp_path)
    # Gera template em arquivo
    out_yaml = tmp_path / "hippo.yaml"
    _run_ok(["set", "--generate-template", "-o", str(out_yaml)])
    assert out_yaml.exists() and out_yaml.read_text(encoding="utf-8")

    # Ajusta YAML mínimo válido e aplica com --reset (provider suportado)
    out_yaml.write_text("engine:\n  provider: openai\n", encoding="utf-8")
    _run_ok(["set", "--file", str(out_yaml), "--reset"])

    # Verifica que config foi aplicado
    cfg_path = tmp_path / ".hippo" / "config.json"
    assert cfg_path.exists()
    data = cfg_path.read_text(encoding="utf-8")
    assert "openai" in data


# === KEY-VALUE PAIR FUNCTIONALITY ===

def test_set_key_value_pairs(monkeypatch, tmp_path: Path):
    """Testa definição de chaves individuais (key=value)"""
    monkeypatch.chdir(tmp_path)

    # Set engine model
    code = main(["set", "engine.model=gpt-4o-mini"])  # type: ignore[arg-type]
    assert code == 0

    # Set engine provider
    code = main(["set", "engine.provider=openai"])  # type: ignore[arg-type]
    assert code == 0

    # Set temperature
    code = main(["set", "engine.temperature=0.7"])  # type: ignore[arg-type]
    assert code == 0

    # Verify all settings were applied
    cfg_path = tmp_path / ".hippo" / "config.json"
    data = cfg_path.read_text(encoding="utf-8")
    assert "gpt-4o-mini" in data
    assert "openai" in data
    assert "0.7" in data


def test_set_api_key_masking(monkeypatch, tmp_path: Path, capsys):
    """Testa que API keys são mascaradas na saída"""
    monkeypatch.chdir(tmp_path)

    code = main(["set", "api.openai.key=sk-secret123"])  # type: ignore[arg-type]
    assert code == 0

    # Verificar que a chave foi mascarada na saída
    output = capsys.readouterr().out
    assert "***" in output
    assert "sk-secret123" not in output
    assert "api.openai.key" in output


def test_set_invalid_key_format(tmp_path, capsys):
    """Testa chave sem formato key=value"""
    code = main(["set", "invalid_format"])  # type: ignore[arg-type]
    assert code == 1
    err = capsys.readouterr().err
    assert "entry must be in the form key=value" in err


# === SCOPE FUNCTIONALITY ===

def test_set_local_vs_global_scope(monkeypatch, tmp_path: Path):
    """Testa diferença entre scope local e global"""
    monkeypatch.chdir(tmp_path)

    # Set local scope (default)
    code = main(["set", "--local", "engine.model=gpt-4o-mini"])  # type: ignore[arg-type]
    assert code == 0
    local_cfg = tmp_path / ".hippo" / "config.json"
    assert local_cfg.exists()

    # Set global scope
    code = main(["set", "--global", "engine.provider=openai"])  # type: ignore[arg-type]
    assert code == 0
    # Global config goes to ~/.config/hippocampus/config.json
    # We can't easily test this without affecting user's actual global config


def test_set_template_with_different_scopes(monkeypatch, tmp_path: Path):
    """Testa generate template com scopes diferentes"""
    monkeypatch.chdir(tmp_path)

    # Generate local template
    local_template = tmp_path / "local.yaml"
    _run_ok(["set", "--local", "--generate-template", "-o", str(local_template)])
    assert local_template.exists()

    # Generate global template
    global_template = tmp_path / "global.yaml"
    _run_ok(["set", "--global", "--generate-template", "-o", str(global_template)])
    assert global_template.exists()

    # Both should have same content since it's just a template
    assert local_template.read_text() == global_template.read_text()


# === HELP AND UI FUNCTIONALITY ===

def test_set_command_help_flag(monkeypatch, capsys):
    """Testa comando set com flag -h"""
    from unittest.mock import patch
    from core.cli.root import _cmd_set

    with patch("core.cli.root._print_set_help_rich") as mock_help:
        result = _cmd_set(["-h"])

        mock_help.assert_called_once()
        assert result == 0


def test_set_command_help_long_flag(monkeypatch, capsys):
    """Testa comando set com flag --help"""
    from unittest.mock import patch
    from core.cli.root import _cmd_set

    with patch("core.cli.root._print_set_help_rich") as mock_help:
        result = _cmd_set(["--help"])

        mock_help.assert_called_once()
        assert result == 0


def test_print_set_help_rich_output(monkeypatch, capsys):
    """Testa saída completa da função _print_set_help_rich"""
    from unittest.mock import patch
    from core.cli.root import _print_set_help_rich

    # Mock das funções de UI do rich
    with patch("core.cli.root.rule") as mock_rule, \
         patch("core.cli.root.summary_panel") as mock_panel:

        _print_set_help_rich()

        # Verificar que rule foi chamado com título correto
        mock_rule.assert_called_once_with("hippo set — Help")

        # Verificar que summary_panel foi chamado 4 vezes (Usage, Options, Keys, Examples)
        assert mock_panel.call_count == 4

        # Verificar conteúdo das chamadas
        calls = mock_panel.call_args_list

        # Primeira chamada: Usage
        assert calls[0][0][0] == "Usage"
        assert "hippo set" in calls[0][0][1]

        # Segunda chamada: Options
        assert calls[1][0][0] == "Options"
        assert "--local" in calls[1][0][1]

        # Terceira chamada: Keys
        assert calls[2][0][0] == "Keys"
        assert "engine.provider" in calls[2][0][1]

        # Quarta chamada: Examples
        assert calls[3][0][0] == "Examples"
        assert "hippo set engine.model" in calls[3][0][1]
        assert "--generate-template" in calls[3][0][1]


def test_help_rich_formatting_content():
    """Testa conteúdo específico da formatação rich"""
    from unittest.mock import patch
    from core.cli.root import _print_set_help_rich

    with patch("core.cli.root.rule") as mock_rule, \
         patch("core.cli.root.summary_panel") as mock_panel:

        _print_set_help_rich()

        # Verificar formatação do título
        mock_rule.assert_called_once_with("hippo set — Help")

        # Obter todas as chamadas do summary_panel
        calls = mock_panel.call_args_list

        # Verificar estrutura detalhada de Usage
        usage_call = calls[0]
        assert usage_call[0][0] == "Usage"
        usage_text = usage_call[0][1]
        assert "hippo set [--local|--global]" in usage_text
        assert "[--generate-template|-o PATH|--file YAML" in usage_text
        assert "[--merge|--reset]]" in usage_text
        assert "hippo set key=value" in usage_text

        # Verificar estrutura de Examples
        examples_call = calls[3]  # Examples é a 4ª chamada (índice 3)
        assert examples_call[0][0] == "Examples"
        examples_text = examples_call[0][1]
        assert "hippo set engine.model=gpt-4o-mini" in examples_text
        assert "--generate-template" in examples_text


# === ERROR HANDLING ===

def test_set_no_arguments_error(capsys):
    """Testa set sem argumentos (deve falhar)"""
    code = main(["set"])  # type: ignore[arg-type]
    assert code == 1
    err = capsys.readouterr().err
    assert "Use --help" in err


def test_set_invalid_yaml_file(tmp_path, capsys):
    """Testa set com arquivo YAML inválido"""
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("invalid: yaml: content: [", encoding="utf-8")

    code = main(["set", "--file", str(invalid_yaml)])  # type: ignore[arg-type]
    assert code == 1


def test_set_nonexistent_yaml_file(capsys):
    """Testa set com arquivo inexistente"""
    code = main(["set", "--file", "/nonexistent/file.yaml"])  # type: ignore[arg-type]
    assert code == 1


# === INTEGRATION TESTS ===

def test_set_complete_workflow(monkeypatch, tmp_path: Path):
    """Testa workflow completo de configuração"""
    monkeypatch.chdir(tmp_path)

    # 1. Generate template
    template_file = tmp_path / "config.yaml"
    _run_ok(["set", "--generate-template", "-o", str(template_file)])

    # 2. Modify template
    template_file.write_text("""
engine:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
api:
  openai:
    key: sk-test123
""".strip(), encoding="utf-8")

    # 3. Apply configuration
    _run_ok(["set", "--file", str(template_file)])

    # 4. Override specific key
    _run_ok(["set", "engine.temperature=0.5"])

    # 5. Verify final state
    cfg_path = tmp_path / ".hippo" / "config.json"
    data = cfg_path.read_text(encoding="utf-8")
    assert "openai" in data
    assert "gpt-4o-mini" in data
    assert "0.5" in data  # overridden temperature


def test_set_all_supported_keys(monkeypatch, tmp_path: Path):
    """Testa definição de todas as chaves suportadas"""
    monkeypatch.chdir(tmp_path)

    # Engine keys
    _run_ok(["set", "engine.provider=openai"])
    _run_ok(["set", "engine.model=gpt-4o-mini"])
    _run_ok(["set", "engine.temperature=0.7"])
    _run_ok(["set", "engine.max_tokens=1000"])
    _run_ok(["set", "engine.timeout_s=30"])
    _run_ok(["set", "engine.base_url=https://api.openai.com/v1"])
    _run_ok(["set", "engine.retries=3"])

    # API keys (should all work without error)
    _run_ok(["set", "api.openai.key=sk-test1"])
    _run_ok(["set", "api.gemini.key=test-key-2"])
    _run_ok(["set", "api.claude.key=test-key-3"])
    _run_ok(["set", "api.deepseek.key=test-key-4"])

    # Verify configuration file contains all settings
    cfg_path = tmp_path / ".hippo" / "config.json"
    data = cfg_path.read_text(encoding="utf-8")

    # Check engine settings
    assert "openai" in data
    assert "gpt-4o-mini" in data
    assert "0.7" in data
    assert "1000" in data
    assert "30" in data
    assert "https://api.openai.com/v1" in data
    assert "3" in data
