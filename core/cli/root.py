"""Command-line interface for the Hippocampus agent.

Provides the `main` entry point used by the packaged console script,
handling argument parsing and invoking the application pipeline.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from core.application.pipeline import build_manifest_from_file, build_manifest_from_text
from core.cli.exit_codes import get_exit_code_for_exception
from core.infrastructure.config.manager import ConfigManager
from core.infrastructure.logging.structured import get_logger
from core.resources.templates import render_template
from core.ui.console import rule, summary_panel

_TPL_CONFIG_SET = "config_set.j2"
_TPL_ERROR = "error.j2"
_TPL_YAML_SAMPLE = "config_apply.yaml.j2"


def _print_config_applied(scope_name: str, key: str, value: str) -> None:
    print(render_template(_TPL_CONFIG_SET, scope=scope_name, key=key, value=value))


def _handle_set_exception(exc: Exception, scope_name: str) -> int:
    exit_code = get_exit_code_for_exception(exc)
    logger = get_logger(__name__)
    logger.error(
        f"Configuration error: {exc}",
        exit_code=int(exit_code),
        error_type=type(exc).__name__,
        scope=scope_name,
    )
    title = f"Configuration error: {exc}"
    if isinstance(exc, FileNotFoundError):
        hint = (
            "Confirme o caminho do YAML.\n"
            "- Gere um template: hippo set --generate-template -o hippo.yaml\n"
            "- Use --file hippo.yaml --merge para aplicar"
        )
    elif isinstance(exc, PermissionError):
        hint = (
            "Permissão negada ao acessar arquivo de configuração.\n"
            "- Ajuste permissões do caminho ou escolha outro arquivo com -o"
        )
    elif isinstance(exc, ValueError) and (
        "entry must be in the form key=value" in str(exc)
    ):
        hint = (
            "Entrada inválida. Use o formato key=value.\n"
            "Ex.: hippo set engine.model=gpt-4o-mini"
        )
    elif isinstance(exc, ValueError) and str(exc).startswith("nothing to do"):
        hint = "Use --help for usage."
    else:
        hint = "Use --help para ver exemplos de uso."
    print(render_template(_TPL_ERROR, title=title, hint=hint), file=sys.stderr)
    return int(exit_code)


def _perform_set_action(
    args: argparse.Namespace, scope_name: str, mgr: ConfigManager
) -> None:
    if args.generate_template:
        content = render_template(_TPL_YAML_SAMPLE)
        if args.output:
            p = args.output
            Path(p).expanduser().resolve().write_text(content, encoding="utf-8")
            _print_config_applied(scope_name, "template", p)
        else:
            print(content)
        return

    if args.file:
        mgr.apply_yaml(args.file, reset=bool(args.reset))
        _print_config_applied(scope_name, "yaml", args.file)
        return

    if args.entry:
        if "=" not in args.entry:
            raise ValueError("entry must be in the form key=value")
        key, value = args.entry.split("=", 1)
        mgr.set(key.strip(), value.strip())
        masked = value if not key.endswith(".key") else "***"
        _print_config_applied(scope_name, key, masked)
        return

    raise ValueError("nothing to do; provide --generate-template, --file or key=value")


def _collect_overrides(args: argparse.Namespace) -> dict[str, Any] | None:
    overrides = {
        k: v
        for k, v in {
            "provider": args.provider,
            "model": args.model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "timeout_s": args.timeout_s,
            "base_url": args.base_url,
            "retries": args.retries,
        }.items()
        if v is not None
    }
    return overrides or None


def _make_graph_config(args: argparse.Namespace) -> Any | None:
    if args.engine != "llm-graph":
        return None
    from core.noesis.graph.types import GraphConfig

    return GraphConfig(
        enabled=True,
        use_fallback=not bool(args.no_graph_fallback),
        timeout_s=(args.graph_timeout if args.graph_timeout is not None else 60),
        retries=args.graph_retries if args.graph_retries is not None else 0,
        backoff_base_s=(
            args.graph_backoff_base if args.graph_backoff_base is not None else 0.1
        ),
        backoff_max_s=(
            args.graph_backoff_max if args.graph_backoff_max is not None else 2.0
        ),
        jitter_s=(args.graph_jitter if args.graph_jitter is not None else 0.05),
    )


def _handle_collect_exception(
    exc: Exception, args: argparse.Namespace, output_dir: str
) -> int:
    exit_code = get_exit_code_for_exception(exc)
    logger = get_logger(__name__)
    if isinstance(exc, FileNotFoundError):
        logger.error(f"File not found: {exc}", exit_code=int(exit_code))
        hint = (
            "Verifique se o caminho existe e é legível.\n"
            "- Use um caminho absoluto com -f\n"
            "- Verifique permissões de leitura/escrita no destino: "
            f"{output_dir}"
        )
        title = f"File not found: {exc}"
    elif isinstance(exc, PermissionError):
        logger.error("Permission denied", exit_code=int(exit_code), error=str(exc))
        hint = (
            "Verifique permissões de leitura do arquivo e "
            f"escrita em '{output_dir}'.\n"
            "- Ajuste permissões (chmod/chown) ou use um usuário com acesso\n"
            "- Confirme o caminho passado ao -f"
        )
        title = f"Permission error: {exc}"
    elif isinstance(exc, ValueError):
        logger.error(f"Invalid value: {exc}", exit_code=int(exit_code))
        hint = (
            "Corrija a entrada/configuração e tente novamente.\n"
            "- Dica: use --verbose para detalhes adicionais\n"
            "- Se for validação de manifesto, verifique campos exigidos"
        )
        title = f"Invalid value: {exc}"
    elif isinstance(exc, TimeoutError):
        logger.error("Timeout during operation", exit_code=int(exit_code))
        graph_tips = (
            "- Ajuste --graph-timeout e --graph-retries\n"
            "- Considere --graph-backoff-base/--graph-backoff-max\n"
        )
        llm_tips = (
            "- Aumente --timeout-s e/ou --retries\n"
            "- Também é possível usar a env HIPPO_LLM_RETRIES\n"
        )
        hint = (
            "A operação excedeu o tempo limite.\n"
            f"{graph_tips if args.engine == 'llm-graph' else ''}"
            f"{llm_tips if args.engine in ('llm', 'llm-graph') else ''}"
            "- Reduza o tamanho da entrada quando possível"
        )
        title = f"Timeout: {exc}"
    elif isinstance(exc, ImportError):
        logger.error("Missing dependency", exit_code=int(exit_code), error=str(exc))
        hint = (
            "Instale dependências opcionais para provedores LLM.\n"
            "Ex.: pip install langchain_openai "
            "langchain_google_genai langchain_anthropic"
        )
        title = f"Dependency error: {exc}"
    else:  # noqa: BLE001
        logger.error(
            f"Unexpected error: {exc}",
            exit_code=int(exit_code),
            error_type=type(exc).__name__,
        )
        if getattr(args, "verbose", False):
            raise exc
        hint = "Use --verbose para ver o traceback."
        title = f"error: {exc}"

    print(render_template(_TPL_ERROR, title=title, hint=hint), file=sys.stderr)
    return int(exit_code)


def _default_output_dir() -> str:
    return str(
        Path.home() / ".brain-model" / "hippocampus" / "buffer" / "consolidation"
    )


def _print_main_help_rich() -> None:
    rule("Hippocampus — Help")
    usage = "Usage\nhippo <command> [options]\nCommands: collect, set"
    summary_panel("Usage", usage)

    options = "Options\nUse `hippo <command> -h` for command-specific options"
    summary_panel("Options", options)

    sub = (
        "Subcommands\n"
        "collect  Build a manifest from text or file\n"
        "set      Configure Hippocampus (local/global scopes)"
    )
    summary_panel("Subcommands", sub)

    ex = (
        "Examples\n"
        "hippo collect -f document.pdf\n"
        "hippo collect --verbose -f document.pdf\n"
        "hippo set --generate-template -o hippo.yaml"
    )
    summary_panel("Examples", ex)


def _print_collect_help_rich() -> None:
    rule("hippo collect — Help")
    usage = (
        "Usage\n"
        "hippo collect (-t TEXT | -f FILE) [-o OUTPUT]\n"
        "             [--engine ENGINE] [ENGINE OPTS] [--graph-opts] [--verbose]\n"
        "Default output: ~/.brain-model/hippocampus/buffer/consolidation"
    )
    summary_panel("Usage", usage)

    options = (
        "Options\n"
        "-t, --text TEXT         Input text content\n"
        "-f, --file FILE         Input file path\n"
        "-o, --output DIR        Output directory (default:\n"
        "                        ~/.brain-model/hippocampus/buffer/consolidation)\n"
        "                        or $HIPPO_OUTPUT_DIR when set\n"
        "--engine ENGINE         Selection: heuristic|llm|llm-graph\n"
        "                        (default: heuristic)\n"
        "--provider NAME         LLM provider: openai|gemini|claude|deepseek\n"
        "--model NAME            LLM model name (e.g., gpt-4o-mini)\n"
        "--temperature FLOAT     Sampling temperature (LLM)\n"
        "--max-tokens INT        Max output tokens (LLM)\n"
        "--timeout-s INT         Request timeout in seconds (LLM)\n"
        "--base-url URL          Base URL for OpenAI-compatible providers\n"
        "--retries INT           Retry attempts for LLM calls\n"
        "--verbose               Stream step logs (begin/phase) with final report\n"
        "--graph-timeout INT     Graph per-node timeout (seconds)\n"
        "--graph-retries INT     Graph per-node retry attempts\n"
        "--no-graph-fallback     Disable heuristic fallback in graph path\n"
        "--graph-backoff-base FLOAT  Graph retry backoff base seconds (default 0.1)\n"
        "--graph-backoff-max FLOAT   Graph retry backoff max seconds (default 2.0)\n"
        "--graph-jitter FLOAT        Graph retry jitter seconds (default 0.05)"
    )
    summary_panel("Options", options)

    ex = (
        "Examples\n"
        "hippo collect -f document.pdf\n"
        "hippo collect --engine llm --provider openai \\\n+"
        "              --model gpt-4o-mini -f document.pdf\n"
        "hippo collect --verbose -f document.pdf"
    )
    summary_panel("Examples", ex)


def _cmd_collect(argv: list[str] | None) -> int:
    if argv and any(x in ("-h", "--help") for x in argv):
        _print_collect_help_rich()
        return 0
    parser = argparse.ArgumentParser(
        description=(
            "Build a manifest from text or file using heuristic or LLM engine."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  hippo collect -f document.pdf -o ./hippo-out\n"
            "  hippo collect --verbose -f document.pdf -o ./hippo-out"
        ),
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("-t", "--text", type=str, help="Input text content")
    g.add_argument("-f", "--file", type=str, help="Input file path")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=_default_output_dir(),
        help=f"Output directory (default: {_default_output_dir()})",
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=("heuristic", "llm", "llm-graph"),
        default="heuristic",
        help="Engine selection (default: heuristic)",
    )
    # LLM overrides
    parser.add_argument("--provider", type=str, help="LLM provider name")
    parser.add_argument("--model", type=str, help="LLM model name")
    parser.add_argument("--temperature", type=float, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, help="Max output tokens")
    parser.add_argument("--timeout-s", type=int, help="Timeout seconds")
    parser.add_argument("--base-url", type=str, help="OpenAI-compatible base URL")
    parser.add_argument("--retries", type=int, help="Retry attempts for LLM calls")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    # Graph-specific options
    parser.add_argument(
        "--graph-timeout",
        type=int,
        dest="graph_timeout",
        help="Graph per-node timeout seconds",
    )
    parser.add_argument(
        "--graph-retries",
        type=int,
        dest="graph_retries",
        help="Graph per-node retries",
    )
    parser.add_argument(
        "--no-graph-fallback",
        action="store_true",
        dest="no_graph_fallback",
        help="Disable heuristic fallback in graph",
    )
    parser.add_argument(
        "--graph-backoff-base",
        type=float,
        dest="graph_backoff_base",
        help="Graph retry backoff base seconds",
    )
    parser.add_argument(
        "--graph-backoff-max",
        type=float,
        dest="graph_backoff_max",
        help="Graph retry backoff max seconds",
    )
    parser.add_argument(
        "--graph-jitter",
        type=float,
        dest="graph_jitter",
        help="Graph retry jitter seconds",
    )
    args = parser.parse_args(argv)

    # Precedence: CLI -o > env > default
    env_out = os.getenv("HIPPO_OUTPUT_DIR")
    output_dir = (
        args.output
        if args.output != _default_output_dir()
        else (env_out or args.output)
    )

    try:
        overrides = _collect_overrides(args)
        graph_cfg = _make_graph_config(args)
        if args.file:
            build_manifest_from_file(
                args.file,
                output_dir,
                verbose=args.verbose,
                engine=args.engine,
                engine_overrides=overrides,
                graph_config=graph_cfg,
            )
        else:
            build_manifest_from_text(
                args.text,
                output_dir,
                verbose=args.verbose,
                engine=args.engine,
                engine_overrides=overrides,
                graph_config=graph_cfg,
            )
    except Exception as e:  # noqa: BLE001
        return _handle_collect_exception(e, args, output_dir)
    return 0


def _print_set_help_rich() -> None:
    rule("hippo set — Help")
    usage = (
        "Usage\n"
        "hippo set [--local|--global] [--generate-template|-o PATH|\n"
        "           --file YAML [--merge|--reset]]\n"
        "hippo set key=value"
    )
    summary_panel("Usage", usage)

    options = (
        "Options\n"
        "--local               Local scope (.hippo/config.json)\n"
        "--global              Global scope (~/.config/hippocampus/config.json)\n"
        "--generate-template   Print YAML sample (or save with -o)\n"
        "--file YAML           Apply YAML (default: merge; use --reset to replace)\n"
        "-o, --output PATH     Output path for the template\n"
        "--merge | --reset     Strategy when applying YAML"
    )
    summary_panel("Options", options)

    keys = (
        "Supported Keys\n"
        "Engine:\n"
        "- engine.provider\n"
        "- engine.model\n"
        "- engine.temperature\n"
        "- engine.max_tokens\n"
        "- engine.timeout_s\n"
        "- engine.base_url\n"
        "- engine.retries\n"
        "Secrets:\n"
        "- api.openai.key\n"
        "- api.gemini.key\n"
        "- api.claude.key\n"
        "- api.deepseek.key"
    )
    summary_panel("Keys", keys)

    ex = (
        "Examples\n"
        "hippo set engine.model=gpt-4o-mini\n"
        "hippo set --generate-template -o hippo.yaml\n"
        "hippo set --file hippo.yaml --merge"
    )
    summary_panel("Examples", ex)


def _cmd_set(argv: list[str] | None) -> int:
    if argv and any(x in ("-h", "--help") for x in argv):
        _print_set_help_rich()
        return 0
    parser = argparse.ArgumentParser(
        description="Configure Hippocampus (local or global scope)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  hippo set --generate-template\n"
            "  hippo set --generate-template -o hippo.yaml\n"
            "  hippo set --file hippo.yaml --merge\n"
            "  hippo set --file hippo.yaml --reset\n"
            "  hippo set engine.model=gpt-4o-mini\n"
            "  hippo set api.openai.key=sk-...\n"
        ),
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--local",
        action="store_true",
        help="Apply to local scope (.hippo/config.json)",
    )
    scope.add_argument(
        "--global",
        dest="use_global",
        action="store_true",
        help="Apply to global scope (~/.config/hippocampus/config.json)",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--generate-template",
        action="store_true",
        help="Print a YAML config template (or write to -o)",
    )
    mode.add_argument("--file", type=str, help="Apply settings from YAML file")
    parser.add_argument("entry", nargs="?", help="Single entry in the form key=value")

    parser.add_argument(
        "-o", "--output", type=str, help="Output path for generated template"
    )
    merge = parser.add_mutually_exclusive_group()
    merge.add_argument(
        "--merge",
        action="store_true",
        help="Merge YAML into existing config (default)",
    )
    merge.add_argument(
        "--reset", action="store_true", help="Replace existing config with YAML"
    )

    args = parser.parse_args(argv)
    scope_name = "global" if args.use_global else "local"
    mgr = ConfigManager(scope=scope_name)

    try:
        _perform_set_action(args, scope_name, mgr)
        return 0
    except Exception as e:  # noqa: BLE001
        return _handle_set_exception(e, scope_name)


def main(argv: list[str] | None = None) -> int:
    """Hippocampus CLI entry point.

    Parses arguments, runs the manifest build pipeline and reports errors in a
    friendly way (or re-raises exceptions with `--verbose`).

    Args:
        argv: Argument list (for tests). Uses `sys.argv` when None.

    Returns:
        Process exit code (0 on success, 1 on failure).
    """
    # Normalize argv for subcommand detection and parsing
    arglist = list(argv) if argv is not None else sys.argv[1:]

    # Subcommand dispatch
    if arglist:
        cmd = arglist[0]
        if cmd == "set":
            return _cmd_set(arglist[1:])
        if cmd == "collect":
            return _cmd_collect(arglist[1:])
        if any(x in ("-h", "--help") for x in arglist):
            _print_main_help_rich()
            return 0
        # Backward compatibility: treat legacy flags as 'collect'
        if any(x in ("-t", "--text", "-f", "--file") for x in arglist):
            return _cmd_collect(arglist)

    # No args: print main help
    _print_main_help_rich()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
