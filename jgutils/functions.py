import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from typing import TypeVar

import yaml

SELF_EXCLUDE = ('__class__', 'args', 'kw', 'kwargs')

T = TypeVar('T')


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


def safe_append(lst: list, item: list | Any) -> None:
    """safely append or extend to list

    Parameters
    ----------
    lst : list
        list to append/extend on
    item : list | Any
        item(s) to append/extend
    """
    if isinstance(item, list):
        lst.extend(item)
    else:
        lst.append(item)


def inverse(m: dict) -> dict:
    """Return inverse of dict"""
    return {v: k for k, v in m.items()}


def pretty_dict(m: dict, html: bool = False, prnt: bool = True, bold_keys: bool = False) -> str | None:
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


def nested_dict_update(m1: dict, m2: dict) -> dict:
    """Nested update dict m1 with keys/vals from m2

    Parameters
    ----------
    m1 : dict
    m2 : dict

    Returns
    -------
    dict
        updated dict
    """
    if not isinstance(m1, dict) or not isinstance(m2, dict):
        return m1 if m2 is None else m2
    else:
        # Compute set of all keys in both dictionaries.
        keys = set(m1.keys()) | set(m2.keys())

        return {k: nested_dict_update(m1.get(k), m2.get(k)) for k in keys}


def check_path(p: Path | str) -> Path:
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
    data : dict
        Data to write
    """
    p = check_path(p)

    with p.open('w') as file:
        yaml.dump(data, file, default_flow_style=False)
