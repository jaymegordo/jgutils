import enum
from collections.abc import ItemsView
from enum import Enum
from enum import EnumType
from enum import IntEnum as _IntEnum
from enum import StrEnum as _StrEnum
from enum import property as enum_property
from typing import Any


class ChoicesType(EnumType):

    def __new__(cls, classname: str, bases: tuple, classdict: dict, **kw) -> Enum:
        """Mostly copied from django ChoicesType"""
        labels = []

        for key in classdict._member_names:
            value = classdict[key]
            label = key.replace('_', ' ').title()
            labels.append(label)
            dict.__setitem__(classdict, key, value)

        cls = super().__new__(cls, classname, bases, classdict, **kw)

        for member, label in zip(cls.__members__.values(), labels, strict=False):
            member._label_ = label

        return enum.unique(cls)

    @property
    def choices(cls) -> list[tuple[Any, str]]:
        """Return tuple of vale, label to create choices list for django models"""
        return [(member.value, member.label) for member in cls]


class _BaseEnum(enum.Enum):
    """Base enum class to add utility methods"""

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}.{self._name_}'

    @classmethod
    def as_dict(cls) -> dict[str, str]:
        """Return enum as dict"""
        return {e.name: e.value for e in cls}

    @classmethod
    def inverse_dict(cls) -> dict[str, str]:
        """Return inverse dict of enum"""
        return {e.value: e.name for e in cls}

    @classmethod
    def items(cls) -> ItemsView[str, str]:
        """Return dict items"""
        return cls.as_dict().items()

    @classmethod
    def keys(cls) -> set[str]:
        """Return self.keys as set"""
        return {e.name for e in cls}

    @classmethod
    def values(cls) -> list[str]:
        """Return self.values as list"""
        return [e.value for e in cls]

    @classmethod
    def get(
            cls,
            key: str,
            default: 'str | None' = None) -> 'str | None':
        """Get enum value"""
        return cls.as_dict().get(key, default)

    @classmethod
    def get_inverse(
            cls,
            key: str,
            default: 'str | None' = None) -> 'str | None':
        """Get inverse enum value"""
        return cls.inverse_dict().get(key, default)


class BaseEnum(_BaseEnum, metaclass=ChoicesType):
    """Base enum class to add django-like choices, and other utility methods"""

    @enum_property
    def label(self) -> str:
        return self._label_


class IntEnum(BaseEnum, _IntEnum):
    """IntEnum"""

    pass


class StrEnum(BaseEnum, _StrEnum):
    """Enum to allow equality check with any case string"""

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        """NOTE important to override both __hash__ and __eq__ in SAME class,
        or else class will be marked as "unhashable"
        """
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:  # noqa: ANN401
        """Check equality with any case string"""
        return str(self.value).lower() == str(other).lower()
