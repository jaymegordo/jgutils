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
