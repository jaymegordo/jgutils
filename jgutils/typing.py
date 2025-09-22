from collections.abc import Iterable
from typing import TypeVar

T = TypeVar('T')
Listable = T | Iterable[T]  # either single item or list of items
Num = int | float

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'
DATETIME_MINS_FMT = '%Y-%m-%d %H:%M'
DATETIME_FMT_UTC = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FMT_UTC_MS = '%Y-%m-%dT%H:%M:%S.%fZ'
