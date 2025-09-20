"""Command-line interface for the Hippocampus agent.

Provides the `main` entry point used by the packaged console script,
handling argument parsing and invoking the application pipeline.
"""

from __future__ import annotations

import argparse
import sys

from core.application.pipeline import (build_manifest_from_file,
                                       build_manifest_from_text)
from core.infrastructure.config.manager import ConfigManager
from core.resources.templates import render_template
from core.ui.console import rule, summary_panel

_TPL_CONFIG_SET = "config_set.j2"
_TPL_ERROR = "error.j2"
_TPL_YAML_SAMPLE = "config_apply.yaml.j2"


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
        "hippo collect -f document.pdf -o ./hippo-out\n"
        "hippo collect --verbose -f document.pdf -o ./hippo-out\n"
        "hippo set --generate-template -o hippo.yaml"
    )
    summary_panel("Examples", ex)


def _print_collect_help_rich() -> None:
    rule("hippo collect — Help")
    usage = (
        "Usage\n"
        "hippo collect (-t TEXT | -f FILE) [-o OUTPUT]\n"
        "             [--engine ENGINE] [ENGINE OPTS] [--verbose]\n"
        "Default output: ./hippo-out"
    )
    summary_panel("Usage", usage)

    options = (
        "Options\n"
        "-t, --text TEXT         Input text content\n"
        "-f, --file FILE         Input file path\n"
        "-o, --output DIR        Output directory (default: ./hippo-out)\n"
        "--engine ENGINE         Selection: heuristic|llm (default: heuristic)\n"
        "--provider NAME         LLM provider: openai|gemini|claude|deepseek\n"
        "--model NAME            LLM model name (e.g., gpt-4o-mini)\n"
        "--temperature FLOAT     Sampling temperature (LLM)\n"
        "--max-tokens INT        Max output tokens (LLM)\n"
        "--timeout-s INT         Request timeout in seconds (LLM)\n"
        "--base-url URL          Base URL for OpenAI-compatible providers\n"
        "--retries INT           Retry attempts for LLM calls\n"
        "--verbose               Stream step logs (begin/phase) with final report"
    )
    summary_panel("Options", options)

    ex = (
        "Examples\n"
        "hippo collect -f document.pdf -o ./hippo-out\n"
        "hippo collect --engine llm --provider openai --model gpt-4o-mini -f document.pdf\n"
        "hippo collect --verbose -f document.pdf -o ./hippo-out"
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
        "-o", "--output", type=str, default="./hippo-out", help="Output directory"
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=("heuristic", "llm"),
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
    args = parser.parse_args(argv)

    try:
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
        if args.file:
            build_manifest_from_file(
                args.file,
                args.output,
                verbose=args.verbose,
                engine=args.engine,
                engine_overrides=overrides or None,
            )
        else:
            build_manifest_from_text(
                args.text,
                args.output,
                verbose=args.verbose,
                engine=args.engine,
                engine_overrides=overrides or None,
            )
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Invalid value: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        if args.verbose:
            raise
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def _print_set_help_rich() -> None:
    rule("hippo set — Help")
    usage = (
        "Usage\n"
        "hippo set [--local|--global] [--generate-template|-o PATH|--file YAML [--merge|--reset]]\n"
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
        if args.generate_template:
            content = render_template(_TPL_YAML_SAMPLE)
            if args.output:
                p = args.output
                from pathlib import Path

                Path(p).expanduser().resolve().write_text(content, encoding="utf-8")
                print(
                    render_template(
                        _TPL_CONFIG_SET, scope=scope_name, key="template", value=p
                    )
                )
            else:
                print(content)
            return 0

        if args.file:
            mgr.apply_yaml(args.file, reset=bool(args.reset))
            print(
                render_template(
                    _TPL_CONFIG_SET, scope=scope_name, key="yaml", value=args.file
                )
            )
            return 0

        if args.entry:
            if "=" not in args.entry:
                raise ValueError("entry must be in the form key=value")
            key, value = args.entry.split("=", 1)
            mgr.set(key.strip(), value.strip())
            masked = value if not key.endswith(".key") else "***"
            print(
                render_template(
                    _TPL_CONFIG_SET, scope=scope_name, key=key, value=masked
                )
            )
            return 0

        raise ValueError(
            "nothing to do; provide --generate-template, --file or key=value"
        )
    except Exception as e:  # noqa: BLE001
        print(
            render_template(_TPL_ERROR, title=str(e), hint="Use --help for usage."),
            file=sys.stderr,
        )
        return 1


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
