"""Module containing definition for data sources."""
import dataclasses
import enum

class SourceEnum(enum.Enum):
    CAMEL = enum.auto()
    USER = enum.auto()
    ASSISTANT = enum.auto()
    TRUSTED_TOOL_SOURCE = enum.auto()

@dataclasses.dataclass(frozen=True)
class Tool:
    """Tool source."""
    tool_name: str
    'Name of the tool.'
    inner_sources: frozenset[str | SourceEnum] = dataclasses.field(default_factory=frozenset)
    'Sources within the tool (e.g., email addresses).'

    def __hash__(self) -> int:
        return hash(self.tool_name) ^ hash(tuple(self.inner_sources))
type Source = SourceEnum | Tool