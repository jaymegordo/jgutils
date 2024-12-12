from datetime import datetime as dt
from pathlib import Path
from typing import Any
from typing import TypeVar

T = TypeVar('T')
StrNone = str | None
FloatNone = float | None
IntNone = int | None
DictAny = dict[str, Any]
Listable = T | list[T]  # either single item or list of items
PathNone = Path | None
DtNone = dt | None
Num = int | float

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'
DATETIME_MINS_FMT = '%Y-%m-%d %H:%M'
DATETIME_FMT_UTC = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FMT_UTC_MS = '%Y-%m-%dT%H:%M:%S.%fZ'
