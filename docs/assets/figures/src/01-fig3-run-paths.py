"""Mode-specific demo executables, host-side simulation and hardware evidence."""
from theme import (canvas, bilingual, bilingual_in_box, box, arrow, save, tint,
                   SKY, RED, GRAY, CHARCOAL, BLUE_LIGHT, INK, DPI)
from matplotlib.patches import Polygon


def chip(ax, cx, cy, size, zh, en, label_size=13):
    """Symbolic package; graphic pads imply no physical pin or core count."""
    x, y = cx - size / 2, cy - size / 2
    for i in range(6):
        p = (i + 1) * size / 7
        for xs, ys in [([x - 8, x - 2], [y + p, y + p]),
                       ([x + size + 2, x + size + 8], [y + p, y + p]),
                       ([x + p, x + p], [y - 8, y - 2]),
                       ([x + p, x + p], [y + size + 2, y + size + 8])]:
            ax.plot(xs, ys, color=CHARCOAL, lw=2.3, solid_capstyle="butt")
    box(ax, x, y, size, size, SKY, SKY, radius=4, lw=0)
    box(ax, x + 7, y + 7, size - 14, size - 14, SKY, tint(SKY, 0.6), radius=2, lw=0.65)
    bilingual(ax, cx, cy - label_size - 5, zh, en, label_size, "white")


def domain(ax, x, width):
    frame = box(ax, x, 344, width, 183, fill="none", edge=GRAY, radius=9, lw=1)
    frame.set_linestyle((0, (5, 4)))
    frame.set_zorder(0)


def main():
    fig, ax = canvas("三种编译运行的模式区别 —— CPU/SIM/NPU",
                     "Compilation and Execution Modes: CPU / SIM / NPU")

    # One source file. Labels beside the icon leave room for executable outputs.
    ax.add_patch(Polygon([(504, 120), (554, 120), (576, 142), (576, 196), (504, 196)],
                         closed=True, facecolor=RED, edgecolor="none"))
    ax.add_patch(Polygon([(554, 120), (554, 142), (576, 142)],
                         closed=True, facecolor=tint(RED, 0.6), edgecolor="none"))
    ax.plot([526, 517, 526], [151, 160, 169], color="white", lw=1.5)
    ax.plot([554, 563, 554], [151, 160, 169], color="white", lw=1.5)
    ax.plot([544, 536], [148, 173], color="white", lw=1.5)
    ax.plot([517, 545], [184, 184], color=tint(RED, 0.8), lw=1.1)
    bilingual(ax, 601, 134, "算子源码", "Ascend C source", 16, ha="left")

    # The same source is built separately into a demo executable for each mode.
    ax.plot([540, 540], [196, 215], color=INK, lw=1)
    ax.plot([225, 855], [215, 215], color=INK, lw=1)
    for cx, mode in [(225, "CPU"), (540, "SIM"), (855, "NPU")]:
        arrow(ax, [(cx, 215), (cx, 266)], INK)
        bilingual(ax, cx + 18, 220, f"{mode} 编译", f"{mode} build", 12, GRAY, ha="left")
        # Matplotlib linewidth uses pt: convert the requested 2 px at output DPI.
        box(ax, cx - 94, 273, 188, 50, "#FAFAFA", RED, radius=4, lw=2 * 72 / DPI)
        bilingual_in_box(ax, cx - 94, 273, 188, 50, "可执行程序 demo", "Executable demo", 13, INK)
        arrow(ax, [(cx, 325), (cx, 360)], INK)

    for left in (78, 393, 708):
        domain(ax, left, 294)
    chip(ax, 225, 412, 80, "处理器", "CPU")

    # SIM is a model of the target, displayed inside a host-side monitor.
    box(ax, 463, 361, 154, 77, CHARCOAL, CHARCOAL, radius=5, lw=0)
    box(ax, 470, 368, 140, 61, "white", "white", radius=2, lw=0)
    target = box(ax, 494, 374, 92, 49, BLUE_LIGHT, SKY, radius=3, lw=0.9)
    target.set_linestyle((0, (3, 3)))
    bilingual_in_box(ax, 494, 374, 92, 49, "目标模型", "NPU model", 12, SKY)
    box(ax, 535, 438, 10, 10, CHARCOAL, CHARCOAL, radius=0, lw=0)
    box(ax, 511, 448, 58, 3, CHARCOAL, CHARCOAL, radius=1, lw=0)

    # Generic accelerator card; no claim about a particular product's layout.
    box(ax, 777, 378, 156, 78, CHARCOAL, CHARCOAL, radius=5, lw=0)
    ax.plot([770, 770, 779], [372, 465, 465], color=GRAY, lw=1.8)
    for i in range(9):
        ax.plot([798 + i * 11, 798 + i * 11], [456, 464], color=GRAY, lw=2.5,
                solid_capstyle="butt")
    chip(ax, 855, 417, 60, "加速器", "NPU", 11)
    for xx in (788, 914):
        for yy in (389, 405, 440):
            box(ax, xx, yy, 8, 4, "#AAB2B9", "#AAB2B9", radius=1, lw=0)

    for cx, zh, en in [(225, "CPU 模式", "CPU mode"),
                       (855, "真机模式", "NPU mode")]:
        bilingual(ax, cx, 475, zh, en, 14, gap=20)

    bilingual(ax, 540, 452, "在主机 CPU 上运行仿真模型",
              "Simulation model on host CPU", 11, gap=17)
    bilingual(ax, 540, 490, "无需本地物理 NPU", "No local NPU required", 10, GRAY, gap=16)

    scopes = [(225, "CPU域功能调试", "CPU-domain functional debugging"),
              (540, "目标模型中的功能与性能观察", "Model function / performance"),
              (855, "真实设备功能验证与性能测量", "Hardware checks / performance tests")]
    for cx, zh, en in scopes:
        bilingual(ax, cx, 533, zh, en, 12, gap=18)
    save(fig, __file__)


if __name__ == "__main__":
    main()
