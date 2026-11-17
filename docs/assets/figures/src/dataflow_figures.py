"""Original article 02 diagrams. Coordinates follow the shared 1920 × 1080 theme."""
from theme import BLUE_LIGHT, RED_LIGHT, RED, SKY, GRAY, INK, arrow, box, canvas, save, text

TITLES = [
    ("向量加法，每一列独立求和", "Add | Independent elements"),
    ("一行 Softmax 共用两个统计量", "Safe Softmax | Row maximum and exponential sum"),
    ("取一行、一列，得到一个输出", "Matmul | One row meets one column"),
    ("四个公式，四种数据依赖", "Operator dependencies"),
    ("计算单元如何组织", "Coupled AI Core / Ascend 2201 / NVIDIA Ampere A100"),
    ("从全局内存向计算单元供数", "Ascend 2201 | Selected SIMD data paths"),
    ("相同带宽，两条计算屋顶", "Roofline | Hypothetical ceilings"),
    ("同一组缓冲，可以处理多个数据块", "Add | Working set and logical traffic"),
    ("同一个输出块，沿 K 分四轮累加", "Matmul | 128 × 128 with 64 × 32 output tiles"),
    ("谁会再次读到同一块输入？", "Matmul | Reuse across independent output tiles"),
    ("方阵乘法在 Cube 屋顶上的位置", "Cube Roofline | Model bounds only"),
]


def node(ax, x, y, w, h, label, color=None, size=34):
    fill = BLUE_LIGHT if color == SKY else RED_LIGHT if color == RED else "white"
    box(ax, x, y, w, h, fill, color or GRAY)
    text(ax, x+w/2, y+h/2, label, size, ha="center", va="center")


def grid(ax, x, y, rows, cols, w, h, select, values=None, color=SKY):
    for i in range(rows):
        for j in range(cols):
            node(ax, x+j*w, y+i*h, w-3, h-3, str(values[i][j]) if values else "",
                 color if select(i,j) else None)


def chain(ax, labels, y, colors=None, left=110, right=1810):
    gap = 55
    width = (right-left-(len(labels)-1)*gap)/len(labels)
    for i, label in enumerate(labels):
        x = left+i*(width+gap)
        node(ax, x, y, width, 100, label, colors[i] if colors else None, 32)
        if i:
            arrow(ax, [(x-gap, y+50), (x-5, y+50)])


def foot(ax, caption):
    text(ax, 960, 940, caption, 29, GRAY, ha="center")


def roofs(fig, cube_only):
    for j, peak in enumerate([100] if cube_only else [10, 100]):
        axis = fig.add_axes([.13 if cube_only else .09+j*.49, .23, .76 if cube_only else .37, .51])
        axis.set(xscale="log", yscale="log", xlim=(5 if cube_only else .03, 500),
                 ylim=(4 if cube_only else .02, 240), xlabel="FLOP / Byte", ylabel="TFLOP / s",
                 title="Cube" if peak == 100 else "Vector")
        axis.grid(alpha=.18, which="both")
        axis.plot([.02, peak, 500], [.02, peak, peak], color=RED, lw=3)
        points = [(16,"n=64"), (32,"n=128"), (100,"n=400")] if cube_only else (
            [(1/12,"Add: 1/12"), (10,"I* = 10")] if peak==10 else [(16,"n=64"),(100,"I* = 100")])
        for p, label in points:
            axis.plot(p,p,"o",ms=9,mfc="white",mec=RED)
            axis.annotate(label,(p,p),xytext=(6,9),textcoords="offset points",fontsize=16)
        if cube_only:
            axis.annotate("", (12.8,6), (32,6), arrowprops=dict(arrowstyle="->",color=SKY,lw=3))
            axis.text(12.8,6.8,"12.8", ha="center")
            axis.text(32,6.8,"32",ha="center")


