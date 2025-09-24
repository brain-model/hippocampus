from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule

_console = Console()


def banner(title: str) -> None:
    _console.print(Panel.fit(f"[bold]{title}[/bold]", border_style="cyan"))


def line(text: str) -> None:
    _console.print(text)


def rule(text: str) -> None:
    _console.print(Rule(text))


@contextmanager
def collect_section(title: str = "Collect") -> Iterator[None]:
    rule(f"✳ {title} Start ✳")
    try:
        yield
    finally:
        rule(f"✳ {title} End ✳")


def summary_panel(title: str, body: str) -> None:
    _console.print(Panel.fit(body, title=title, border_style="green", padding=(0, 1)))


@contextmanager
def progress_bar(task_names: list[str]) -> Iterator[tuple[Progress, dict[str, int]]]:
    columns = (
        SpinnerColumn(style="cyan"),
        TextColumn("{task.description}"),
        BarColumn(bar_width=None),
        TimeElapsedColumn(),
    )
    with Progress(*columns, transient=False) as prog:
        tasks: dict[str, int] = {}
        for name in task_names:
            tasks[name] = prog.add_task(name, total=1)
        yield prog, tasks


def friendly_ts(dt: str) -> str:
    # dt: ISO8601 string; return shorter human-friendly form YYYY-MM-DD HH:MM:SS UTC
    try:
        from datetime import datetime

        d = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        return d.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return dt
