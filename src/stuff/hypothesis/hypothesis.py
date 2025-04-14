import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

from hypothesis.saver import HypothesisSaver, JSONParser, MarkdownParser
from hypothesis.types import HypothesisGeneratorProtocol


@dataclass
class Hypothesis:
    """A class representing a research hypothesis with its source subgraph and metadata."""

    title: str
    statement: str
    source: Subgraph
    method: HypothesisGeneratorProtocol
    references: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def hypothesis_id(self) -> str:
        """The ID of the hypothesis."""
        return hashlib.sha256(str(self.statement).encode()).hexdigest()

    @property
    def subgraph_id(self) -> str:
        """The ID of the subgraph."""
        return self.source.subgraph_id

    def save(
        self,
        saver: Optional[HypothesisSaver] = None,
        backend_type: str = "local",
        backend_path: str = ".",
        parser_type: Literal["json", "md"] = "json",
        backend_name: str = "hypothesis",
    ):
        """Save the hypothesis using a provided saver or specified storage configuration.

        Args:
            saver: An optional HypothesisSaver instance. If provided, other parameters are ignored.
            backend_type: Type of storage backend ("s3" or "local")
            backend_path: Path for the storage backend
            parser_type: Type of parser (currently only "json" supported)
            backend_name: Name to identify the backend
        """
        # Use provided saver if available
        if saver is not None:
            saver.save(self)
            return

        # Otherwise, create one from parameters
        # Set up storage manager and backend
        storage_manager = StorageManager()
        storage_manager.add_backend(backend_type, backend_path, backend_name)

        # Select parser based on type
        if parser_type.lower() == "json":
            parser = JSONParser()
        elif parser_type.lower() == "md":
            parser = MarkdownParser()
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")

        # Create saver and save
        hypothesis_saver = HypothesisSaver(
            storage_backend=storage_manager.get_backend(backend_name), parser=parser
        )
        hypothesis_saver.save(self)
