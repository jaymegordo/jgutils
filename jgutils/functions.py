import json
import re
import sys
from typing import *

SELF_EXCLUDE = ('__class__', 'args', 'kw', 'kwargs')


def as_list(items: Any) -> List[Any]:
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


def set_self(exclude: Optional[Union[tuple, str]] = None, include: Optional[Union[dict, None]] = None):
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
