"""Shared Matplotlib layout, palette and bilingual typography; coordinates in px."""
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local" / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.textpath import TextPath

WIDTH, HEIGHT, DPI = 1080, 600, 100
TITLE_SIZE, TITLE_EN_SIZE = 24, 18
WATERMARK = "AI Kernel 101 | From Hello World to Flash Attention in Ascend C @LambertLiu"
WATERMARK_COLOR = "#CFD3D7"
# Sampled from the two flat swatches in the author's color.png.
RED, SKY = "#C00000", "#00B0F0"
INK, CHARCOAL = "#20262C", "#3C4650"
GRAY, LINE = "#59636D", "#D7DDE2"


def tint(color, white=0.85):
    """Derive accents from the two swatches instead of introducing extra hues."""
    rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(c * (1 - white) + 255 * white):02X}" for c in rgb)


BLUE_LIGHT, RED_LIGHT = tint(SKY, 0.91), tint(RED, 0.92)


def setup_font():
    """Chinese titles use STZhongsong; body uses YaHei; English uses Cascadia."""
    roles = {"TITLE_CHINESE": "STZhongsong", "CHINESE": "Microsoft YaHei",
             "ENGLISH": "Cascadia Code"}
    local_font = ROOT / ".local" / "figure-fonts" / "CascadiaCode-Regular.ttf"
    if local_font.exists():
        font_manager.fontManager.addfont(local_font)
    names = {f.name for f in font_manager.fontManager.ttflist}
    for role, default in roles.items():
        override = os.environ.get(f"FIGURE_{role}_FONT")
        if override:
            font_manager.fontManager.addfont(override)
            roles[role] = font_manager.FontProperties(fname=override).get_name()
        elif default not in names:
            raise RuntimeError(f"Install {default} or set FIGURE_{role}_FONT to its file path.")
    plt.rcParams.update({"font.family": [roles["ENGLISH"], roles["CHINESE"]],
                         "axes.unicode_minus": False, "svg.fonttype": "path",
                         "svg.hashsalt": "ai-kernel-101", "text.hinting": "none",
                         "figure.facecolor": "white", "savefig.facecolor": "white"})
    return roles


def canvas(title_zh, title_en):
    fonts = setup_font()
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI)
    ax = fig.add_axes((0, 0, 1, 1), xlim=(0, WIDTH), ylim=(HEIGHT, 0))
    ax.set_axis_off()
    ax._figure_fonts = fonts
    text(ax, WIDTH / 2, 43, title_zh, TITLE_SIZE, ha="center", role="title")
    text(ax, WIDTH / 2, 78, title_en, TITLE_EN_SIZE, GRAY, ha="center")
    for y in (10, HEIGHT - 24):
        text(ax, WIDTH / 2, y, WATERMARK, 10, WATERMARK_COLOR, ha="center")
    return fig, ax


def text(ax, x, y, value, size=16, color=INK, weight="normal", ha="left", va="top", role="body"):
    fonts = ax._figure_fonts
    family = [fonts["ENGLISH"]]
    if re.search(r"[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]", value):
        family.append(fonts["TITLE_CHINESE" if role == "title" else "CHINESE"])
    return ax.text(x, y, value, fontsize=size * 72 / DPI, color=color,
                   fontfamily=family, fontweight=weight, ha=ha, va=va, linespacing=1.45)


def bilingual(ax, x, y, zh, en, size=16, color=INK, ha="center", gap=None):
    """Chinese above English; identical nominal font sizes for the pair."""
    gap = size + 6 if gap is None else gap
    return (text(ax, x, y, zh, size, color, ha=ha),
            text(ax, x, y + gap, en, size, color, ha=ha))


def bilingual_in_box(ax, x, y, w, h, zh, en, size=16, color=INK, line_gap=7):
    """Center the two lines as one group, using glyph ink bounds, not line leading."""
    labels = [text(ax, x + w / 2, 0, value, size, color, ha="center", va="baseline")
              for value in (zh, en)]
    bounds = [TextPath((0, 0), label.get_text(), size=size,
                       prop=label.get_fontproperties()).get_extents() for label in labels]
    top = y + (h - bounds[0].height - line_gap - bounds[1].height) / 2
    for label, ink in zip(labels, bounds):
        label.set_y(top + ink.y1)
        top += ink.height + line_gap
    return tuple(labels)


def box(ax, x, y, w, h, fill="white", edge=LINE, radius=10, lw=1):
    patch = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={radius}",
                          facecolor=fill, edgecolor=edge, linewidth=lw)
    ax.add_patch(patch)
    return patch


def arrow(ax, points, color=GRAY, dashed=False):
    if len(points) > 2:
        ax.plot(*zip(*points[:-1]), color=color, lw=1.1,
                linestyle=(0, (4, 3)) if dashed else "-", solid_capstyle="round")
    ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>",
                                mutation_scale=10, color=color, lw=1.1,
                                linestyle=(0, (4, 3)) if dashed else "-",
                                shrinkA=0, shrinkB=0))


def save(fig, script):
    """Keep exact dimensions; embed SVG glyph outlines, not font files."""
    output = Path(__file__).resolve().parents[1] / "gen"
    output.mkdir(parents=True, exist_ok=True)
    stem = Path(script).stem
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in fig.axes:
        for label in ax.texts:
            bounds = label.get_window_extent(renderer)
            if bounds.x0 < 0 or bounds.y0 < 0 or bounds.x1 > WIDTH or bounds.y1 > HEIGHT:
                raise ValueError(f"Text outside canvas: {label.get_text()}")
    for extension in ("png", "svg"):
        path = output / f"{stem}.{extension}"
        metadata = {"Software": "AI Kernel 101 / Matplotlib"} if extension == "png" else {
            "Creator": "AI Kernel 101 / Matplotlib", "Date": None}
        fig.savefig(path, dpi=DPI, metadata=metadata)
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines())
                            + "\n", encoding="utf-8")
        print(path)
    plt.close(fig)
