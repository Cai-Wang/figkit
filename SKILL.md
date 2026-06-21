---
name: figkit
description: 投稿图件工具箱 — 布局(Layout) + 格式(Format) + 风格(Style)
---

# figkit — 投稿图件工具箱

## 三个概念

```
布局(Layout)    格式(Format)              风格(Style)
空间位置         字体族/字号/DPI/          点大小/颜色/线型
A4Grid,         图例边框/                  标记形状/调色板
finalize,        轴框线粗
save             → 一调整体变              → 好不好看（各图不同）
```

## 核心设计原则（踩坑经验）

**figkit 只能管"全局统一"的，不能管"图型特有"的。**

❌ 不要做的事：
- 不要管 X 轴刻度交替内外（某些图有29个元素名需要交替，其他图不需要——这是图型特性）
- 不要管 Y 轴范围（每个图数据不同，IgneousWR 自己算）
- 不要管标签旋转/偏移（REE 14个元素不旋也能放，蛛网29个需要特殊处理）
- 不要在 apply_format/apply_style 里判断"这个子图是不是蛛网图"——figkit 不知道
- 不要管刻度方向（in/out）、副刻度开关、网格——这些是 IgneousWR 的图型逻辑

### 刻度尺寸 vs 刻度逻辑（关键架构决策，2026-06-21）

**figkit 只控制刻度 SIZE（视觉比例），不控制刻度 LOGIC（方向/交替）。** 区分如下：

| 维度 | 属于 | 例子 |
|------|------|------|
| 刻度 LOGIC | IgneousWR（图型特性） | 方向(in/out)、交替内外、副刻度开关、Y轴竖排 |
| 刻度 SIZE | figkit（排版比例） | 刻度长度、刻度粗细——跟随字号缩放 |

**做法：** 在 `formats.py` 的 `format_params` 里设 `tick_length`、`tick_width` 等。出图脚本在调用 IgneousWR 画图**之前**通过 `plt.rcParams` 设好这些值，IgneousWR 画出来的刻度尺寸就是对的。

```python
# 出图脚本中，在调用 plot_spider 之前：
plt.rcParams['xtick.major.size'] = fmt.format_params['tick_length']
plt.rcParams['xtick.major.width'] = fmt.format_params['tick_width']
plt.rcParams['xtick.minor.size'] = fmt.format_params['tick_length_minor']
```

**关键踩坑：** 不要在画图后调 `ax.tick_params(length=..., width=...)`——它看起来只改尺寸，但实际会**重置所有 tick 的属性**，包括 IgneousWR 精心设置的 `marker(2/3)` 交替逻辑。`tick_params` 不是"增量更新"，是全量重置。

字号和刻度长度应同步缩放。例如字号 8pt（原 12pt 的 0.67）→ 刻度长度也从 5pt 缩到 3.5pt。默认值存于 `format_params`，各格式预设可单独覆盖。

✅ figkit 该做的事（全局统一）：
- 所有图的字体族（Times New Roman）、字号、DPI
- 所有图的轴框线粗
- 所有图的**刻度尺寸**（长度、粗细，与字号配套缩放）
- 所有图的图例样式（字号、位置、边框、纯色点不显示线条）
- 所有图的数据点线粗和点大小（全局默认值）

## 出图顺序（新流程 v2.1 — 推荐）

**核心变化：视觉参数前置传入 IgneousWR，不再事后覆写。** `apply_format` / `apply_style` 已废弃（旧流程保留但勿用——tick_params 全量重置破坏后置轴样式）。

```
1. 定风格        → style dict + plt.rcParams              调用方（字号/字体/刻度尺寸/线粗/点大小）
2. 搭画布        → layout = A4Grid(...)                    figkit 布局
   cell          → layout.add_subplot(row, col, label='..')
3. 画内容        → plot_*(gd, ax=ax, **style)              IgneousWR（视觉参数一次画到位）
4. 排版          → layout.finalize(pairs=...)              figkit auto_gap（⚠ 内部 draw 重置 Tick）
5. 后置轴样式    → apply_spider_axis_style(ax) /           IgneousWR Tick 级（每个子图单独调）
                    apply_ree_axis_style(ax)
6. 保存          → layout.save(path)                       figkit（save 不重建 Tick）
```

**时序铁律：** `plot_*` → `finalize` → `apply_*_axis_style` → `save`。违反则刻度交替不生效。

第5步必须放在 finalize **之后**。`apply_*_axis_style` 内部有 `fig.canvas.draw()`——这是全流程最后一次 draw。

