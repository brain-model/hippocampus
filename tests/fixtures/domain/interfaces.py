import pytest


class DummyLoader:
    def load(self, *, text=None, file_path=None):
        if text:
            return text.strip()
        if file_path:
            return "conteúdo do arquivo"
        raise ValueError("Nenhum argumento fornecido")


class DummyAgent:
    def extract(self, text):
        if "referência" in text and "sem referência" not in text:
            return {"references": ["ref1"]}
        return {"references": []}


class DummyFormatter:
    def write(self, manifest, out_dir):
        if not manifest or not out_dir:
            raise ValueError("Manifesto ou diretório ausente")
        return f"{out_dir}/manifest.json"


@pytest.fixture
def dummy_loader():
    return DummyLoader()


@pytest.fixture
def dummy_agent():
    return DummyAgent()


@pytest.fixture
def dummy_formatter():
    return DummyFormatter()