def render(index, script):
    fig, ax = canvas(*TITLES[index-1])
    if index == 1:
        for i,(a,b) in enumerate(zip([1,2,3,4],[4,1,5,2])):
            x = 410+i*320
            text(ax,x+105,250,f"i = {i}",32,GRAY,ha="center")
            for y,value in [(345,a),(515,b),(735,a+b)]:
                node(ax,x,y,210,90,str(value),RED if y==735 else SKY)
            text(ax,x+105,452,"+",38,ha="center")
            arrow(ax,[(x+105,614),(x+105,720)])
        for y,s in [(373,"输入 x"),(543,"输入 y"),(763,"输出 z")]:
            text(ax,190,y,s,34)
        foot(ax,"沿一列读完一次加法；相邻两列之间没有数据依赖。")
    elif index == 2:
        for y,label in [(265,"输入"),(422,"减去 2"),(579,"取指数"),(769,"除以 D")]:
            text(ax,110,y+22,label)
        for i,(a,b,c) in enumerate([(1,-1,"1/e"),(2,0,"1"),(2,0,"1")]):
            x = 450+i*330
            for y,value in [(265,a),(422,b),(579,c),(769,c+" / D")]:
                node(ax,x,y,205,75,str(value),RED if y==769 else SKY)
            for top,bot in [(340,412),(497,569),(654,759)]:
                arrow(ax,[(x+103,top),(x+103,bot)])
        node(ax,1430,340,360,95,"行最大值 m = 2",RED)
        node(ax,1430,660,360,95,"D = 1/e + 2",RED)
        for y,mid,bot in [(300,340,450),(618,660,805)]:
            arrow(ax,[(1325,y),(1610,y),(1610,mid)])
            arrow(ax,[(1610,mid+95),(1610,bot),(1325,bot)])
        foot(ax,"三个输出使用同一个分母，归一化后整行之和为 1。")
    elif index == 3:
        for x,title in [(250,"A   (2 × 3)"),(830,"B   (3 × 2)"),(1410,"C   (2 × 2)")]:
            text(ax,x,330,title)
        grid(ax,230,410,2,3,105,100,lambda i,j:i==0,[[1,2,3],[0,1,2]])
        grid(ax,840,410,3,2,105,100,lambda i,j:j==1,[[2,3],[1,4],[0,1]],RED)
        grid(ax,1410,410,2,2,105,100,lambda i,j:(i,j)==(0,1),[[4,14],[1,6]],RED)
        text(ax,655,475,"×",56)
        text(ax,1230,475,"=",56)
        node(ax,510,770,900,92,"1 × 3  +  2 × 4  +  3 × 1  =  14",RED)
        foot(ax,"计算同一输出行的另一格时，A 的第 0 行可以继续使用。")
    elif index == 4:
        for y,name,labels in [(240,"Add",["同一位置 x、y","逐元素相加","一个输出"]),
                              (414,"Softmax",["一整行","行最大值、指数和","整行归一化"]),
                              (588,"Matmul",["A 的行、B 的列","点积与输入复用","输出块"]),
                              (762,"Attention",["Q、K","分数 S → 概率 P","与 V 相乘得 O"])]:
            text(ax,125,y+30,name,37)
            chain(ax,labels,y,[SKY,None,RED],420,1800)
        foot(ax,"Attention 的分数与概率只在后续步骤仍需使用时保留。")
    elif index == 5:
        for x,title,labels in [(95,"昇腾 · 耦合 AI Core",["Scalar","Vector     Cube"]),
                (685,"昇腾 · 2201",["AIV   Scalar + Vector","GM 交接","AIC   Scalar + Cube"]),
                (1275,"Ampere A100 · SM",["Warp 调度器","FP32 运算单元","第三代 Tensor Core"])]:
            box(ax,x,270,550,555)
            text(ax,x+275,318,title,34,ha="center")
            for j,label in enumerate(labels):
                node(ax,x+40,430+j*120,470,85,label,SKY if j==0 else RED if j==len(labels)-1 else None)
            if x==95:
                arrow(ax,[(x+275,515),(x+275,548)],dashed=True)
            elif x==685:
                for y in [515,635]: arrow(ax,[(x+275,y),(x+275,y+32)])
        foot(ax,"框表示组织层级；图中单元数量、面积和位置均不代表实际规格。")
    elif index == 6:
        text(ax,120,245,"AIV   ·   Scalar 控制")
        chain(ax,["GM","MTE2 → UB","Vector","UB → MTE3","GM"],335,[None,SKY,RED,SKY,None])
        text(ax,120,560,"AIC   ·   Scalar 控制")
        chain(ax,["GM","MTE2 → L1","L0A / L0B","Cube","L0C","Fixpipe → GM"],650,
              [None,SKY,SKY,RED,SKY,None])
        foot(ax,"两条支路通过 GM 交接。箭头仅表示本文涉及的业务数据路径。")
    elif index in (7,11):
        roofs(fig,index==11)
        foot(ax,"假设带宽 1 TB/s。空心点表示模型上限。" if index==7 else
             "同一 128 阶方阵，若分块重读全部经过 HBM，强度由 32 降至 12.8 FLOP/Byte。")
    elif index == 8:
        text(ax,130,248,"一个任务一次处理 2048 对 FP32 元素")
        chain(ax,["GM 输入 x、y","UB：2 × 8 KiB","Vector 加法","UB：8 KiB","写回 GM"],335,
              [None,SKY,RED,SKY,None])
        text(ax,130,570,"长度 16384：同一组缓冲循环使用 8 次")
        for i in range(8):
            node(ax,165+i*200,680,185,105,f"块 {i}",SKY)
        foot(ax,"同时占用 24 KiB；处理完整向量共读 128 KiB、写 64 KiB。")
    elif index == 9:
        for i in range(2):
            y=330+i*265
            text(ax,100,y+53,f"第 {i+1} 轮",32)
            grid(ax,340,y,2,4,65,70,lambda r,c:r==0 and c==i)
            grid(ax,790,y,4,4,52,38,lambda r,c:r==i and c==0,color=RED)
            text(ax,650,y+45,"×",50)
            arrow(ax,[(1030,y+70),(1120,y+70),(1270,510)])
        for x,label in [(335,"A：向右移 32 列"),(760,"B：向下移 32 行"),(1295,"C：同一块部分和")]:
            text(ax,x,240,label,30)
        grid(ax,1300,430,2,4,90,85,lambda r,c:r==0 and c==0,color=RED)
        foot(ax,"每轮取 A 的 64 × 32 与 B 的 32 × 32；共 4 轮，最后写回 64 × 32 个输出。")
    elif index == 10:
        text(ax,165,265,"横向四块用同一组 A 行")
        text(ax,1025,265,"纵向两块用同一组 B 列")
        grid(ax,170,390,2,4,150,105,lambda r,c:r==0)
        grid(ax,1030,390,2,4,150,105,lambda r,c:c==0,color=RED)
        for x in [170,1030]:
            text(ax,x,642,"每个格子代表一个 64 × 32 输出块",28)
        node(ax,355,755,1210,90,"同一格：第 1 段乘积 + 第 2 段 + 第 3 段 + 第 4 段",RED)
        foot(ax,"若各输出块独立取数，A 总计读 4 遍，B 读 2 遍；每个输出块只写回一次。")
    save(fig,script)
