"""Module containining definitions for data readers."""
import dataclasses
from typing import TypeVar

@dataclasses.dataclass(frozen=True)
class Public:
    """Annotation for data that are publicly readable."""

    def __hash__(self) -> int:
        """Hash for Public readers."""
        return 7810134600596034160

    def __and__(self, other) -> 'Readers | NotImplemented':
        if not isinstance(other, frozenset | Public):
            return NotImplemented
        return other

    def __rand__(self, other) -> 'Readers | NotImplemented':
        if not isinstance(other, frozenset | Public):
            return NotImplemented
        return other
_T = TypeVar('_T')
type Readers = frozenset[_T] | Public