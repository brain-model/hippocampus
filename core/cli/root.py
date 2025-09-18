"""Command-line interface for the Hippocampus agent.

Provides the `main` entry point used by the packaged console script,
handling argument parsing and invoking the application pipeline.
"""

from __future__ import annotations

import argparse
import sys

from core.application.pipeline import build_manifest_from_text


def main(argv: list[str] | None = None) -> int:
    """Hippocampus CLI entry point.

    Parses arguments, runs the manifest build pipeline and reports errors in a
    friendly way (or re-raises exceptions with `--verbose`).

    Args:
        argv: Argument list (for tests). Uses `sys.argv` when None.

    Returns:
        Process exit code (0 on success, 1 on failure).
    """
    parser = argparse.ArgumentParser(
        prog="hippocampus", description="Hippocampus Agent"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("-t", "--text", type=str, help="Input text content")
    g.add_argument("-f", "--file", type=str, help="Input file path (disabled in MVP)")
    parser.add_argument(
        "-o", "--output", type=str, default="./hippo-out", help="Output directory"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args(argv)

    if args.file:
        parser.error("--file is not supported in MVP. Use --text.")

    try:
        build_manifest_from_text(args.text, args.output)
    except Exception as e:  # noqa: BLE001
        if args.verbose:
            raise
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
