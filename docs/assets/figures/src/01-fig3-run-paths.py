"""Mode-specific demo executables, host-side simulation and hardware evidence."""
from theme import (canvas, bilingual, bilingual_in_box, box, arrow, save, tint,
                   SKY, RED, GRAY, CHARCOAL, BLUE_LIGHT, INK, DPI)
from matplotlib.patches import Polygon


def chip(ax, cx, cy, size, zh, en, label_size=23):
    """Symbolic package, with no physical pin or core-count assertion."""
    x, y = cx - size / 2, cy - size / 2
    for i in range(6):
        p = (i + 1) * size / 7
        for xs, ys in [([x - 14, x - 4], [y + p, y + p]),
                       ([x + size + 4, x + size + 14], [y + p, y + p]),
                       ([x + p, x + p], [y - 14, y - 4]),
                       ([x + p, x + p], [y + size + 4, y + size + 14])]:
            ax.plot(xs, ys, color=CHARCOAL, lw=3, solid_capstyle="butt")
    box(ax, x, y, size, size, SKY, SKY, radius=7, lw=0)
    box(ax, x + 12, y + 12, size - 24, size - 24, SKY, tint(SKY, 0.6), radius=4, lw=1)
    bilingual_in_box(ax, x, y, size, size, zh, en, "white", size=label_size)


def domain(ax, x, width):
    frame = box(ax, x, 620, width, 330, fill="none", edge=GRAY, radius=16, lw=1.5)
    frame.set_linestyle((0, (5, 4)))
    frame.set_zorder(0)


def main():
    fig, ax = canvas("三种编译运行的模式区别 —— CPU/SIM/NPU",
                     "Compilation and Execution Modes: CPU / SIM / NPU")
    ax.add_patch(Polygon([(896, 216), (984, 216), (1024, 256), (1024, 354), (896, 354)],
                         closed=True, facecolor=RED, edgecolor="none"))
    ax.add_patch(Polygon([(984, 216), (984, 256), (1024, 256)],
                         closed=True, facecolor=tint(RED, 0.6), edgecolor="none"))
    ax.plot([934, 918, 934], [272, 288, 304], color="white", lw=2.2)
    ax.plot([984, 1000, 984], [272, 288, 304], color="white", lw=2.2)
    ax.plot([968, 952], [266, 312], color="white", lw=2.2)
    ax.plot([918, 968], [332, 332], color=tint(RED, 0.8), lw=1.6)
    bilingual(ax, 1068, 256, "算子源码", "Ascend C source", ha="left", size=28)
    ax.plot([960, 960], [354, 388], color=INK, lw=1.5)
    ax.plot([400, 1520], [388, 388], color=INK, lw=1.5)
    for cx, mode in [(400, "CPU"), (960, "SIM"), (1520, "NPU")]:
        arrow(ax, [(cx, 388), (cx, 480)], INK)
        bilingual(ax, cx + 32, 404, f"{mode} 编译", f"{mode} build", GRAY, ha="left", size=21)
        box(ax, cx - 168, 492, 336, 90, "#FAFAFA", RED, radius=7, lw=2 * 72 / DPI)
        bilingual_in_box(ax, cx - 168, 492, 336, 90, "可执行程序 demo", "Executable demo", size=23)
        arrow(ax, [(cx, 586), (cx, 648)], INK)
    for left in (138, 698, 1258):
        domain(ax, left, 524)
    chip(ax, 400, 742, 144, "处理器", "CPU")
    # Host-side monitor encloses the target model.
    box(ax, 822, 650, 276, 140, CHARCOAL, CHARCOAL, radius=9, lw=0)
    box(ax, 834, 662, 252, 110, "white", "white", radius=4, lw=0)
    target = box(ax, 878, 674, 164, 88, BLUE_LIGHT, SKY, radius=5, lw=1.3)
    target.set_linestyle((0, (3, 3)))
    bilingual_in_box(ax, 878, 674, 164, 88, "目标模型", "NPU model", SKY, size=21)
    box(ax, 950, 790, 20, 18, CHARCOAL, CHARCOAL, radius=0, lw=0)
    box(ax, 908, 808, 104, 5, CHARCOAL, CHARCOAL, radius=2, lw=0)
    # Generic accelerator card, not a particular product's layout.
    box(ax, 1382, 680, 276, 142, CHARCOAL, CHARCOAL, radius=9, lw=0)
    ax.plot([1368, 1368, 1386], [670, 838, 838], color=GRAY, lw=2.6)
    for i in range(9):
        ax.plot([1418 + i * 20, 1418 + i * 20], [822, 836], color=GRAY, lw=3,
                solid_capstyle="butt")
    chip(ax, 1520, 752, 108, "加速器", "NPU", label_size=20)
    for xx in (1400, 1626):
        for yy in (700, 730, 794):
            box(ax, xx, yy, 14, 7, "#AAB2B9", "#AAB2B9", radius=2, lw=0)
    for cx, zh, en in [(400, "CPU 模式", "CPU mode"), (1520, "真机模式", "NPU mode")]:
        bilingual(ax, cx, 864, zh, en, size=25)
    bilingual(ax, 960, 826, "在主机 CPU 上运行仿真模型",
              "Simulation model on host CPU", size=20)
    bilingual(ax, 960, 894, "无需本地物理 NPU", "No local NPU required", GRAY, size=18)
    scopes = [(400, "CPU 域功能调试", "CPU-domain functional debugging"),
              (960, "目标模型中的功能与性能观察", "Model function / performance"),
              (1520, "真实设备功能验证与性能测量", "Hardware checks / performance tests")]
    for cx, zh, en in scopes:
        bilingual(ax, cx, 968, zh, en, size=21)
    save(fig, __file__)


if __name__ == "__main__":
    main()
