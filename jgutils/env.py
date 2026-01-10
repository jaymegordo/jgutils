"""
Simple file to define environments without importing config.py first
- Mostly used for scripts which need env choices
"""
from jgutils.helpers.enums import StrEnum


class Env(StrEnum):
    """Environment enum
    - TODO not used everywhere yet
    """
    TEST = 'test'
    LOCAL = 'local'
    DEV = 'dev'
    PROD = 'prod'
