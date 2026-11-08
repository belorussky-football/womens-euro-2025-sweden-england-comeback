"""Visualization helpers: shared style, pitch setup, coordinate conversion and figure text.

Every chart in the project uses the same small palette:

* ``neutral``  - one grey for ordinary events,
* ``accent``   - one colour for shots (and other highlighted, non-goal events);
  ``accent_secondary`` is a lighter tint of it for secondary, de-emphasised marks,
* ``goal``     - the strongest colour, reserved for goals,

on a white background with light grey pitch lines. The accent/goal pair was checked
for colour-vision-deficiency separation (all checks pass, protan ΔE 24.7).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from mplsoccer import Pitch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "figures"

COLORS = {
    "background": "#ffffff",
    "pitch_line": "#c9c8c3",
    "neutral": "#9a9994",
    "neutral_edge": "#2b2b2a",
    "accent": "#2a78d6",
    "accent_secondary": "#7aa9e3",  # lighter tint of accent for secondary sequences
    "goal": "#eb6834",
    "text": "#1b1b1a",
    "text_secondary": "#52514e",
    "text_muted": "#7a7975",
}

# Fixed team colours for every chart that compares the two teams (validated pair:
# CVD protan ΔE 21.6, normal-vision ΔE 32.3, both >= 3:1 contrast on white).
TEAM_COLORS = {"England": "#e34948", "Sweden": "#2a78d6"}

PRESSURE_RING_WIDTH = 2.8  # edge width marking "under pressure" events

FONT_SIZES = {"title": 13.5, "subtitle": 10.5, "label": 9, "legend": 9.5, "footer": 8.5}

DATA_CREDIT = "Data: StatsBomb Open Data · xG: StatsBomb model"


def apply_style() -> None:
    """Set matplotlib defaults used by every project figure."""
    plt.rcParams.update({
        "figure.facecolor": COLORS["background"],
        "axes.facecolor": COLORS["background"],
        "savefig.facecolor": COLORS["background"],
        "font.family": "DejaVu Sans",
        "text.color": COLORS["text"],
    })


def make_pitch(
    figsize: tuple[float, float] = (12, 8),
    axes_rect: tuple[float, float, float, float] = (0.03, 0.07, 0.94, 0.77),
) -> tuple[Pitch, Figure, plt.Axes]:
    """Horizontal StatsBomb pitch on a white background with light grey lines.

    The team of interest attacks left to right (towards x = 120). Note that
    mplsoccer's StatsBomb pitch has y increasing downwards, so y = 0 (the
    attacking team's left touchline) is at the top.

    ``axes_rect`` (left, bottom, width, height in figure fractions) keeps a band
    free above the pitch for the title, subtitle and legend.
    """
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=COLORS["background"],
        line_color=COLORS["pitch_line"],
        linewidth=1.2,
        goal_type="box",
        pad_bottom=6,
        pad_top=2,
    )
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes(axes_rect)
    pitch.draw(ax=ax)
    fig.set_facecolor(COLORS["background"])
    return pitch, fig, ax


def style_line_axes(ax: plt.Axes) -> None:
    """Recessive axes for line/step charts: no top/right spines, light horizontal grid."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(COLORS["pitch_line"])
    ax.tick_params(colors=COLORS["text_secondary"], labelsize=FONT_SIZES["label"])
    ax.grid(axis="y", color=COLORS["pitch_line"], linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)


def to_attacking_frame(x, y):
    """Mirror opponent coordinates into the other team's frame: (120 - x, 80 - y).

    StatsBomb stores each event from the acting team's attacking direction, so
    opponent events must be mirrored before they share a pitch.
    """
    return 120 - np.asarray(x, dtype=float), 80 - np.asarray(y, dtype=float)


def add_title(fig: Figure, title: str, subtitle: str | None = None,
              top: float = 0.965) -> None:
    """Left-aligned title and optional subtitle above the pitch."""
    fig.text(0.04, top, title, ha="left", va="top", fontsize=FONT_SIZES["title"],
             fontweight="bold", color=COLORS["text"])
    if subtitle:
        fig.text(0.04, top - 0.045, subtitle, ha="left", va="top",
                 fontsize=FONT_SIZES["subtitle"], color=COLORS["text_secondary"])


def add_footer(fig: Figure, text: str = DATA_CREDIT, note: str | None = None) -> None:
    """Data credit at the bottom left, with an optional second line (``note``) below it.

    The bottom right is left free for the StatsBomb logo.
    """
    fig.text(0.04, 0.034 if note else 0.025, text, ha="left", va="bottom",
             fontsize=FONT_SIZES["footer"], color=COLORS["text_muted"])
    if note:
        fig.text(0.04, 0.014, note, ha="left", va="bottom", fontsize=FONT_SIZES["footer"],
                 color=COLORS["text_muted"])


def add_attack_arrow(ax: plt.Axes, label: str, y: float = 83.5,
                     x_start: float = 45, x_end: float = 75) -> None:
    """Attacking-direction arrow drawn just below the pitch (data coordinates)."""
    ax.annotate("", xy=(x_end, y), xytext=(x_start, y), annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color=COLORS["text_secondary"], lw=1.4))
    ax.text((x_start + x_end) / 2, y + 1.2, label, ha="center", va="top",
            fontsize=FONT_SIZES["label"] + 0.5, color=COLORS["text_secondary"], clip_on=False)


def label(ax: plt.Axes, text: str, xy: tuple[float, float], xytext: tuple[float, float],
          color: str | None = None, weight: str = "normal", ha: str = "left") -> None:
    """Text label with a thin leader line from ``xytext`` back to the point ``xy``.

    ``ha="left"`` starts the text at ``xytext``; ``ha="right"`` ends it there. The
    leader line leaves from the end of the text nearest to the point, so it never
    crosses the label. Labels may sit outside the pitch (they are not clipped).
    """
    relpos = (1.0, 0.5) if xy[0] > xytext[0] else (0.0, 0.5)
    ax.annotate(
        text, xy=xy, xytext=xytext, ha=ha, va="center", annotation_clip=False,
        fontsize=FONT_SIZES["label"], fontweight=weight, color=COLORS["text"],
        bbox=dict(boxstyle="round,pad=0.25", fc=COLORS["background"], ec="none", alpha=0.9),
        arrowprops=dict(arrowstyle="-", color=color or COLORS["text_muted"], lw=0.8,
                        shrinkA=2, shrinkB=4, relpos=relpos),
        zorder=6,
    )


def save_figure(fig: Figure, name: str, dpi: int = 300) -> Path:
    """Save ``fig`` to ``figures/{name}.png`` and return the path."""
    FIGURES_DIR.mkdir(exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    return path
