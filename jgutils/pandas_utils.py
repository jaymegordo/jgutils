"""
Pandas/DataFrame utils
"""
import re
from typing import *

import pandas as pd
from pandas.io.formats.style import Styler

from jgutils import functions as f


def filter_df(dfall, symbol):
    return dfall[dfall.symbol == symbol].reset_index(drop=True)


def filter_cols(df: pd.DataFrame, expr: str = '.') -> list:
    """Return list of cols in df based on regex expr

    Parameters
    ----------
    df : pd.DataFrame
    expr : str, optional
        default '.'

    Returns
    -------
    list
        list of cols which match expression
    """
    return [c for c in df.columns if re.search(expr, c)]


def select_cols(df: pd.DataFrame, expr: str = '.', include: list = None) -> pd.DataFrame:
    """Filter df cols based on regex

    Parameters
    ----------
    df : pd.DataFrame
    expr : str, optional
        regex expr, by default '.'

    Returns
    -------
    pd.DataFrame
    """
    cols = filter_cols(df, expr)

    # include other cols
    if not include is None:
        include = f.as_list(include)
        cols += include

    return df[cols]


def drop_cols(df: pd.DataFrame, expr: str = '.') -> pd.DataFrame:
    """Filter df cols based on regex

    Parameters
    ----------
    df : pd.DataFrame
    expr : str, optional
        regex expr, by default '.'

    Returns
    -------
    pd.DataFrame
    """
    return df.drop(columns=filter_cols(df, expr))


