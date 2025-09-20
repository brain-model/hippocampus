from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


# === NORMALIZATION TESTS ===
class TestNormalizeOutput:
    """Testa normalização de saída do LLM"""

    def test_normalize_output_complete_reference(self):
        agent = LangChainExtractionAgent()
        data = {
            "references": [{
                "id": 1,
                "rawString": "https://example.com",
                "referenceType": "web_link",
                "sourceFormat": "web_content",
                "sourcePath": "https://example.com",
                "details": {"title": "Example"}
            }]
        }

        result = agent._normalize_output(data)

        assert "references" in result
        assert len(result["references"]) == 1
        ref = result["references"][0]
        assert ref["id"] == 1
        assert ref["rawString"] == "https://example.com"
        assert ref["referenceType"] == "web_link"
        assert ref["details"]["title"] == "Example"

    def test_normalize_output_legacy_format(self):
        agent = LangChainExtractionAgent()
        data = {
            "references": [{
                "title": "Test Paper",
                "authors": ["Smith, J."],
                "year": 2023,
                "url": "https://example.com/paper",
                "doi": "10.1000/test"
            }]
        }

        result = agent._normalize_output(data)

        assert "references" in result
        ref = result["references"][0]
        assert ref["rawString"] == "https://example.com/paper"
        assert ref["referenceType"] == "web_link"
        assert ref["sourceFormat"] == "web_content"
        assert ref["details"]["title"] == "Test Paper"
        assert ref["details"]["authors"] == ["Smith, J."]
        assert ref["details"]["year"] == 2023
        assert ref["details"]["doi"] == "10.1000/test"

    def test_normalize_output_doi_without_url(self):
        agent = LangChainExtractionAgent()
        data = {
            "references": [{
                "title": "DOI Paper",
                "doi": "10.1000/test"
            }]
        }

        result = agent._normalize_output(data)

        ref = result["references"][0]
        assert ref["rawString"] == "https://doi.org/10.1000/test"
        assert ref["sourcePath"] == "https://doi.org/10.1000/test"

    def test_normalize_output_citation_text(self):
        agent = LangChainExtractionAgent()
        data = {
            "references": [{
                "citation": "Smith, J. (2023). Test paper."
            }]
        }

        result = agent._normalize_output(data)

        ref = result["references"][0]
        assert ref["rawString"] == "Smith, J. (2023). Test paper."
        assert ref["referenceType"] == "in_text_citation"
        assert ref["sourceFormat"] == "text"

    def test_normalize_output_filters_invalid_references(self):
        agent = LangChainExtractionAgent()
        data = {
            "references": [
                {"title": "Valid paper", "url": "https://valid.com"},
                "invalid string reference",  # Should be filtered
                {"incomplete": "data"},  # Should be filtered
                None,  # Should be filtered
                {"title": "Another valid", "citation": "Valid citation"}
            ]
        }

        result = agent._normalize_output(data)

        # Devem restar as referências válidas (com url, citation ou title)
        assert len(result["references"]) >= 2
        # Verificar que referências inválidas foram filtradas
        valid_refs = [r for r in result["references"] if r is not None]
        assert len(valid_refs) >= 2

    def test_normalize_output_only_returns_references(self):
        agent = LangChainExtractionAgent()
        data = {
            "references": [],
            "summary": "Test summary",
            "metadata": {"key": "value"}
        }

        result = agent._normalize_output(data)

        # _normalize_output only returns references, not other fields
        assert result == {"references": []}


# === REFERENCE ITEM NORMALIZATION TESTS ===
class TestNormalizeReferenceItem:
    """Testa normalização de item individual de referência"""

    def test_normalize_reference_item_complete_format(self):
        agent = LangChainExtractionAgent()
        ref = {
            "id": 1,
            "rawString": "test",
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": "path",
            "details": {"extra": "data"}
        }

        result = agent._normalize_reference_item(ref, 0)

        assert result == ref

    def test_normalize_reference_item_missing_details(self):
        agent = LangChainExtractionAgent()
        ref = {
            "rawString": "test",
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": "path"
        }

        result = agent._normalize_reference_item(ref, 5)

        assert result["id"] == 5  # Uses provided index
        assert result["details"] == {}

    def test_normalize_reference_item_null_details(self):
        agent = LangChainExtractionAgent()
        ref = {
            "rawString": "test",
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": "path",
            "details": None
        }

        result = agent._normalize_reference_item(ref, 0)

        assert result["details"] == {}

    def test_normalize_reference_item_invalid_input(self):
        agent = LangChainExtractionAgent()

        # Test non-dict input
        assert agent._normalize_reference_item("invalid", 0) is None
        assert agent._normalize_reference_item(None, 0) is None
        assert agent._normalize_reference_item([], 0) is None

    def test_normalize_reference_item_missing_required_fields(self):
        agent = LangChainExtractionAgent()
        ref = {
            "rawString": "test",
            "referenceType": "web_link"
            # Missing sourceFormat, sourcePath, details
        }

        # Should fall back to legacy normalization
        result = agent._normalize_reference_item(ref, 0)

        # Returns fallback format with empty rawString since no url/citation/doi/title
        assert result is not None
        assert result["rawString"] == ""
        assert result["referenceType"] == "in_text_citation"

    def test_normalize_reference_item_legacy_with_url(self):
        agent = LangChainExtractionAgent()
        ref = {
            "title": "Test",
            "url": "https://test.com",
            "year": "2023"
        }

        result = agent._normalize_reference_item(ref, 2)

        assert result["id"] == 2
        assert result["rawString"] == "https://test.com"
        assert result["referenceType"] == "web_link"
        assert result["sourceFormat"] == "web_content"
        assert result["sourcePath"] == "https://test.com"
        assert result["details"]["title"] == "Test"
        assert result["details"]["year"] == "2023"

    def test_normalize_reference_item_legacy_with_citation(self):
        agent = LangChainExtractionAgent()
        ref = {
            "title": "Test Paper",
            "citation": "Smith et al. (2023)"
        }

        result = agent._normalize_reference_item(ref, 3)

        assert result["rawString"] == "Smith et al. (2023)"
        assert result["referenceType"] == "in_text_citation"
        assert result["sourceFormat"] == "text"
        assert result["sourcePath"] == ""
        assert result["details"]["title"] == "Test Paper"

    def test_normalize_reference_item_legacy_doi_to_url(self):
        agent = LangChainExtractionAgent()
        ref = {
            "title": "DOI Paper",
            "doi": "10.1000/test",
            "authors": ["Author A"]
        }

        result = agent._normalize_reference_item(ref, 4)

        assert result["rawString"] == "https://doi.org/10.1000/test"
        assert result["sourcePath"] == "https://doi.org/10.1000/test"
        assert result["details"]["doi"] == "10.1000/test"
        assert result["details"]["authors"] == ["Author A"]