### 旧流程（deprecated — 勿用）

以下两步会重置 tick 属性，导致后置轴样式失效：
- `apply_format(layout, fmt)` — 内部调 `ax.tick_params(labelsize=...)` 全量重置 tick
- `apply_style(layout, 'default')` — 调 `set_sizes`/`set_linewidth` 覆盖数据线属性

新流程中所有视觉参数（字号、字体、线粗、点大小、刻度尺寸）通过 `plt.rcParams` 和 `plot_*` 参数前置传入。

## 共享图例行为

`apply_style` 遍历所有子图的 axes：
1. 收集所有带 label 的 Line2D 颜色 → 去重
2. 用 `Line2D(linewidth=0, marker='o')` 构造纯色点 handle
3. 只画在 `layout.axes[0]`（第一个子图）
4. 其他子图不画图例

这意味着：**多图拼版时只有一个共享图例，放在第一个子图的 upper right。**

## 开发／出图流程（校准循环）

1. 拿真实数据 + 布局模板出图到桌面
2. 先出 IgneousWR 裸版（不经 figkit），确认内容正确
3. 再加 figkit 出投稿版，看格式/风格是否满意
4. 用户指出问题后调 formats.py / styles.py 参数
5. 调好后的参数通过 `skill_manage action='patch'` 存为预设
## 踩坑记录

### 字体大小 vs 画布尺寸不匹配（2026-06-26 发现）

**新流程的漏洞：** `apply_format` 废弃后，字号由 `plt.rcParams['font.size']` 统一设一次。但同一个字号在不同画布上效果不同：

| 场景 | 图宽 | 29个蛛网标签 | 结果 |
|------|------|-------------|------|
| 裸图预览 | 8" (203mm) | 每标签 ~7.0mm | 正常 |
| A4 拼版 cell (1×2) | 75mm | 每标签 ~2.6mm | **重叠** |

**根因：** 旧流程的 `apply_format` 会根据格式预设调字号（`A4-1x2-ree-spider` 预设 8pt vs `A4-2x2-standard` 预设 12pt）。新流程没有这个按布局调字号的机制。

**避免方法：** 裸图和拼版不能用同一个 `plt.rcParams['font.size']`。出图脚本里按场景分别设置：

```python
# 裸图预览：正常字号
plt.rcParams['font.size'] = 9

# 拼版（A4 1×2 REE+spider）：缩小字号
plt.rcParams['font.size'] = 7    # 75mm cell 容纳 29 个蛛网标签
```

### 裸图画布尺寸（2026-06-26 发现）

**问题：** 裸图预览不应套用 A4 拼版的 cell 尺寸。裸图目的是给人看内容是否正确，用正常宽高比。

**避免方法：** 裸图用 `figsize=(8, 5)` 或 `(6, 4)`，拼版才用 A4 单元格尺寸。两者传同样的 `ax=ax` 参数和 `**style` 视觉参数，只是画布尺寸不同。

```
# ✅ 裸图
fig, ax = plt.subplots(figsize=(8, 5))
plot_spider(gd, ax=ax, **style)
apply_spider_axis_style(ax)
fig.savefig('bare.png')

# ✅ 拼版（画布尺寸不同，视觉参数相同）
layout = A4Grid(1, 2, paper='A4', ...)
ax = layout.add_subplot(0, 0, label='sp')
plot_spider(gd, ax=ax, **style)       # 同一套 style
```

### 其他已知踩坑

