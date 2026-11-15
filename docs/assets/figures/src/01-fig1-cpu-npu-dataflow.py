"""PCIe data flow with eight illustrative coupled AI Cores, not a target SoC."""
from theme import (canvas, bilingual, bilingual_in_box, box, arrow, save,
                   RED, SKY, INK, CHARCOAL, GRAY, LINE)


def ai_core(ax, x, y, index):
    """Vector and Cube are units of a coupled core; omitted blocks are not absent."""
    frame = box(ax, x, y, 130, 93, "white", LINE, radius=5, lw=0.9)
    frame.set_gid(f"coupled-ai-core-{index}")
    bilingual_in_box(ax, x, y + 3, 130, 31, f"计算核 {index}", f"AI Core {index}",
                     11, INK, line_gap=3)
    for offset, zh, en, color in [(7, "向量单元", "Vector", SKY),
                                  (69, "矩阵单元", "Cube", RED)]:
        unit = box(ax, x + offset, y + 40, 54, 42, color, color, radius=3, lw=0)
        unit.set_gid(f"core-{index}-{en.lower()}-unit")
        bilingual_in_box(ax, x + offset, y + 40, 54, 42, zh, en, 10,
                         "white", line_gap=5)


def main():
    fig, ax = canvas("CPU 与昇腾 NPU 之间的数据流", "CPU–Ascend NPU Data Flow over PCIe")

    box(ax, 50, 137, 230, 370, "white", LINE, radius=9, lw=1)
    box(ax, 440, 137, 600, 370, "white", LINE, radius=9, lw=1)
    bilingual(ax, 165, 150, "主机", "Host", 17)
    bilingual(ax, 740, 150, "昇腾处理器", "Ascend NPU", 17)

    box(ax, 73, 215, 184, 49, "#FAFAFA", RED, radius=4, lw=1)
    bilingual_in_box(ax, 73, 215, 184, 49, "主机内存", "Host memory", 13)
    box(ax, 461, 215, 558, 49, "#FAFAFA", RED, radius=4, lw=1)
    bilingual_in_box(ax, 461, 215, 558, 49, "设备内存", "Device memory / GM", 14)

    # Host/device copies connect the memory spaces, not the arithmetic units.
    bilingual(ax, 359, 157, "总线连接", "PCIe", 14)
    arrow(ax, [(258, 230), (460, 230)], INK)
    arrow(ax, [(460, 250), (258, 250)], INK)
    bilingual(ax, 359, 275, "双向数据传输", "Bidirectional data", 12, GRAY)

    # Symbolic CPU package with a control program; no cache/topology assertion.
    for i in range(7):
        p = 121 + i * 15
        ax.plot([p, p], [327, 335], color=GRAY, lw=2.2)
        ax.plot([p, p], [435, 443], color=GRAY, lw=2.2)
    for i in range(6):
        p = 347 + i * 15
        ax.plot([102, 110], [p, p], color=GRAY, lw=2.2)
        ax.plot([220, 228], [p, p], color=GRAY, lw=2.2)
    box(ax, 110, 335, 110, 100, CHARCOAL, CHARCOAL, radius=5, lw=0)
    bilingual_in_box(ax, 110, 335, 110, 100, "主机处理器", "CPU", 15, "white")
    arrow(ax, [(152, 271), (152, 323)], INK)
    arrow(ax, [(178, 323), (178, 271)], INK)
    bilingual(ax, 165, 452, "运行控制程序", "Host program", 13)

    # Abstract memory-access connectors; not a physical on-chip interconnect.
    ax.plot([740, 740], [265, 281], color=GRAY, lw=0.8)
    ax.plot([450, 952], [281, 281], color=GRAY, lw=0.8)
    ax.plot([450, 450, 952], [281, 394, 394], color=GRAY, lw=0.8)
    for column in range(4):
        cx = 526 + 142 * column
        ax.plot([cx, cx], [281, 294], color=GRAY, lw=0.8)
        ax.plot([cx, cx], [394, 400], color=GRAY, lw=0.8)
    for index in range(8):
        ai_core(ax, 461 + 142 * (index % 4), 294 + 106 * (index // 4), index)

    # Control submission is dashed and distinct from the solid data-copy paths.
    arrow(ax, [(229, 414), (306, 414), (306, 478), (438, 478)], GRAY, dashed=True)
    bilingual(ax, 359, 427, "任务提交", "Kernel launch", 11, GRAY)

    bilingual(ax, 540, 528, "8 核耦合架构示意，非实际设备核数或芯片布局",
              "8 coupled cores for illustration, not a product floorplan", 11, GRAY)
    save(fig, __file__)


if __name__ == "__main__":
    main()
