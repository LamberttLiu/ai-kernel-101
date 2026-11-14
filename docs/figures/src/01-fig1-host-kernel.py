"""Schematic Host/Stream lanes, not a measured schedule or a core mapping."""
from theme import (canvas, bilingual, bilingual_in_box, box, arrow, save,
                   SKY, RED, GRAY, LINE, CHARCOAL)


def main():
    fig, ax = canvas("从 Host 到 Device 的异步执行路径", "Asynchronous Execution from Host to Device")

    # Solid bars carry the sequence. Lengths and positions are schematic.
    for y in (244, 394):
        ax.plot([174, 1010], [y, y], color=LINE, lw=0.85, zorder=0)
    bilingual(ax, 110, 224, "主机", "Host", 18)
    bilingual(ax, 110, 374, "设备流", "NPU Stream", 18)

    box(ax, 178, 213, 138, 62, CHARCOAL, CHARCOAL, radius=4, lw=0)
    bilingual_in_box(ax, 178, 213, 138, 62, "初始化", "Initialize", 17, "white")

    box(ax, 339, 213, 39, 62, SKY, SKY, radius=4, lw=0)
    bilingual(ax, 358.5, 157, "提交", "Launch", 15)
    arrow(ax, [(369, 282), (433, 355)], RED)

    # The sample synchronizes immediately after launch; no invented CPU work.
    box(ax, 403, 213, 417, 62, RED, RED, radius=4, lw=0)
    bilingual_in_box(ax, 403, 213, 417, 62, "同步等待", "Synchronize", 17, "white")
    box(ax, 849, 213, 158, 62, CHARCOAL, CHARCOAL, radius=4, lw=0)
    bilingual_in_box(ax, 849, 213, 158, 62, "清理资源", "Clean up", 17, "white")

    box(ax, 438, 363, 382, 62, SKY, SKY, radius=4, lw=0)
    bilingual_in_box(ax, 438, 363, 382, 62, "核函数执行", "hello_world()", 19, "white")
    bilingual(ax, 629, 441, "逻辑任务 0–7", "Blocks 0–7", 14, GRAY)

    ax.plot([820, 820], [183, 437], color=RED, lw=0.9, linestyle=(0, (4, 4)))
    bilingual(ax, 820, 132, "任务完成", "Complete", 14, RED)
    arrow(ax, [(820, 357), (820, 282)], RED)

    arrow(ax, [(174, 501), (1009, 501)], GRAY)
    bilingual(ax, 988, 513, "时间", "Time", 13, GRAY)
    bilingual(ax, 540, 531, "执行关系示意，非实测时间线",
              "Schematic only · not measured timing", 12, GRAY)
    save(fig, __file__)


if __name__ == "__main__":
    main()
