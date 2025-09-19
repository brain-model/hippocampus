from __future__ import annotations

from __future__ import annotations

from core.infrastructure.loaders.pdf import PdfLoader
from core.infrastructure.loaders.registry import get_loader_for_file
import types
import sys


def test_registry_selects_pdf_loader():
    loader = get_loader_for_file("doc.pdf")
    assert isinstance(loader, PdfLoader)


def test_pdf_loader_reads_pages(monkeypatch, tmp_path):
    # Create a fake pypdf with a PdfReader returning pages with extract_text
    fake_pypdf = types.ModuleType("pypdf")

    class Page:
        def extract_text(self):
            return "Page 1 text https://example.com"

    class PdfReader:
        def __init__(self, *_args, **_kwargs):
            self.pages = [Page()]

    fake_pypdf.PdfReader = PdfReader  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pypdf", fake_pypdf)

    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4\n...")
    loader = PdfLoader()
    out = loader.load(file_path=str(p))
    assert "https://example.com" in out


def test_pdf_loader_param_validation():
    loader = PdfLoader()
    # text passthrough
    out = loader.load(text="inline text")
    assert out == "inline text"
    # missing file_path
    try:
        loader.load()
    except ValueError as e:
        assert "file_path" in str(e)
    else:
        raise AssertionError("Expected ValueError when file_path missing")


def test_pdf_loader_skips_page_errors(monkeypatch, tmp_path):
    import types
    import sys

    fake_pypdf = types.ModuleType("pypdf")

    class BadPage:
        def extract_text(self):
            raise RuntimeError("boom")

    class GoodPage:
        def extract_text(self):
            return "OK"

    class PdfReader:
        def __init__(self, *_args, **_kwargs):
            self.pages = [BadPage(), GoodPage()]

    fake_pypdf.PdfReader = PdfReader  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pypdf", fake_pypdf)

    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4\n...")
    loader = PdfLoader()
    out = loader.load(file_path=str(p))
    assert out.strip().endswith("OK")
