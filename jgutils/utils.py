
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Union
from typing import overload

from jgutils.typing import Listable
from jgutils.typing import T


def check_path(p: Union[Path, str], force_file: bool = False) -> Path:
    """Create path if doesn't exist

    Parameters
    ----------
    p : Union[Path, str]
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

    p_create = p if (p.is_dir() or not '.' in p.name) and not force_file else p.parent

    # if file, create parent dir, else create dir
    p_create.mkdir(parents=True, exist_ok=True)

    return p


def flatten_list_list(lst: list[list[T]]) -> list[T]:
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
def as_list(items: Listable[T]) -> list[T]:
    ...


@overload
def as_list(items: dict[Any, Any]) -> list[tuple[Any, Any]]:
    ...


@overload
def as_list(items: str) -> list[str]:
    ...


@overload
def as_list(items: None) -> list[Any]:
    ...


def as_list(
        items: Union[Listable[T], dict[Any, Any], str, None]
) -> Union[list[T], list[tuple[Any, Any]], list[str], list[Any]]:
    """Convert single item or iterable of items to list
    - if items is None, return empty list

    Parameters
    ----------
    items : Union[Listable[T], dict[Any, Any], str, None]
        item, iterable of items, single str, dict, or None

    Returns
    -------
    Union[list[T], list[tuple[Any, Any]], list[str], list[Any]]
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
