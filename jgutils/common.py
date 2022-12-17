from abc import ABCMeta
from typing import Any
from typing import List

from joblib import Parallel

from jgutils import IntNone
from jgutils.pretty import PrettyString as PS

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    pass


class DictRepr(object, metaclass=ABCMeta):
    """Class to add better string rep with to_dict"""
    display_keys = []  # type: List[str]
    max_key_len = 40

    def to_dict_str(self):
        """TODO func to convert values of output dicts to string reprs based on dtype"""
        pass

    def truncate(self, text: Any) -> str:
        """Truncate display value to max_key_len

        Parameters
        ----------
        text : str

        Returns
        -------
        str
        """
        try:
            text = str(text)
            return text[:self.max_key_len] + '...' if len(text) > self.max_key_len else text
        except:
            return text
        

    def __str__(self) -> str:
        """Create string representation of self from dict or list of strings"""
        data = []

        if hasattr(self, 'to_dict'):
            m = self.to_dict()
        elif self.display_keys:
            m = self.display_keys
        else:
            m = None

        # convert list to dict of self items
        if isinstance(m, (list, tuple)):
            m = {k: getattr(self, k) for k in m}

        if m:
            data = ['{}={}'.format(k, PS(self.truncate(v), color='yellow')) for k, v in m.items()]

        return '<{}: {}>'.format(
            PS(self.__class__.__name__, color='blue'),
            ', '.join(data))

    def __repr__(self) -> str:
        return str(self)

    def keys(self) -> List[str]:
        return list(self.to_dict().keys())

    def __getitem__(self, key: str) -> Any:
        """Used to call dict() on object
        - NOTE this calls self.to_dict() for every key requested
        - NOTE not actually used yet
        """
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


class ProgressParallel(Parallel):
    """Modified from https://stackoverflow.com/a/61900501/6278428"""

    def __init__(self, use_tqdm: bool = True, total: IntNone = None, *args, **kwargs):
        self._use_tqdm = use_tqdm
        self._total = total
        self.bar_format = '{l_bar}{bar:20}{r_bar}{bar:-20b}'  # limit bar width in terminal
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        with tqdm(
                disable=not self._use_tqdm,
                total=self._total,
                bar_format=self.bar_format) as self._pbar:
            return Parallel.__call__(self, *args, **kwargs)

    def print_progress(self):
        if self._total is None:
            self._pbar.total = self.n_dispatched_tasks

        self._pbar.n = self.n_completed_tasks
        self._pbar.refresh()
