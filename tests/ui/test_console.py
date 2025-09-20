from __future__ import annotations

from datetime import datetime, timezone

from core.ui.console import friendly_ts, progress_bar, line, summary_panel, rule, banner


def test_console_helpers_cover_branches():
    now = datetime.now(timezone.utc)
    # iso com timezone
    s1 = friendly_ts(now.isoformat())
    assert "UTC" in s1
    # sem timezone
    s2 = friendly_ts(now.replace(tzinfo=None).isoformat())
    assert len(s2) >= 10
    # string inválida deve retornar como veio
    s3 = friendly_ts("not-a-date")
    assert s3 == "not-a-date"

    # impressão simples
    line("Mensagem de teste")
    rule("Regra")
    banner("Titulo")

    # progress_bar com tarefas
    with progress_bar(["load", "extract"]) as (prog, tasks):
        prog.update(tasks["load"], advance=1)
        prog.update(tasks["extract"], advance=1)

    # summary_panel
    summary_panel("Info", "Corpo")
