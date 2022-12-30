"""
General regex string processing functions
"""

import re
from typing import List
from typing import Tuple

import pandas as pd

from jgutils import FloatNone
from jgutils import StrNone
from jgutils.logger import get_log

log = get_log(__name__)

# set of months lowercase, and month abbreviations
MONTHS = set([
    'january', 'february', 'march', 'april', 'may', 'june', 'july',
    'august', 'september', 'october', 'november', 'december', 'jan',
    'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct',
    'nov', 'dec'])

# regex expr to replace any instance of a month with <month>
RE_MONTHS = re.compile(r'\b(' + '|'.join(MONTHS) + r')\b', re.IGNORECASE)

# set of days lowercase, and day abbreviations
DAYS = set([
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
    'sunday', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'])

# regex expr to replace any instance of a day with <day>
RE_DAYS = re.compile(r'\b(' + '|'.join(DAYS) + r')\b', re.IGNORECASE)


def extract_date(text: str) -> StrNone:
    """Try to extract date (eg 'June 30, 2021') in word format from text

    Parameters
    ----------
    text: str
        text to extract date from

    Returns
    -------
    StrNone
        date in word format, or None if no date found
    """
    expr = r'\w+\s+\d{1,2}[,/]\s+\d{4}'
    match = re.search(expr, text)
    if match:
        return match.group()


def sub_dates_placeholder(text: str) -> str:
    """
    Replace any instance of a month or day with <month> or <day>

    Parameters
    ----------
    text : str
        text to replace
    """
    # NOTE final text similarity accuracy is better when using eg "month" instead of "<month>"

    text = RE_MONTHS.sub('month', text)
    text = RE_DAYS.sub('day', text)

    # check for date and replace with date
    date = extract_date(text)
    if date:
        text = re.sub(date, 'precise date', text)

    return text


def remove_non_alpha(text: str) -> str:
    """
    Remove non-alphabetic characters from text

    Parameters
    ----------
    text : str
        text to remove non-alphabetic characters from
    """
    return re.sub(r'[^a-zA-Z\s]', ' ', text)


def remove_non_alphanum(text: str) -> str:
    """Removes non alphanumeric characters from text
    """
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)


def sub_numbers(text: str) -> str:
    """Replaces instances of numbers with 'number'
    """
    return re.sub(r' \d+', ' number', text)


def parse_currency(text: str) -> FloatNone:
    """
    Parse currency from text
    - TODO this will need more testing

    Parameters
    ----------
    text : str
        text to parse currency from
    """

    text = text.replace(',', '').replace('$', '').strip()

    # return single "-" as 0
    expr = r'^-$'
    match = re.search(expr, text)
    if match:
        return 0.0

    # convert parentheses to negative number
    expr = r'\((.+)\)'
    match = re.search(expr, text)
    if match:
        text = re.sub(expr, r'-\1', text)

    # parse currency or number considering dashes, commas, dollar signs, and/or decimals
    expr = r'(\-?\d+\.*\d*)'
    match = re.search(expr, text)
    if match:
        try:
            num = match.groups()[0]
            return float(num)
        except ValueError:
            # error parsing number
            log.warning(f'Error parsing currency: {text}')
            return None


def parse_date(s: str):
    """Parse date from string
    - TODO #265 probably need to test/handle various formats
        - eg 'June 30, 2021' works, but 'June 30,2021' doesn't


    Parameters
    ----------
    s : str
        date string

    Returns
    -------
    datetime
        parsed date
    """
    try:
        return pd.to_datetime(s).to_pydatetime()
    except (ValueError, OverflowError):
        return pd.NaT


def parse_string(s: str) -> StrNone:
    """Check if string value does NOT contain valid currency or date

    Parameters
    ----------
    s : str
        string to parse

    Returns
    -------
    StrNone
        same input string as long as it does not contain currency or date
    """
    exclude_funcs = [parse_currency, parse_date]
    return s if all([pd.isnull(func(s)) for func in exclude_funcs]) and len(s) > 0 else None


def sub_multi(text: str, sub_vals: List[Tuple[str, str]]) -> str:
    """
    Convenience func to perform multiple regex substitutions

    Parameters
    ----------
    text : str
        text to perform substitutions on
    sub_vals : List[Tuple[str, str]]
        list of tuples of (expr, replacement)

    Returns
    -------
    str
        text with substitutions performed

    Examples
    --------
    >>> sub_multi('hello world', [('hello', 'goodbye'), (r'world$', 'universe')])
    """
    for sub_val in sub_vals:
        text = re.sub(sub_val[0], sub_val[1], text)

    return text
