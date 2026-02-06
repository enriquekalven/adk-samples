"""Module containing definitions for the capabilities in CaMeL."""
import dataclasses
from typing import Any, Self
from . import readers, sources

@dataclasses.dataclass(frozen=True)
class Capabilities:
    """Capabilities for a value."""
    sources_set: frozenset[sources.Source]
    readers_set: readers.Readers[Any]
    other_metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.sources_set) ^ hash(self.readers_set) ^ hash(tuple(self.other_metadata.items()))

    @classmethod
    def default(cls) -> Self:
        return cls(frozenset({sources.SourceEnum.USER}), readers.Public())

    @classmethod
    def camel(cls) -> Self:
        return cls(frozenset({sources.SourceEnum.CAMEL}), readers.Public())