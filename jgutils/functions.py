import json
import re
import sys
from pathlib import Path
from typing import Any

from typing import Iterable

from typing import Optional
from typing import TypeVar
from typing import Union

import yaml

from jgutils.typing import DictAny
from jgutils.typing import Listable

SELF_EXCLUDE = ('__class__', 'args', 'kw', 'kwargs')

T = TypeVar('T')


def as_list(items: Optional[Listable[T]]) -> list[T]:
    """Convert single item or list/tuple of items to list
    - if items is None, return empty list

    Parameters
    ----------
    items : Listable[T]

    Returns
    -------
    list[T]
    """
    if items is None:
        return []

    if not isinstance(items, list):
        if isinstance(items, tuple):
            items = list(items)
        else:
            items = [items]

    return items


def flatten_list_list(lst: Iterable[list]) -> list:
    """Flatten single level nested list of lists

    Parameters
    ----------
    lst : Iterable[list]

    Returns
    -------
    list
        flattened list
    """
    return [item for sublist in lst for item in sublist]


def safe_append(lst: list, item: Union[list, Any]) -> None:
    """safely append or extend to list

    Parameters
    ----------
    lst : list
        list to append/extend on
    item : Union[list, Any]
        item(s) to append/extend
    """
    if isinstance(item, list):
        lst.extend(item)
    else:
        lst.append(item)


def set_self(exclude: Optional[Union[tuple, str]] = None, include: Optional[DictAny] = None):
    """Convenience func to assign an object's func's local vars to self"""
    fr = sys._getframe(1)
    # code = fr.f_code
    m = fr.f_locals
    obj = m.pop('self')

    # args = code.co_varnames[:code.co_argcount + code.co_kwonlyargcount]
    # obj = fr.f_locals[args[0]]  # self

    # ns = getattr(obj, '__slots__', args[1:])  # type: ignore
    # m = {n: fr.f_locals[n] for n in ns}  # vars() dict, excluding self

    if include:
        m |= include

    if not isinstance(exclude, tuple):
        if exclude is None:
            exclude = ()

        exclude = (exclude,)

    exclude += SELF_EXCLUDE  # always exclude class

    for k, v in m.items():
        if not k in exclude:
            setattr(obj, k, v)


def inverse(m: dict) -> dict:
    """Return inverse of dict"""
    return {v: k for k, v in m.items()}


def pretty_dict(m: dict, html: bool = False, prnt: bool = True, bold_keys: bool = False) -> Optional[str]:
    """Print pretty dict converted to newlines
    Paramaters
    ----
    m : dict
    html: bool
        Use <br> instead of html
    prnt : bool
        print, or return formatted string
    bold_keys : bool
        if true, add ** to dict keys to bold for discord msg

    Returns
    -------
    str
        'Key 1: value 1
        'Key 2: value 2"
    """

    def _bold_keys(m):
        """Recursively bold all keys in dict"""
        if isinstance(m, dict):
            return {f'**{k}**': _bold_keys(v) for k, v in m.items()}
        else:
            return m

    if bold_keys:
        m = _bold_keys(m)

    s = json.dumps(m, indent=4, ensure_ascii=False)
    newline_char = '\n' if not html else '<br>'

    # remove these chars from string
    remove = '}{\'"[]'
    for char in remove:
        s = s.replace(char, '')

        # .replace(', ', newline_char) \
    s = s \
        .replace(',\n', newline_char)

    # remove leading and trailing newlines
    s = re.sub(r'^[\n]', '', s)
    s = re.sub(r'\s*[\n]$', '', s)

    # remove blank lines (if something was a list etc)
    # s = re.sub(r'(\n\s+)(\n)', r'\2', s)

    if prnt:
        print(s)
    else:
        return s


def nested_dict_update(m1: DictAny, m2: DictAny) -> DictAny:
    """Nested update dict m1 with keys/vals from m2

    Parameters
    ----------
    m1 : DictAny
    m2 : DictAny

    Returns
    -------
    DictAny
        updated dict
    """
    if not isinstance(m1, dict) or not isinstance(m2, dict):
        return m1 if m2 is None else m2
    else:
        # Compute set of all keys in both dictionaries.
        keys = set(m1.keys()) | set(m2.keys())

        return {k: nested_dict_update(m1.get(k), m2.get(k)) for k in keys}


def check_path(p: Union[Path, str]) -> Path:
    """Create path if doesn't exist

    Returns
    -------
    Path
        Path checked
    """
    p = Path(p)

    if p.exists():
        return p

    p_create = p if p.is_dir() or not '.' in p.name else p.parent

    # if file, create parent dir, else create dir
    p_create.mkdir(parents=True, exist_ok=True)

    return p


def load_yaml(p: Path) -> Any:
    """Load yaml from file

    Parameters
    ----------
    p : Path
        Path to yaml file

    Returns
    -------
    Any
        yaml object
    """
    with p.open('r', encoding='utf-8') as file:
        return yaml.full_load(file)


def write_yaml(p: Path, data: dict):
    """Write Yaml

    Parameters
    ----------
    p : Path
        Path to write to
    data : DictAny
        Data to write
    """
    p = check_path(p)

    with p.open('w') as file:
        yaml.dump(data, file, default_flow_style=False)
