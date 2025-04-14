import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from ard.storage.file import StorageBackend

if TYPE_CHECKING:
    from ard.hypothesis.hypothesis import Hypothesis


# Custom JSON encoder to handle objects that aren't JSON serializable
class HypothesisJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Try to convert the object to a dict if it has a to_dict method
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        # Try to convert the object to a string
        try:
            return str(obj)
        except:
            return f"<non-serializable: {type(obj).__name__}>"


class Parser(Protocol):
    def parse(self, hypothesis: "Hypothesis"): ...

    output_type: str


@dataclass
class HypothesisSaver:
    """A class for saving hypotheses to a storage backend."""

    storage_backend: "StorageBackend"
    parser: Parser

    def save(self, hypothesis: "Hypothesis") -> None:
        """Save a hypothesis to the storage backend."""
        parsed_hypothesis = self.parser.parse(hypothesis)

        file_name = self.get_file_name(hypothesis)

        self.storage_backend.save_file(
            file_name,
            f"hypothesis.{self.parser.output_type}",
            bytes(parsed_hypothesis, "utf-8"),
        )

    def get_file_name(self, hypothesis: "Hypothesis") -> str:
        file_name = f"{hypothesis.subgraph_id[:10]}-{hypothesis.hypothesis_id[:10]}"

        return file_name


class MarkdownParser(Parser):
    output_type = "md"

    def parse(self, hypothesis: "Hypothesis") -> str:
        return f"""
# {hypothesis.title}

**Hypothesis ID:** {hypothesis.hypothesis_id}

**Subgraph ID:** {hypothesis.subgraph_id}

{hypothesis.statement}

## References
{"\n".join(hypothesis.references)}

## Context
{hypothesis.source._context}

## Subgraph
```
{hypothesis.source.to_cypher_string()}
```
"""


class JSONParser(Parser):
    output_type = "json"

    def parse(self, hypothesis: "Hypothesis"):
        return json.dumps(
            {
                "title": hypothesis.title,
                "text": hypothesis.statement,
                "hypothesis_id": hypothesis.hypothesis_id,
                "subgraph_id": hypothesis.subgraph_id,
                "references": hypothesis.references,
                "metadata": hypothesis.metadata,
                "method_name": str(hypothesis.method),
                "method": hypothesis.method.to_json(),
                "source": hypothesis.source.to_json(),
            },
            cls=HypothesisJSONEncoder,
        )
