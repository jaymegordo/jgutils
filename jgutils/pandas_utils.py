"""
Pandas/DataFrame utils
"""
import re
from typing import *

import pandas as pd

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
