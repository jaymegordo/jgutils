from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union
from datetime import datetime as dt

T = TypeVar('T')
StrNone = Optional[str]
FloatNone = Optional[float]
IntNone = Optional[int]
DictAny = Dict[str, Any]
Listable = Union[T, List[T]]  # either single item or list of items
PathNone = Optional[Path]
DtNone = Optional[dt]

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'
DATETIME_MINS_FMT = '%Y-%m-%d %H:%M'