from datetime import datetime as dt
from pathlib import Path
from typing import Any


from typing import Optional
from typing import TypeVar
from typing import Union

T = TypeVar('T')
StrNone = Optional[str]
FloatNone = Optional[float]
IntNone = Optional[int]
DictAny = dict[str, Any]
Listable = Union[T, list[T]]  # either single item or list of items
PathNone = Optional[Path]
DtNone = Optional[dt]
Num = Union[int, float]

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'
DATETIME_MINS_FMT = '%Y-%m-%d %H:%M'
