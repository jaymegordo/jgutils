import json
import pickle
import re
from pathlib import Path
from typing import *


def check_path(p: Path) -> Path:
    """Create path if doesn't exist"""
    if isinstance(p, str):
        p = Path(p)

    p_create = p if p.is_dir() or not '.' in p.name else p.parent

    # if file, create parent dir, else create dir
    if not p_create.exists():
        p_create.mkdir(parents=True)

    return p


def clean_dir(p: Path) -> None:
    """Clean all saved models in models dir"""
    if p.is_dir():
        for _p in p.glob('*'):
            _p.unlink()


def save_pickle(obj: object, p: Path, name: str) -> Path:
    """Save object to pickle file

    Parameters
    ----------
    obj : object
        object to save as pickle
    p : Path
        base dir to save in
    name : str
        file name (excluding .pkl)

    Returns
    -------
    Path
        path of saved file
    """
    p = p / f'{name}.pkl'
    with open(check_path(p), 'wb') as file:
        pickle.dump(obj, file)

    return p


def load_pickle(p: Path) -> object:
    """Load pickle from file"""
    with open(p, 'rb') as file:
        return pickle.load(file)


def as_list(items: Any) -> list:
    """Check item(s) is list, make list if not"""
    if not isinstance(items, list):
        items = [items]

    return items


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


def set_self(m: dict, exclude: Union[tuple, str] = ()):
    """Convenience func to assign an object's func's local vars to self"""
    if not isinstance(exclude, tuple):
        exclude = (exclude, )
    exclude += ('__class__', 'self')  # always exclude class/self
    obj = m.get('self', None)  # self must always be in vars dict

    if obj is None:
        return

    for k, v in m.items():
        if not k in exclude:
            setattr(obj, k, v)


def inverse(m: dict) -> dict:
    """Return inverse of dict"""
    return {v: k for k, v in m.items()}


def pretty_dict(m: dict, html: bool = False, prnt: bool = True, bold_keys: bool = False) -> str:
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