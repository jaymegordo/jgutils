
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
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


def flatten_list_list(lst: List[List[T]]) -> List[T]:
    """Flatten single level nested list of lists

    Parameters
    ----------
    lst : List[list]

    Returns
    -------
    list
        flattened list
    """
    return [item for sublist in lst for item in sublist]


@overload
def as_list(items: Listable[T]) -> List[T]:
    ...


@overload
def as_list(items: Dict[Any, Any]) -> List[Tuple[Any, Any]]:
    ...


@overload
def as_list(items: str) -> List[str]:
    ...


@overload
def as_list(items: None) -> List[Any]:
    ...


def as_list(
        items: Union[Listable[T], Dict[Any, Any], str, None]
) -> Union[List[T], List[Tuple[Any, Any]], List[str], List[Any]]:
    """Convert single item or iterable of items to list
    - if items is None, return empty list

    Parameters
    ----------
    items : Union[Listable[T], Dict[Any, Any], str, None]
        item, iterable of items, single str, dict, or None

    Returns
    -------
    Union[List[T], List[Tuple[Any, Any]], List[str], List[Any]]
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
