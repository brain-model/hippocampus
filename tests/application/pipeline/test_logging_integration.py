from __future__ import annotations

import logging

from core.application.pipeline import build_manifest_from_text


def test_pipeline_logs_metrics_when_verbose(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="core.application.pipeline")

    # Run pipeline in verbose mode (heuristic) to trigger metrics logging
    manifest = build_manifest_from_text(
        "Hello http://example.com world",
        out_dir="/tmp",
        verbose=True,
        engine="heuristic",
    )
    assert manifest and manifest.get("manifestId")

    # Assert that the structured logger emitted the completion message
    assert any(
        (
            "Pipeline execution completed" in rec.getMessage()
            and rec.name == "core.application.pipeline"
        )
        for rec in caplog.records
    )
