import json
import re
import sys
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

from jgutils import DictAny
from jgutils import Listable

SELF_EXCLUDE = ('__class__', 'args', 'kw', 'kwargs')

T = TypeVar('T')


def as_list(items: Listable[T]) -> List[T]:
    """Check item(s) is list, make list if not"""
    if not isinstance(items, list):
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


class PrettyDict():
    """class to print a tree of nested dicts with key colored by ansi escape codes based on depth"""

    def __init__(
            self,
            m: Union[DictAny, List[DictAny]],
            max_keys: int = 100):
        """

        Parameters
        ----------
        m : Union[DictAny, List[DictAny]]
            dict or list of dicts to display
        max_keys : int, optional
            max dict keys to display per level, by default 100
            - NOTE could allow passing max_keys per level

        """

        self.m = m
        self.max_keys = max_keys

        self.ansi_colors = {
            'green': '\033[32m',
            'blue': '\033[34m',
            'yellow': '\033[33m',
            'red': '\033[31m',
            'cyan': '\033[36m',
            'reset': '\033[0m'
        }

        # list ansi escape codes for each level of depth
        self.ansi_colors_list = list(self.ansi_colors.values())

    def __str__(self) -> str:
        return self.pretty_print(self.m)

    def __repr__(self):
        return self.__str__()

    def print(self):
        print(self.__str__())

    def display(self):
        from IPython.display import display
        display(self)

    def pretty_print(self, m: Union[Dict[str, Any], List[Dict[str, Any]]], depth: int = 0) -> str:
        """Recursively pretty print nested dicts with keys colored by depth

        Parameters
        ----------
        m : Union[Dict[str, Any], List[Dict[str, Any]]]
            nested dict or list of dicts to pretty print
        depth : int, optional
            depth of current dict, default 0

        Returns
        -------
        str
            pretty printed nested dict
        """
        ret = ''
        depth_indent = depth * '  '
        lst = self.ansi_colors_list
        reset = self.ansi_colors['reset']
        i = 0

        if isinstance(m, dict):
            for k, v in m.items():

                if isinstance(v, dict):
                    ret += f'{depth_indent}{lst[depth]}{k}{reset}:\n{self.pretty_print(v, depth + 1)}'
                else:
                    # join list of dicts into single value
                    if isinstance(v, list):
                        v = '\n' + '\n'.join([self.pretty_print(item, depth + 1) for item in v])

                    ret += f'{depth_indent}{lst[depth]}{k}{reset}: {v}\n'

                i += 1
                if i >= self.max_keys:
                    ret += f'{depth_indent}...\n'
                    break

        elif isinstance(m, list):
            for item in m:
                if isinstance(item, dict):
                    ret += self.pretty_print(item, depth + 1) + '\n'
                else:
                    ret += f'{depth_indent}{item}\n'

        else:
            ret += f'{depth_indent}{m}'

        return ret


class PrettyString():
    """class to print string with ansi escape code colors"""

    def __init__(self, s: str, color: str = 'green', prehighlight: bool = False):
        self.s = s
        self.prehighlight = prehighlight
        self.color = color
        self.ansi_codes = {
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'red': '\033[31m',
            'cyan': '\033[36m',
            'reset': '\033[0m'
        }

    def __str__(self):
        if self.prehighlight:
            return self.s
        else:
            return self.pretty_print(self.s)

    def __repr__(self):
        return self.__str__()

    def print(self):
        print(self)

    def pretty_print(self, s: str) -> str:
        """Print a string with ansi escape code colors

        Parameters
        ----------
        s : str
            string to print
        color : str, optional
            color to use, default 'green'

        Returns
        -------
        str
            string with ansi escape code colors
        """
        return f'{self.ansi_codes[self.color]}{s}{self.ansi_codes["reset"]}'
