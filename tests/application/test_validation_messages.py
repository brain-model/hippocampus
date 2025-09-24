from __future__ import annotations

import pytest

from core.application.validation import validate_manifest


def test_schema_error_root_path_and_order(schema_path: str):
    # Erro na raiz: falta de campos obrigatórios e additionalProperties
    bad = {"foo": 1}
    with pytest.raises(ValueError) as ei:
        validate_manifest(bad, schema_path)
    msg = str(ei.value)
    # Deve conter prefixo e usar <root> para caminho vazio
    assert msg.startswith("Manifest validation failed:")
    assert "<root>" in msg
    # Ordem determinística: sem checar exatamente a ordem, ao menos estável
    # por múltiplas execuções
    # (Executar duas vezes e comparar)
    with pytest.raises(ValueError) as ei2:
        validate_manifest(bad, schema_path)
    assert str(ei.value) == str(ei2.value)
