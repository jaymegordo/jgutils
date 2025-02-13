from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections import defaultdict
    from collections.abc import Sequence

    import pandas as pd
    from pandas.io.formats.style import Styler as _Styler
    from pandas.io.formats.style_render import CSSList
    from pandas.io.formats.style_render import CSSStyles

    class Styler(_Styler):
        data: pd.DataFrame
        index: pd.Index
        columns: pd.Index
        table_styles: CSSStyles | None
        table_attributes: str | None
        hidden_rows: Sequence[int]
        hidden_columns: Sequence[int]
        ctx: defaultdict[tuple[int, int], CSSList]

        def _compute(self):
            pass
