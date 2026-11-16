"""PCIe data flow with eight illustrative coupled AI Cores, not a target SoC."""
from theme import (canvas, bilingual, bilingual_in_box, box, arrow, save,
                   RED, SKY, INK, CHARCOAL, GRAY, LINE)


def ai_core(ax, x, y, index):
    """Vector and Cube are units of a coupled core; omitted blocks are not absent."""
    frame = box(ax, x, y, 232, 168, "white", LINE, radius=9, lw=1.4)
    frame.set_gid(f"coupled-ai-core-{index}")
    bilingual_in_box(ax, x, y + 5, 232, 56, f"计算核 {index}", f"AI Core {index}", line_gap=8)
    for offset, zh, en, color in [(12, "向量单元", "Vector", SKY),
                                  (123, "矩阵单元", "Cube", RED)]:
        unit = box(ax, x + offset, y + 72, 97, 76, color, color, radius=5, lw=0)
        unit.set_gid(f"core-{index}-{en.lower()}-unit")
        bilingual_in_box(ax, x + offset, y + 72, 97, 76, zh, en, "white")


def main():
    fig, ax = canvas("CPU 与昇腾 NPU 之间的数据流", "CPU–Ascend NPU Data Flow over PCIe")
    box(ax, 88, 246, 412, 668, "white", LINE, radius=16, lw=1.5)
    box(ax, 782, 246, 1066, 668, "white", LINE, radius=16, lw=1.5)
    bilingual(ax, 294, 280, "主机", "Host")
    bilingual(ax, 1316, 280, "昇腾处理器", "Ascend NPU")
    box(ax, 130, 386, 328, 88, "#FAFAFA", RED, radius=7, lw=1.5)
    bilingual_in_box(ax, 130, 386, 328, 88, "主机内存", "Host memory")
    box(ax, 820, 386, 990, 88, "#FAFAFA", RED, radius=7, lw=1.5)
    bilingual_in_box(ax, 820, 386, 990, 88, "设备内存", "Device memory / GM")
    # Copies connect memory spaces; the dashed path submits control work.
    bilingual(ax, 638, 286, "总线连接", "PCIe")
    arrow(ax, [(460, 414), (818, 414)], INK)
    arrow(ax, [(818, 450), (460, 450)], INK)
    bilingual(ax, 638, 496, "双向数据传输", "Bidirectional data", GRAY)
    for i in range(7):
        p = 215 + i * 27
        ax.plot([p, p], [588, 604], color=GRAY, lw=3)
        ax.plot([p, p], [784, 800], color=GRAY, lw=3)
    for i in range(6):
        p = 624 + i * 27
        ax.plot([182, 198], [p, p], color=GRAY, lw=3)
        ax.plot([392, 408], [p, p], color=GRAY, lw=3)
    box(ax, 198, 604, 194, 180, CHARCOAL, CHARCOAL, radius=9, lw=0)
    bilingual_in_box(ax, 198, 604, 194, 180, "主机处理器", "CPU", "white")
    arrow(ax, [(270, 488), (270, 580)], INK)
    arrow(ax, [(318, 580), (318, 488)], INK)
    bilingual(ax, 294, 818, "运行控制程序", "Host program")
    # Abstract memory-access connectors, not a physical on-chip interconnect.
    ax.plot([1316, 1316], [476, 506], color=GRAY, lw=1.2)
    ax.plot([800, 1692], [506, 506], color=GRAY, lw=1.2)
    ax.plot([800, 800, 1692], [506, 708, 708], color=GRAY, lw=1.2)
    for column in range(4):
        cx = 936 + 252 * column
        ax.plot([cx, cx], [506, 530], color=GRAY, lw=1.2)
        ax.plot([cx, cx], [708, 720], color=GRAY, lw=1.2)
    for index in range(8):
        ai_core(ax, 820 + 252 * (index % 4), 530 + 190 * (index // 4), index)
    arrow(ax, [(410, 746), (544, 746), (544, 862), (780, 862)], GRAY, dashed=True)
    bilingual(ax, 638, 770, "任务提交", "Kernel launch", GRAY)
    bilingual(ax, 960, 958, "8 核耦合架构示意，非实际设备核数或芯片布局",
              "8 coupled cores for illustration, not a product floorplan", GRAY)
    save(fig, __file__)


if __name__ == "__main__":
    main()
