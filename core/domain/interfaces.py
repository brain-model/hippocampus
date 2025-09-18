"""Domain protocols that define core contracts.

These `Protocol` interfaces decouple application logic from concrete
implementations across infrastructure (loaders, extractors, formatters).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentLoader(Protocol):
    """Contract for document loaders.

    Implementations should accept direct text or file path (but not both at
    once), normalize and return the content as a `str`.
    """

    def load(self, *, text: str | None = None, file_path: str | None = None) -> str:
        """Load and normalize text content.

        Args:
            text: Raw text content. Mutually exclusive with `file_path`.
            file_path: Path to a file with content. Exclusive with `text`.

        Returns:
            The normalized content as `str`.
        """


@runtime_checkable
class ExtractionAgent(Protocol):
    """Contract for extraction agents.

    Implementations receive normalized text and return extracted structures
    (such as references, metadata, entities, etc.) in a dictionary ready for
    composition into the manifest.
    """

    def extract(self, text: str) -> dict:
        """Extract structures of interest from text.

        Args:
            text: Normalized text to be processed.

        Returns:
            A dictionary with specific keys (e.g., `references`).
        """


@runtime_checkable
class Formatter(Protocol):
    """Contract for manifest formatters/persisters.

    Implementations are responsible for persisting or representing the
    manifest in a target format (e.g., JSON on disk) and returning the final
    destination.
    """

    def write(self, manifest: dict, out_dir: str) -> str:
        """Persist the manifest into `out_dir` and return the generated path.

        Args:
            manifest: Validated manifest dictionary.
            out_dir: Base directory where the artifact will be written.

        Returns:
            Absolute path to the persisted file or resource.
        """
