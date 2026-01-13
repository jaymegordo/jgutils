"""Matplotlib color utilities with HUSL color space support.

This module provides a seaborn-compatible diverging_palette function
without requiring scipy as a dependency.

HUSL (Human-friendly HSL, also known as HSLuv) is a perceptually uniform
color space. The implementation is based on the husl library.
"""
# ruff: noqa: N806, N803
import math
import operator

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# =============================================================================
# HUSL Color Space Implementation
# Based on seaborn's vendored husl module (MIT License)
# =============================================================================

_M = [
    [3.2406, -1.5372, -0.4986],
    [-0.9689, 1.8758, 0.0415],
    [0.0557, -0.2040, 1.0570]
]

_M_INV = [
    [0.4124, 0.3576, 0.1805],
    [0.2126, 0.7152, 0.0722],
    [0.0193, 0.1192, 0.9505]
]

# D65 illuminant
_REF_X = 0.95047
_REF_Y = 1.00000
_REF_Z = 1.08883
_REF_U = 0.19784
_REF_V = 0.46834
_LAB_E = 0.008856
_LAB_K = 903.3


def _dot_product(a: list[float], b: list[float]) -> float:
    return sum(map(operator.mul, a, b))


def _f(t: float) -> float:
    if t > _LAB_E:
        return math.pow(t, 1.0 / 3.0)
    return 7.787 * t + 16.0 / 116.0


def _f_inv(t: float) -> float:
    if math.pow(t, 3.0) > _LAB_E:
        return math.pow(t, 3.0)
    return (116.0 * t - 16.0) / _LAB_K


def _from_linear(c: float) -> float:
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * math.pow(c, 1.0 / 2.4) - 0.055


def _to_linear(c: float) -> float:
    if c > 0.04045:
        return math.pow((c + 0.055) / 1.055, 2.4)
    return c / 12.92


def _xyz_to_rgb(triple: list[float]) -> list[float]:
    xyz = (_dot_product(row, triple) for row in _M)
    return list(map(_from_linear, xyz))


def _rgb_to_xyz(triple: list[float]) -> list[float]:
    rgbl = list(map(_to_linear, triple))
    return [_dot_product(row, rgbl) for row in _M_INV]


def _xyz_to_luv(triple: list[float]) -> list[float]:
    X, Y, Z = triple
    if X == Y == Z == 0.0:
        return [0.0, 0.0, 0.0]

    varU = (4.0 * X) / (X + (15.0 * Y) + (3.0 * Z))
    varV = (9.0 * Y) / (X + (15.0 * Y) + (3.0 * Z))
    L = 116.0 * _f(Y / _REF_Y) - 16.0

    if L == 0.0:
        return [0.0, 0.0, 0.0]

    U = 13.0 * L * (varU - _REF_U)
    V = 13.0 * L * (varV - _REF_V)
    return [L, U, V]


def _luv_to_xyz(triple: list[float]) -> list[float]:
    L, U, V = triple
    if L == 0:
        return [0.0, 0.0, 0.0]

    varY = _f_inv((L + 16.0) / 116.0)
    varU = U / (13.0 * L) + _REF_U
    varV = V / (13.0 * L) + _REF_V
    Y = varY * _REF_Y
    X = 0.0 - (9.0 * Y * varU) / ((varU - 4.0) * varV - varU * varV)
    Z = (9.0 * Y - (15.0 * varV * Y) - (varV * X)) / (3.0 * varV)
    return [X, Y, Z]


def _luv_to_lch(triple: list[float]) -> list[float]:
    L, U, V = triple
    C = math.sqrt(U * U + V * V)
    hrad = math.atan2(V, U)
    H = math.degrees(hrad)
    if H < 0.0:
        H = 360.0 + H
    return [L, C, H]


def _lch_to_luv(triple: list[float]) -> list[float]:
    L, C, H = triple
    Hrad = math.radians(H)
    U = math.cos(Hrad) * C
    V = math.sin(Hrad) * C
    return [L, U, V]


def _max_chroma(L: float, H: float) -> float:
    hrad = math.radians(H)
    sinH = math.sin(hrad)
    cosH = math.cos(hrad)
    sub1 = math.pow(L + 16, 3.0) / 1560896.0
    sub2 = sub1 if sub1 > 0.008856 else (L / 903.3)
    result = float('inf')

    for row in _M:
        m1, m2, m3 = row
        top = (0.99915 * m1 + 1.05122 * m2 + 1.14460 * m3) * sub2
        rbottom = 0.86330 * m3 - 0.17266 * m2
        lbottom = 0.12949 * m3 - 0.38848 * m1
        bottom = (rbottom * sinH + lbottom * cosH) * sub2

        for t in (0.0, 1.0):
            C = L * (top - 1.05122 * t) / (bottom + 0.17266 * sinH * t)
            if 0.0 < C < result:
                result = C

    return result


def _husl_to_lch(triple: list[float]) -> list[float]:
    H, S, L = triple
    if L > 99.9999999:
        return [100, 0.0, H]
    if L < 0.00000001:
        return [0.0, 0.0, H]

    mx = _max_chroma(L, H)
    C = mx / 100.0 * S
    return [L, C, H]


