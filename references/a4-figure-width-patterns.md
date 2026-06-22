# A4 图件有效总宽模式速查

## 概念：用边距控制总宽，不改画布尺寸

A4 宽 = 210mm。要让两图并排的**有效总宽**为 X mm，公式：

```
left + right = 210 - X
```

常用模式：

| 目标 | left | right | 说明 |
|------|------|-------|------|
| 160mm | 25 | 25 | 投稿拼版常见宽度 |
| 170mm | 20 | 20 | 稍宽，适合元素多的图 |
| 180mm | 15 | 15 | 紧凑拼版 |
| 190mm | 10 | 10 | 最宽，适合简单图对 |

**关键：** 永远不改 `paper=` 参数（保留 `'A4'`），只调 `left`/`right` 来控制可用宽度。

## 典型配置：REE + Spider 1×2，160mm 总宽，8pt Times New Roman

```python
plt.rcParams.update({
    'font.size':         8,
    'font.family':       'serif',      # Times New Roman
    'axes.linewidth':    0.6,
    'xtick.major.size':  3.5,
    'xtick.major.width': 0.6,
    'ytick.major.size':  3.5,
    'ytick.major.width': 0.6,
})

layout = A4Grid(
    1, 2,
    paper='A4',          # ← 保持 A4，不改
    left=25, right=25,   # → 总宽 = 210-25-25 = 160mm
    top=123, bottom=122, # 垂直居中，cell ~78×52mm ≈ 1.5:1 比例（宽>高）
    hspace=0,
    wspace=5,            # 两图间距 5mm
)

# 图例 8pt
ax_ree.legend(..., fontsize=8)

# 子图编号 (a)(b) 8pt
ax.text(..., fontsize=8, fontweight='bold')
```

## 踩坑（第2次后才理解——记录以防再犯）

**错误做法：** 用户说"总宽160mm"→ 把 `paper=(160, 90)` → 画布被改成非标尺寸，不是投稿要求的 A4 页面。

**正确做法：** 用户说"总宽160mm"→ 目标是在 A4 页面上两图加起来 160mm。A4 宽 210mm，所以左右边距各 (210-160)/2 = 25mm。`paper='A4'` 保持不变。

**验证法：** 打印 layout 的 mm 可用宽度：
```python
usable_w = layout.paper_w - layout.margins['left'] - layout.margins['right']
print(f'可用总宽: {usable_w}mm')  # 应该输出 160.0
```

## 默认值参考

| 参数 | 值 | 备注 |
|------|----|------|
| 字体 | Times New Roman (serif) | 用户要求 |
| 字号 | 8pt | 轴标签、刻度、图例全部统一 |
| 刻度长度 | 3.5pt | 与 8pt 字号配套 |
| 刻度粗细 | 0.6pt | |
| 轴框线粗 | 0.6pt | |
