from __future__ import annotations

from core.domain.manifest import MANIFEST_VERSION, STATUS_AWAITING, Manifest


def test_constants_values():
    assert MANIFEST_VERSION == "1.0.0"
    assert STATUS_AWAITING == "Awaiting Consolidation"


def test_manifest_typed_keys():
    m: Manifest = {
        "manifestVersion": MANIFEST_VERSION,
        "manifestId": "abc",
        "processedAt": "2020-01-01T00:00:00Z",
        "status": STATUS_AWAITING,
        "sourceDocument": {"sourceType": "text", "source": "x", "sourceFormat": "text"},
        "knowledgeIndex": {"references": []},
    }
    assert set(m.keys()) == {
        "manifestVersion",
        "manifestId",
        "processedAt",
        "status",
        "sourceDocument",
        "knowledgeIndex",
    }