def _lch_to_husl(triple: list[float]) -> list[float]:
    L, C, H = triple
    if L > 99.9999999:
        return [H, 0.0, 100.0]
    if L < 0.00000001:
        return [H, 0.0, 0.0]

    mx = _max_chroma(L, H)
    S = C / mx * 100.0
    return [H, S, L]


def _lch_to_rgb(l: float, c: float, h: float) -> list[float]:  # noqa: E741
    return _xyz_to_rgb(_luv_to_xyz(_lch_to_luv([l, c, h])))


def _rgb_to_lch(r: float, g: float, b: float) -> list[float]:
    return _luv_to_lch(_xyz_to_luv(_rgb_to_xyz([r, g, b])))


def husl_to_rgb(h: float, s: float, l: float) -> tuple[float, float, float]:  # noqa: E741
    """Convert HUSL (HSLuv) color to RGB.

    Parameters
    ----------
    h : float
        Hue (0-360)
    s : float
        Saturation (0-100)
    l : float
        Lightness (0-100)

    Returns
    -------
    tuple[float, float, float]
        RGB values (0-1, 0-1, 0-1)
    """
    rgb = _lch_to_rgb(*_husl_to_lch([h, s, l]))
    return tuple(np.clip(rgb, 0, 1))  # type: ignore[return-value]


def rgb_to_husl(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Convert RGB color to HUSL (HSLuv).

    Parameters
    ----------
    r, g, b : float
        RGB values (0-1)

    Returns
    -------
    tuple[float, float, float]
        HUSL values (H: 0-360, S: 0-100, L: 0-100)
    """
    result = _lch_to_husl(_rgb_to_lch(r, g, b))
    return (result[0], result[1], result[2])


# =============================================================================
# Palette Functions (seaborn-compatible)
# =============================================================================

def _blend_palette(
        colors: list[tuple[float, float, float]],
        n_colors: int = 6,
        as_cmap: bool = False) -> LinearSegmentedColormap | list[tuple[float, float, float]]:
    """Blend a list of colors into a palette."""
    cmap = LinearSegmentedColormap.from_list('blend', colors)
    if as_cmap:
        return cmap

    rgb_array = cmap(np.linspace(0, 1, n_colors))[:, :3]
    return [tuple(row) for row in rgb_array]  # ty:ignore[invalid-return-type]


def _light_palette(
        color: tuple[float, float, float],
        n_colors: int,
        reverse: bool = False) -> list[tuple[float, float, float]]:
    """Make a sequential palette blending from light to color (HUSL input)."""
    h, s, l = color  # noqa: E741
    rgb = husl_to_rgb(h, s, l)

    # Get gray with reduced saturation at high lightness
    hue, sat, _ = rgb_to_husl(*rgb)
    gray_s, gray_l = 0.15 * sat, 95
    gray = husl_to_rgb(hue, gray_s, gray_l)

    colors = [rgb, gray] if reverse else [gray, rgb]
    return _blend_palette(colors, n_colors)  # type: ignore[return-value]


def _dark_palette(
        color: tuple[float, float, float],
        n_colors: int,
        reverse: bool = False) -> list[tuple[float, float, float]]:
    """Make a sequential palette blending from dark to color (HUSL input)."""
    h, s, l = color  # noqa: E741
    rgb = husl_to_rgb(h, s, l)

    # Get gray with reduced saturation at low lightness
    hue, sat, _ = rgb_to_husl(*rgb)
    gray_s, gray_l = 0.15 * sat, 15
    gray = husl_to_rgb(hue, gray_s, gray_l)

    colors = [rgb, gray] if reverse else [gray, rgb]
    return _blend_palette(colors, n_colors)  # type: ignore[return-value]


def diverging_palette(
        h_neg: float = 240,
        h_pos: float = 10,
        s: float = 75,
        l: float = 50,  # noqa: E741
        sep: int = 1,
        n: int = 6,
        center: str = 'light',
        as_cmap: bool = False) -> LinearSegmentedColormap | list[tuple[float, float, float]]:
    """Make a diverging palette between two HUSL colors.

    This is a seaborn-compatible implementation that doesn't require scipy.

    Parameters
    ----------
    h_neg : float
        Hue for the negative (left) side of the palette (0-360). Default 240 (blue).
    h_pos : float
        Hue for the positive (right) side of the palette (0-360). Default 10 (red).
    s : float
        Saturation for both extents of the map (0-100). Default 75.
    l : float
        Lightness for both extents of the map (0-100). Default 50.
    sep : int
        Size of the intermediate region. Default 1.
    n : int
        Number of colors in the palette (if not returning a cmap). Default 6.
    center : str
        Whether the center should be 'light' or 'dark'. Default 'light'.
    as_cmap : bool
        If True, return a matplotlib LinearSegmentedColormap. Default False.

    Returns
    -------
    LinearSegmentedColormap | list[tuple[float, float, float]]
        Colormap or list of RGB tuples
    """
    palfunc = _dark_palette if center == 'dark' else _light_palette
    n_half = int(128 - (sep // 2))

    neg = palfunc((h_neg, s, l), n_half, reverse=True)
    pos = palfunc((h_pos, s, l), n_half, reverse=False)

    if center == 'light':
        midpoint = [(0.95, 0.95, 0.95)]
    else:
        midpoint = [(0.133, 0.133, 0.133)]

    mid = midpoint * sep
    all_colors = list(neg) + mid + list(pos)

    return _blend_palette(all_colors, n, as_cmap=as_cmap)
