from __future__ import annotations

from core.infrastructure.loaders.latex import LatexLoader
from core.infrastructure.loaders.registry import get_loader_for_file


def test_latex_loader_from_text():
    tex = r"""
    \section{Intro}
    Some text with \textbf{bold} and a \url{https://ex.com}.
    \begin{figure}
    ignored content
    \end{figure}
    """
    loader = LatexLoader()
    out = loader.load(text=tex)
    assert "Intro" in out
    assert "bold" in out
    assert "https://ex.com" in out


def test_registry_selects_latex_loader():
    loader = get_loader_for_file("paper.tex")
    assert isinstance(loader, LatexLoader)


def test_latex_loader_param_validation(tmp_path):
    loader = LatexLoader()
    # neither provided
    try:
        loader.load()
    except ValueError as e:
        assert "either" in str(e)
    else:
        raise AssertionError("Expected ValueError when neither param is provided")
    # both provided
    try:
        loader.load(text="x", file_path=str(tmp_path / "x.tex"))
    except ValueError as e:
        assert "only one" in str(e)
    else:
        raise AssertionError("Expected ValueError when both params are provided")


def test_latex_loader_from_file(tmp_path):
    p = tmp_path / "s.tex"
    p.write_text("\\section{Intro} X\\textbf{B}", encoding="utf-8")
    loader = LatexLoader()
    out = loader.load(file_path=str(p))
    assert "Intro" in out and "B" in out
