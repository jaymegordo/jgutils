from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

T = TypeVar('T')
StrNone = Optional[str]
FloatNone = Optional[float]
IntNone = Optional[int]
DictAny = Dict[str, Any]
Listable = Union[T, List[T]]  # either single item or list of items
