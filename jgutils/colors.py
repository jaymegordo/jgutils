"""Matplotlib color utilities."""
import colorsys

from matplotlib.colors import LinearSegmentedColormap


def diverging_palette(
        h_neg: float = 240,
        h_pos: float = 10,
        s: float = 75,
        l: float = 50,  # noqa: E741
        sep: int = 1,
        n: int = 6,
        center: str = 'light',
        as_cmap: bool = False) -> LinearSegmentedColormap | list[tuple[float, float, float]]:
    """Create a diverging color palette (seaborn replacement).

    Creates a palette that diverges from a central color to two different
    end colors, specified by their hue values.

    Parameters
    ----------
    h_neg : float
        Hue for the negative (left) side of the palette (0-360). Default 240 (blue).
    h_pos : float
        Hue for the positive (right) side of the palette (0-360). Default 10 (red).
    s : float
        Saturation for the end colors (0-100). Default 75.
    l : float
        Lightness for the end colors (0-100). Default 50.
    sep : int
        Size of the separation zone in the center. Default 1.
    n : int
        Number of colors in the palette. Default 6.
    center : str
        Whether the center should be 'light' or 'dark'. Default 'light'.
    as_cmap : bool
        If True, return a matplotlib LinearSegmentedColormap. Default False.

    Returns
    -------
    LinearSegmentedColormap | list[tuple[float, float, float]]
        Colormap or list of RGB tuples
    """

    def hsl_to_rgb(h: float, s: float, l: float) -> tuple[float, float, float]:  # noqa: E741
        """Convert HSL (0-360, 0-100, 0-100) to RGB (0-1, 0-1, 0-1)."""
        h_norm = h / 360.0
        s_norm = s / 100.0
        l_norm = l / 100.0
        return colorsys.hls_to_rgb(h_norm, l_norm, s_norm)

    # Center color
    center_l = 95 if center == 'light' else 15
    center_color = hsl_to_rgb(0, 0, center_l)

    # End colors
    neg_color = hsl_to_rgb(h_neg, s, l)
    pos_color = hsl_to_rgb(h_pos, s, l)

    # Build gradient: neg -> center -> pos
    half = n // 2
    colors = []

    # Negative side (saturated to center)
    for i in range(half):
        t = i / max(half - 1, 1)
        r = neg_color[0] + t * (center_color[0] - neg_color[0])
        g = neg_color[1] + t * (center_color[1] - neg_color[1])
        b = neg_color[2] + t * (center_color[2] - neg_color[2])
        colors.append((r, g, b))

    # Center (add separation)
    for _ in range(sep):
        colors.append(center_color)

    # Positive side (center to saturated)
    for i in range(half):
        t = i / max(half - 1, 1)
        r = center_color[0] + t * (pos_color[0] - center_color[0])
        g = center_color[1] + t * (pos_color[1] - center_color[1])
        b = center_color[2] + t * (pos_color[2] - center_color[2])
        colors.append((r, g, b))

    if as_cmap:
        return LinearSegmentedColormap.from_list('diverging', colors, N=256)

    return colors
