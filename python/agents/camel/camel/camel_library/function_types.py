from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'Pydantic models used in CaMeL.'
from collections.abc import Callable, Mapping
from typing import Any, Generic, ParamSpec, TypeVar
import pydantic
_T = TypeVar('_T')
_P = ParamSpec('_P')

class Function(pydantic.BaseModel, Generic[_P, _T]):
    name: str
    'The name of the function.'
    call: Callable[_P, _T]
    'The call of the function.'
    full_docstring: str
    'The full docstring of the function.'
    parameters: type[pydantic.BaseModel]
    'The parameters of the function.'
    return_type: Any | None
    'The return type of the function.'

class FunctionCall(pydantic.BaseModel, Generic[_T]):
    """An object containing information about a function call requested by an agent."""
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    function: str
    'The name of the function to call.'
    object_type: str | None
    'The name of the type of the object of the method if the function is a method. Otherwise it is `None`.'
    args: Mapping[str, Any]
    'The arguments to pass to the function.'
    output: _T | Exception
    'The output of the function call.'
    is_builtin: bool
    'Whether it is a builtin function.'