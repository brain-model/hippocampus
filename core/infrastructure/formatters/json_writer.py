"""Formatter for persisting manifests as JSON files on disk.

Ensures required fields exist and writes the artifact in a stable path
under the provided output directory.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
        manifest.setdefault("processedAt", datetime.now(timezone.utc).isoformat())

        target = out / "manifest" / "manifest.json"
        target.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(target)
