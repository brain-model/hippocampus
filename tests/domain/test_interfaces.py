import pytest


def test_document_loader_happy_path(dummy_loader):
    assert dummy_loader.load(text="  texto  ") == "texto"
    assert dummy_loader.load(file_path="fake.txt") == "conteúdo do arquivo"


def test_document_loader_edge_case(dummy_loader):
    with pytest.raises(ValueError):
        dummy_loader.load()


def test_extraction_agent_happy_path(dummy_agent):
    result = dummy_agent.extract("texto com referência")
    assert "references" in result
    assert result["references"] == ["ref1"]


def test_extraction_agent_no_reference(dummy_agent):
    result = dummy_agent.extract("texto sem referência")
    assert result["references"] == []


def test_formatter_happy_path(dummy_formatter):
    path = dummy_formatter.write({"manifest": True}, "/tmp")
    assert path.endswith("manifest.json")


def test_formatter_edge_case(dummy_formatter):
    with pytest.raises(ValueError):
        dummy_formatter.write({}, "")