def clean_cols(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Return cols if they exist in dataframe"""
    cols = [c for c in cols if c in df.columns]
    return df[cols]


def safe_drop(df: pd.DataFrame, cols: Union[str, list], do: bool = True) -> pd.DataFrame:
    """Drop columns from dataframe if they exist

    Parameters
    ----------
    df : pd.DataFrame
    cols : Union[str, list]
        list of cols or str

    Returns
    -------
    pd.DataFrame
        df with cols dropped
    """
    if not do:
        return df

    cols = [c for c in f.as_list(cols) if c in df.columns]
    return df.drop(columns=cols)


def safe_select(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Select df cols if they exist

    Parameters
    ----------
    df : pd.DataFrame
    cols : List[str]

    Returns
    -------
    pd.DataFrame

    """
    cols = [c for c in cols if c in df.columns]
    return df[cols]


def reduce_dtypes(df: pd.DataFrame, dtypes: dict) -> pd.DataFrame:
    """Change dtypes from {select: to}

    Parameters
    ----------
    df : pd.DataFrame
    dtypes : dict
        dict eg {np.float32: np.float16}

    Returns
    -------
    pd.DataFrame
        df with dtypes changed
    """
    dtype_cols = {}
    for d_from, d_to in dtypes.items():
        dtype_cols |= {c: d_to for c in df.select_dtypes(d_from).columns}

    return df.astype(dtype_cols)


def append_list(df: pd.DataFrame, lst: list) -> pd.DataFrame:
    """Append dataframe to list
    - for use with later pd.concat()

    Parameters
    ----------
    df : pd.DataFrame
    lst : list
        lst to add to in-place

    Returns
    -------
    pd.DataFrame
        original unmodified df
    """
    lst.append(df)
    return df


def left_merge(df: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
    """Convenience func to left merge df on index

    Parameters
    ----------
    df : pd.DataFrame
    df_right : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        df with df_right merged
    """
    return df \
        .merge(
            right=df_right,
            how='left',
            left_index=True,
            right_index=True)


def convert_dtypes(df: pd.DataFrame, cols: List[str], _type: Union[str, type]) -> pd.DataFrame:
    """Convert cols to dtype

    Parameters
    ----------
    df : pd.DataFrame
    cols : List[str]
    _type : Union[str, type]
        dtype to convert to

    Returns
    -------
    pd.DataFrame
    """
    m_types = {c: lambda df, c=c: df[c].astype(_type) for c in cols}
    return df.assign(**m_types)


def remove_bad_chars(w: str):
    """Remove any bad chars " : < > | . \\ / * ? in string to make safe for filepaths"""  # noqa
    return re.sub(r'[":<>|.\\\/\*\?]', '', str(w))


def from_snake(s: str):
    """Convert from snake case cols to title"""
    return s.replace('_', ' ').title()


def to_snake(s: str):
    """Convert messy camel case to lower snake case

    Parameters
    ----------
    s : str
        string to convert to special snake case

    Examples
    --------
    """
    s = remove_bad_chars(s).strip()  # get rid of /<() etc
    s = re.sub(r'[\]\[()]', '', s)  # remove brackets/parens
    s = re.sub(r'[\n-]', '_', s)  # replace newline/dash with underscore
    s = re.sub(r'[%]', 'pct', s)
    s = re.sub(r"'", '', s)

    # split on capital letters
    expr = r'(?<!^)((?<![A-Z])|(?<=[A-Z])(?=[A-Z][a-z]))(?=[A-Z])'

    return re \
        .sub(expr, '_', s) \
        .lower() \
        .replace(' ', '_') \
        .replace('__', '_')


def lower_cols(df: Union[pd.DataFrame, List[str]], title: bool = False) -> Union[pd.DataFrame, List[str]]:
    """Convert df columns to snake case and remove bad characters

    Parameters
    ----------
    df : Union[pd.DataFrame, list]
        dataframe or list of strings
    title : bool, optional
        convert back to title case, by default False

    Returns
    -------
    Union[pd.DataFrame, list]
    """
    is_list = False

    if isinstance(df, pd.DataFrame):
        cols = df.columns
    else:
        cols = df
        is_list = True

    func = to_snake if not title else from_snake

    m_cols = {col: func(col) for col in cols}

    if is_list:
        return list(m_cols.values())
    else:
        return df.pipe(lambda df: df.rename(columns=m_cols))


def remove_underscore(df: pd.DataFrame) -> pd.DataFrame:
    """Remove underscores from df columns

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    return df.rename(columns={c: c.replace('_', ' ') for c in df.columns})


def parse_datecols(df: pd.DataFrame, format: dict = None) -> pd.DataFrame:
    """Convert any columns with 'date' or 'time' in header name to datetime"""
    datecols = list(filter(lambda x: any(s in x.lower()
                    for s in ('date', 'time')), df.columns))  # type: List[str]

    df[datecols] = df[datecols].apply(
        pd.to_datetime, errors='coerce', format=format)  # type: ignore

    return df


def reorder_cols(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Reorder df cols with cols first, then remainder

    Parameters
    ----------
    df : pd.DataFrame
    cols : List[str]
        cols to sort first

    Returns
    -------
    pd.DataFrame
    """

    # remove cols not in df
    cols = [c for c in cols if c in df.columns]
    other_cols = [c for c in df.columns if not c in cols]

    return df[cols + other_cols]


def terminal_df(
        df: Union[pd.DataFrame, Styler],
        date_only: bool = True,
        show_na: bool = False,
        pad: bool = False,
        **kw):
    """Display df in terminal with better formatting

    Parameters
    ----------
    df : Union[pd.DataFrame, Styler]
        df or styler object
    date_only : bool, optional
        truncate datetime to date only, by default True
    show_na : bool, optional
        replace na with blank, by default False
    pad : bool, optional
        print space before/after df, by default False
    """
    from tabulate import tabulate

    if isinstance(df, pd.DataFrame):
        # truncate datetime to date only
        if date_only:
            m = {col: lambda x, col=col: x[col].dt.date for col in df.select_dtypes('datetime').columns}
            df = df.assign(**m)
    elif isinstance(df, Styler):
        df = pd.read_html(df.to_html())[0]  # create string format dataframe from stylers html output

    s = tabulate(df, headers=df.columns.tolist(), **kw)

    if not show_na:
        s = s.replace('nan', '   ')

    # print newline before/after df
    if pad:
        s = f'\n{s}\n'

    print(s)
