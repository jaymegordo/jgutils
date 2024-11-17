import re
from abc import ABCMeta
from typing import Union


class PrettyDisplayItem(metaclass=ABCMeta):  # noqa: B024
    """Base class for PrettyDict and PrettyString"""
    ansi_codes = {
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'red': '\033[31m',
        'cyan': '\033[36m',
        'reset': '\033[0m'
    }

    colors = list(ansi_codes.keys())[:-1]

    @classmethod
    def get_color(cls, i: int) -> str:
        """Get color for index i"""
        return cls.colors[i % len(cls.colors)]

    def __repr__(self) -> str:
        return self.__str__()

    def print(self):
        print(self.__str__())  # noqa: T201

    def display(self):
        try:
            from IPython.display import display
            display(self)
        except ImportError:
            print(self)  # noqa: T201


class PrettyDict(PrettyDisplayItem):
    """class to print a tree of nested dicts with key colored by ansi escape codes based on depth"""

    def __init__(
            self,
            m: dict | list[dict],
            param: str = '  ',
            max_keys: int = 100,
            max_rows: int = 100,
            color: bool = True):
        """
        Parameters
        ----------
        m : Union[dict, list[dict]]
            dict or list of dicts to display
        param : str, optional
            beginning string that gets multiplied at each depth level, by default '  '
        max_keys : int, optional
            max dict keys to display per level, by default 100
            - NOTE could allow passing max_keys per level
        color : bool, optional
            if False, don't color keys just use structural formatting
        """

        self.m = m
        self.param = param
        self.max_keys = max_keys
        self.max_rows = max_rows

        # list ansi escape codes for each level of depth
        self.ansi_codes_list = list(self.ansi_codes.values())[:-1] * 3

        # don't highlight keys, just use structural formatting only
        from shelton.config import IS_REMOTE
        if not color or IS_REMOTE:
            self.ansi_codes_list = [''] * len(self.ansi_codes_list)
            self.reset = ''
        else:
            self.reset = self.ansi_codes['reset']

    def __str__(self) -> str:
        return self.pretty_print(self.m)

    def pretty_print(self, m: dict | list[dict], depth: int = 0) -> str:
        """Recursively pretty print nested dicts with keys colored by depth

        Parameters
        ----------
        m : Union[dict, list[dict]]
            nested dict or list of dicts to pretty print
        depth : int, optional
            depth of current dict, default 0

        Returns
        -------
        str
            pretty printed nested dict
        """
        ret = ''
        depth_indent = depth * self.param
        lst = self.ansi_codes_list
        reset = self.reset
        i_dict = 0
        i_list = 0

        if isinstance(m, dict):
            for k, v in m.items():

                if isinstance(v, dict):
                    ret += f'{depth_indent}{lst[depth]}{k}{reset}:\n{self.pretty_print(v, depth + 1)}'
                else:
                    # join list of dicts into single value
                    if isinstance(v, list | tuple):
                        v = '\n' + '\n'.join([self.pretty_print(item, depth + 1) for item in v])

                    ret += f'{depth_indent}{lst[depth]}{k}{reset}: {v}\n'

                i_dict += 1
                if i_dict >= self.max_keys:
                    ret += f'{depth_indent}...\n'
                    break

        elif isinstance(m, list | tuple):
            for item in m:
                if isinstance(item, dict):
                    ret += self.pretty_print(item, depth + 1) + '\n'
                else:
                    ret += f'{depth_indent}{item}\n'

                i_list += 1
                if i_list >= self.max_rows:
                    ret += f'{depth_indent}... ({self.max_rows:,.0f}/{len(m):,.0f})\n'
                    break

        else:
            ret += f'{depth_indent}{m}'

        return ret


class PrettyString(PrettyDisplayItem):
    """class to print string with ansi escape code colors"""

    def __init__(
            self,
            s: str,
            color: str = 'green',
            prehighlight: bool = False,
            expr: Union[str, 're.Pattern[str]'] | None = None):
        """
        Parameters
        ----------
        s : str
            string to print
        color : str, optional
            color to use, default 'green'
        prehighlight : bool, optional
            string already contains color codes, just display it, default False
        expr : Optional[Union[str, re.Pattern[str]]], optional
            regex expression to highlight specific substrings, default None
        """
        self.s = s
        self.prehighlight = prehighlight
        self.color = color

        # compile regex expression if passed as string
        if isinstance(expr, str):
            expr = re.compile(expr)

        self.expr = expr  # type: re.Pattern[str] | None

    def __str__(self) -> str:
        if self.prehighlight:
            return self.s
        else:
            return self.pretty_print(self.s)

    def __add__(self, other: str) -> str:
        return str(self) + other

    def __radd__(self, other: str) -> str:
        return other + str(self)

    def _wrap_highlight(self, s: str) -> str:
        """Add ansi escape code colors to string"""
        return f'{self.ansi_codes[self.color]}{s}{self.ansi_codes["reset"]}'

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
        from shelton.config import IS_REMOTE
        if IS_REMOTE:
            return str(s)

        # highlight specific substrings based on regex expression
        if not self.expr is None:
            offset = 0
            for match in self.expr.finditer(s):

                match_str = match.group()
                if not match_str.strip() == '':
                    # replace the match with the highlighted version, using the match start and end
                    color_replace = self._wrap_highlight(match_str)
                    s = s[:match.start() + offset] + color_replace + s[match.end() + offset:]

                    offset += len(color_replace) - len(match_str)

            return s
        else:
            return self._wrap_highlight(s)


# aliases for easy access
PD = PrettyDict
PS = PrettyString