- AI 编造的模板会被用户删除。每个模板必须来自实际需求。
- 图型特有的视觉（刻度交替、元素名旋转）必须放在 IgneousWR 的 `apply_*_axis_style` 后置函数里，**不是** figkit，也**不是** `plot_*` 函数主路径。
- 使用 IgneousWR 拼版前先确认 plot_* 函数是否接受 ax 参数。SKILL.md 可能写了但代码没实现。
- **`finalize()` 已不再处理刻度。** 刻度方向/长度/副刻度/网格/Y轴竖排全部由 IgneousWR 控制。figkit 的 `finalize()` 只做 `auto_gap` 调间距。
- **`apply_format()` 不碰刻度方向。** 只处理：字体族、字号、轴框线粗、图例边框。
- **`apply_style()` 不做启发式图型判断。** 只处理：数据线粗/点大小、共享图例。不做基于标签数量的刻度交替。
- **matplotlib ≥3.8 踩坑：`fig.canvas.draw()` 通过 `_update_ticks()` 重建 Tick 对象。** 因此 `set_marker(2/3)`、`set_y(offset)` 等 Tick 对象级属性必须在**最后一次** `draw()` 之后设置。在 figkit 工作流中，最后这个 draw 在 `apply_spider_axis_style()` 内部——这也是为什么步骤 6 必须放在步骤 3–5 之后。
- **`ax.tick_params()` 全量重置 tick 属性**（非增量更新）。调用 `tick_params(length=..., width=...)` 会覆盖之前设的 `marker(2/3)`。因此图型特有的刻度方向/交替必须通过 `apply_*_axis_style` 在 `apply_format` 之后调用才能生效。
- **`layout.finalize()` 的 `auto_gap` 已支持多对。** 用法：`layout.finalize(pairs=[('a','b'), ('c','d')])`。旧签名 `finalize(left_ax_name='a', right_ax_name='b')` 仍兼容。内部 `_axes_geom` 记录真实 row/col/rowspan/colspan，不再依赖 dict 插入顺序索引。

## 排版格式

### A4 拼版

| 名字 | 说明 | 何时用 |
|------|------|--------|
| `A4-2x2-standard` | 4 图，每格 80×70mm | 最常用 |
| `A4-1x2-ree-spider` | REE+蛛网并排，78×42mm，垂直居中 | 微量元素图（手动 top/bottom 居中） |
| `A4-3x2-dense` | 6 图，55mm，10pt | 会议 poster/补充材料 |

## 各图型风格预设

| 图型 | 点大小 | 标记 | 线粗 | 说明 |
|------|--------|------|------|------|
| TAS | 50 | o | 1.5 | 加细边 |
| K2O-SiO2 | 45 | o | 1.5 | |
| AFM | 45 | o | 1.5 | |
| 判别图 | 42 | o | 1.5 | 适合黑白打印 |
| REE | 8 | o | 1.2 | 小点在线段上 |
| 蛛网图 | 8 | o | 1.0 | 小点在线段上 |
| 三元图 | 15 | o | 1.5 | 空间紧凑 |

**调用：** `apply_style(layout, 'tas')`

## IgneousWR / figkit 分工约定（2026-06-25 更新）

**关键时序约束：Tick 对象级样式必须在 finalize 之后调用。**

| 谁 | 管什么 | 不能做什么 | 调用时机 |
|----|--------|----------|----------|
| **IgneousWR `plot_*`**（内容函数） | 轴标签文本、元素名、边界线/多边形、标准化数据、轴范围/尺度、参考线、数据分组、刻度位置/值、画线设 `label=` | 不设 fontsize=；不画图例；不碰 Tick 对象级属性（set_marker） | 步骤 2 |
| **figkit `finalize`** | auto_gap 间距测量、子图位置重排 | 不设刻度风格、字体 | 步骤 3 |
| **IgneousWR `apply_spider_axis_style`** | Spider X 轴刻度交替内外、标签偏移、Y 竖排、Y 网格 | 不动子图位置 | 步骤 4（finalize 之后） |
| **IgneousWR `apply_ree_axis_style`** | REE Y 竖排、Y 网格 | 不动子图位置 | 步骤 4（finalize 之后） |

**DEPRECATED（新流程不再调用，tick_params 全量重置破坏后置轴样式）：**
- `apply_format(layout, fmt)` — ~~字体族、字号、轴框线粗、图例边框~~
- `apply_style(layout, 'default')` — ~~数据线粗/点大小/颜色、共享图例~~

## 文件结构

```
~/.hermes/skills/plotting/figkit/
├── SKILL.md
├── references/
│   ├── architecture-principles.md
│   ├── journal-format-research.md
│   ├── matplotlib-tick-workarounds.md   # Tick 重建根因 + 方案
│   └── journal-specs.md
├── templates/
│   └── ree-spider-1x2-pipeline.py       # 可复用的拼版管道模板
└── scripts/
    ├── layout.py      A4Grid（纯定位：格子计算、add_subplot、finalize、save）
    ├── formats.py     LayoutFormat + apply_format + apply_style
    ├── styles.py      DiagramStyle 风格预设 + 调色板
    └── __init__.py    导入指引
```

复制模板到当前目录：
```bash
cp -r ~/.hermes/skills/plotting/figkit/templates/ ./templates/
```

> matplotlib ≥3.8 tick 方向操控踩坑记录位于 IgneousWR skill 的 `references/matplotlib-tick-workarounds.md`。
