"""
Create a custom cell magic function %%prof to display pretty dataframe of pstats results

Examples
--------
>>> %load_ext scripts.profile

>>> %%prof -h 20 -s cum_time (arguments are optional)
    a = 0
    for i in range(10):
        a += i
"""

import profile
import pstats
from typing import TYPE_CHECKING
from typing import List
from typing import Union

import pandas as pd
from IPython.core.magic import Magics
from IPython.core.magic import cell_magic
from IPython.core.magic import magics_class
from seaborn import diverging_palette

from jgutils import config as cf
from jgutils import re_utils as ru
from jgutils.pretty import PrettyDict as PD
from jgutils.typing import StrNone

if TYPE_CHECKING:
    from pandas.io.formats.style import Styler


_cmap = diverging_palette(240, 10, sep=10, n=21, as_cmap=True, center='dark')


def format_cell(bg, t='inherit'):
    return f'background-color: {bg};color: {t};'


def bg(
        style: 'Styler',
        subset: Union[List[str], None] = None,
        higher_better: bool = True,
        axis: int = 0) -> 'Styler':
    """Show style with highlights per column"""
    if subset is None:
        subset = style.data.columns

    cmap = _cmap.reversed() if higher_better else _cmap

    return style \
        .background_gradient(cmap=cmap, subset=subset, axis=axis)


def highlight_max_col(
        style: 'Styler',
        col_max: str,
        col_hl: str,
        color: str = '#F8696B',
        t_color: str = 'inherit') -> 'Styler':
    """Highlight max value in column"""

    df = style.data
    idx_max = df[col_max].idxmax()
    subset = pd.IndexSlice[idx_max, col_hl]

    return style \
        .apply(lambda x: pd.Series([format_cell(color, t_color)], index=x.index), subset=subset, axis=1)


@magics_class
class ProfileMagic(Magics):

    @cell_magic
    def prof(self, params: str = '', cell: StrNone = None):

        # opts = eg {'h': ['5']}
        opts, arg_str = self.parse_options(
            params,
            'h:s:',
            list_all=True,
            posix=False)

        # get or set default options
        m_opts = dict(
            head=int(opts.get('h', [20])[0]),
            sort=opts.get('s', ['cum_time'])[0]
        )

        code = self.shell.transform_cell(cell)
        ns = self.shell.user_ns
        profiler = profile.Profile().runctx(code, ns, ns)
        stats = pstats.Stats(profiler)

        return show_df_stats(stats=stats, **m_opts)


def show_df_stats(stats: pstats.Stats, head: int = 20, sort: str = 'cum_time') -> 'Styler':
    """Show styled dataframe of pstats data

    Parameters
    ----------
    stats : pstats.Stats
    head : int, optional
        show first n rows, default 20
    sort : str, optional
        sort column, default 'cum_time'

    Returns
    -------
    Styler
        dataframe with values highlighted
    """
    exclude = ('profile', 'exec')

    data = []
    for k, v in stats.stats.items():

        # remove long filename prefixes
        sub_vals = [
            (r'.*/lib/', ''),
            (r'.*site-packages/', ''),
            (f'.*{cf.p_root.parent.name}/', ''),
            # (f'.*{cf.p_proj.name}/', ''),
        ]

        module = ru.sub_multi(k[0], sub_vals)
        func = k[2]

        if not any(item in exclude for item in (module, func)):
            m = dict(
                n_calls=v[0],
                per_call=v[2] / max(v[0], 1),
                cum_time=v[3],
                tot_time=v[2],
                module=module,
                func=func,
                lineno=k[1],
            )

            data.append(m)

    df = pd.DataFrame(data) \
        .sort_values(by=sort, ascending=False) \
        .reset_index(drop=True)

    n_funcs = len(df)
    n_calls = df.n_calls.sum()
    tot_time = df.cum_time.max()

    row_most = df.loc[df.n_calls.idxmax()]
    msg_most = f'{row_most.module}::{row_most.func} ({row_most.n_calls:,.0f})'

    row_slowest = df.loc[df.tot_time.idxmax()]
    msg_slowest = f'{row_slowest.module}::{row_slowest.func} ({row_slowest.tot_time:,.3f}s)'

    m_result = dict(
        total_funcs=f'{n_funcs:,.0f}',
        total_calls=f'{n_calls:,.0f}',
        total_time=f'{tot_time:.3f}s',
        most_calls=msg_most,
        slowest_func=msg_slowest)

    # display summary results dict
    PD(m_result).display()

    # set column display formats
    m_fmt = {k: '{:.03f}' for k in ('tot_time', 'cum_time', 'per_call')} | dict(n_calls='{:,.0f}')

    return df.head(head).style \
        .pipe(
            bg,
            subset=['tot_time', 'n_calls'],
            higher_better=False) \
        .pipe(highlight_max_col, col_max='tot_time', col_hl='func', t_color='black') \
        .pipe(highlight_max_col, col_max='n_calls', col_hl='func', color='#ffbf7a', t_color='black') \
        .format(m_fmt) \
        .format(escape='html', subset=['module', 'func'])


def load_ipython_extension(ipython):
    """Load the extension in IPython"""
    ipython.register_magics(ProfileMagic)
