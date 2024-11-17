from abc import ABCMeta
from typing import Any

from jgutils.pretty import PrettyString as PS


class DictRepr(metaclass=ABCMeta):  # noqa: B024
    """Class to add better string rep with to_dict"""
    display_keys = []  # type: list[str]
    max_key_len = 40

    def truncate(self, text: str) -> str:
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
        if isinstance(m, list | tuple):
            m = {k: getattr(self, k) for k in m}

        if m:
            data = ['{}={}'.format(k, PS(self.truncate(v), color='yellow')) for k, v in m.items()]

        return '<{}: {}>'.format(
            PS(self.__class__.__name__, color='blue'),
            ', '.join(data))

    def __repr__(self) -> str:
        return str(self)

    def keys(self) -> list[str]:
        return list(self.to_dict().keys())

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        """Used to call dict() on object
        - NOTE this calls self.to_dict() for every key requested
        - NOTE not actually used yet
        """
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        return self.to_dict().get(key, default)
