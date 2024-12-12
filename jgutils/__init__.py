from typing import Any
from typing import TypeVar

T = TypeVar('T')
DictAny = dict[str, Any]
Listable = T | list[T]  # either single item or list of items
