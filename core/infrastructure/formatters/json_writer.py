"""Formatter for persisting manifests as JSON files on disk.

Ensures required fields exist and writes the artifact in a stable path
under the provided output directory.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class ManifestJsonWriter:
    """Write the manifest as JSON in the output directory.

    Also ensures the presence of minimal fields (`manifestVersion`,
    `manifestId`, `processedAt`) when missing from the given dictionary.
    """

    def write(self, manifest: dict, out_dir: str) -> str:
        """Persist the manifest in `out_dir/manifest/manifest.json`.

        Args:
            manifest: Manifest dictionary to be persisted.
            out_dir: Base output directory.

        Returns:
            Absolute path of the written JSON file.
        """
        out = Path(out_dir).expanduser().resolve()
        (out / "manifest").mkdir(parents=True, exist_ok=True)

        manifest.setdefault("manifestVersion", "1.0.0")
        manifest.setdefault("manifestId", uuid4().hex)
        manifest.setdefault("processedAt", datetime.now(UTC).isoformat())

        # Default consolidation buffer path
        default_buffer = (
            Path.home() / ".brain-model" / "hippocampus" / "buffer" / "consolidation"
        ).resolve()

        if out == default_buffer:
            # Create unique filename to accumulate manifests in the buffer
            short_id = str(manifest.get("manifestId", ""))[:5]
            date_prefix = str(manifest.get("processedAt", ""))[:10].replace("-", "")
            filename = f"manifest_{date_prefix}_{short_id}.json"
        else:
            filename = "manifest.json"

        target = out / "manifest" / filename
        target.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(target)
