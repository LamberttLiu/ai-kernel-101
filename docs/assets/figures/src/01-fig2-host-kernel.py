"""Schematic Host/Stream lanes, not a measured schedule or a core mapping."""
from theme import (canvas, bilingual, bilingual_in_box, box, arrow, save,
                   SKY, RED, GRAY, LINE, CHARCOAL)


def main():
    fig, ax = canvas("从 Host 到 Device 的异步执行路径", "Asynchronous Execution from Host to Device")
    for y in (440, 710):
        ax.plot([310, 1796], [y, y], color=LINE, lw=1.3, zorder=0)
    bilingual(ax, 196, 414, "主机", "Host")
    bilingual(ax, 196, 684, "设备流", "NPU Stream")
    box(ax, 316, 384, 246, 112, CHARCOAL, CHARCOAL, radius=7, lw=0)
    bilingual_in_box(ax, 316, 384, 246, 112, "初始化", "Initialize", "white")
    box(ax, 602, 384, 70, 112, SKY, SKY, radius=7, lw=0)
    bilingual(ax, 637, 290, "提交", "Launch")
    arrow(ax, [(656, 508), (770, 638)], RED)
    # Immediate synchronization: no invented CPU work between launch and wait.
    box(ax, 716, 384, 742, 112, RED, RED, radius=7, lw=0)
    bilingual_in_box(ax, 716, 384, 742, 112, "同步等待", "Synchronize", "white")
    box(ax, 1510, 384, 282, 112, CHARCOAL, CHARCOAL, radius=7, lw=0)
    bilingual_in_box(ax, 1510, 384, 282, 112, "清理资源", "Clean up", "white")
    box(ax, 778, 654, 680, 112, SKY, SKY, radius=7, lw=0)
    bilingual_in_box(ax, 778, 654, 680, 112, "核函数执行", "hello_world()", "white")
    bilingual(ax, 1118, 798, "逻辑任务 0–7", "Blocks 0–7", GRAY)
    ax.plot([1458, 1458], [330, 788], color=RED, lw=1.4, linestyle=(0, (4, 4)))
    bilingual(ax, 1458, 244, "任务完成", "Complete", RED)
    arrow(ax, [(1458, 644), (1458, 508)], RED)
    arrow(ax, [(310, 902), (1796, 902)], GRAY)
    bilingual(ax, 1756, 930, "时间", "Time", GRAY)
    bilingual(ax, 960, 958, "执行关系示意，非实测时间线",
              "Schematic only · not measured timing", GRAY)
    save(fig, __file__)


if __name__ == "__main__":
    main()
