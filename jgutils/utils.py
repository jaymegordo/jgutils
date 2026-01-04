import time
import warnings
from collections.abc import Iterable
from datetime import UTC
from datetime import date
from datetime import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import overload

import pandas as pd

from jgutils import typing as tp

if TYPE_CHECKING:
    from jgutils.typing import T

#  from pandas.to_datetime
warnings.filterwarnings(
    'ignore', message='Discarding nonzero nanoseconds in conversion.')


def check_path(p: Path | str, force_file: bool = False) -> Path:
    """Create path if doesn't exist

    Parameters
    ----------
    p : Path | str
        path to check
    force_file : bool, optional
        if True, path IS a file (eg files with extensions), by default False

    Returns
    -------
    Path
        Path checked
    """
    p = Path(p)

    if p.exists():
        return p

    p_create = p if (
        p.is_dir() or not '.' in p.name) and not force_file else p.parent

    # if file, create parent dir, else create dir
    p_create.mkdir(parents=True, exist_ok=True)

    return p


def flatten_list_list(lst: list[list['T']]) -> list['T']:
    """Flatten single level nested list of lists

    Parameters
    ----------
    lst : list[list]

    Returns
    -------
    list
        flattened list
    """
    return [item for sublist in lst for item in sublist]


@overload
def as_list(items: None) -> list[Any]:
    ...


@overload
def as_list(items: dict[Any, Any]) -> list[tuple[Any, Any]]:
    ...


@overload
def as_list(items: str) -> list[str]:
    ...


@overload
def as_list(items: list['T']) -> list['T']:
    ...


@overload
def as_list(items: Iterable['T']) -> list['T']:
    ...


@overload
def as_list(items: 'T | Iterable[T]') -> list['T']:
    ...


def as_list(
        items: 'T | Iterable[T] | dict[Any, Any] | str | None'
) -> list['T'] | list[tuple[Any, Any]] | list[str] | list[Any]:
    """Convert single item or iterable of items to list
    - if items is None, return empty list

    Parameters
    ----------
    items : Union[Listable[T], dict[Any, Any], str, None]
        item, iterable of items, single str, dict, or None

    Returns
    -------
    Union[list[T], list[Tuple[Any, Any]], list[str], list[Any]]
        list of items

    Examples
    --------
    >>> as_list(['a', 'b'])
    ['a', 'b']
    >>> as_list(dict(a=1, b=2))
    [('a', 1), ('b', 2)]
    >>> as_list('thing')
    ['thing']
    >>> as_list(None)
    []
    """
    if items is None:
        return []
    elif isinstance(items, str):
        return [items]
    elif isinstance(items, dict):
        return list(items.items())
    elif isinstance(items, Iterable):
        return list(items)
    else:
        return [items]


def last_day_of_period(date: dt, freq: str) -> dt:
    """Return the last day of the period that the given date falls in using pandas.

    Parameters
    ----------
    date : dt
        date to find last day of period for
    freq : str
        frequency of period, must be 'Y', 'M', or 'W'

    Returns
    -------
    dt
        last day of period that date falls in
    """
    # Validate frequency
    if freq not in ('Y', 'M', 'ME', 'W'):
        raise ValueError("freq must be 'Y', 'M', or 'W'")

    # Convert datetime to pandas Period
    period = pd.Period(date, freq=freq)

    # Return the end time of the period as a datetime with time set to 00:00:00
    return period.end_time.to_pydatetime() \
        .replace(hour=0, minute=0, second=0, microsecond=0)


def format_d_rng(d_rng: tuple[dt | date, dt | date]) -> str:
    """Format date range as string

    Parameters
    ----------
    d_rng : tuple[dt, dt]
        date range

    Returns
    -------
    str
        formatted date range
    """
    return f'{d_rng[0].strftime(tp.DATE_FMT)} - {d_rng[1].strftime(tp.DATE_FMT)}'


def upper_dict(data: dict) -> dict:
    """Convert all keys in a dictionary to uppercase.

    Parameters
    ----------
    data : DictAny
        The dictionary to convert.

    Returns
    -------
    DictAny
        A new dictionary with all keys in uppercase.
    """
    return {k.upper(): v for k, v in data.items()}


def time_taken(start: float, round: int = 2) -> str:
    """Get time taken from start time in minutes and seconds if over 60 seconds

    Parameters
    ----------
    start : float
        start time in seconds
    round : int, optional
        round seconds to this decimal, by default 2
    """
    elapsed_time = time.time() - start
    if elapsed_time < 60:
        return f'{elapsed_time:.{round}f}s'
    else:
        minutes, seconds = divmod(elapsed_time, 60)
        return f'{int(minutes)}m {int(seconds)}s'


def size_readable(nbytes: int) -> str:
    """Return human readable file size string from bytes"""
    suffixes = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1

    f = f'{nbytes:.2f}'.rstrip('0').rstrip('.')
    return f'{f} {suffixes[i]}'


def calc_size(p: Path, as_str: bool = True) -> int | str:
    """Calculate size of directory and all subdirs

    Parameters
    ----------
    p : Path
    as_str : bool, optional
        return raw float or nicely formatted string, default False

    Returns
    -------
    int | string
        size of folder
    """
    if p.is_file():
        _size = p.stat().st_size
    elif p.is_dir():
        _size = sum(f.stat().st_size for f in p.glob('**/*') if f.is_file())
    else:
        raise ValueError(f'Path {p} is not a file or directory')

    return size_readable(_size) if as_str else _size


def file_modified_dt(p: Path) -> dt:
    """Get file modified date

    Parameters
    ----------
    p : Path
        file to check

    Returns
    -------
    dt
        date file modified
    """
    return dt.fromtimestamp(p.stat().st_mtime, tz=UTC)
