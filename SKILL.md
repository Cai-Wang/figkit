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

## 出图顺序（六步法）

```
1. 搭画布   → A4Grid(...)                              figkit 布局
2. 画内容   → plot_*(gd, ax=ax)                        IgneousWR 内容
3. 收尾     → layout.finalize(...)                      figkit 布局
4. 格式把关 → apply_format(layout, fmt)                figkit 格式
5. 风格覆盖 → apply_style(layout, 'default')            figkit 风格
6. 保存     → layout.save(path)
```

第4步：IgneousWR 内部不设字号，apply_format 统一设置所有文字字号、字体、图例边框。  
第5步：apply_style 覆盖数据线粗/点大小；从 IgneousWR 画线时设的 `label=` 创建**共享图例**（只画在第一个子图上，仅显示色点不显示线条）。

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

- AI 编造的模板会被用户删除。每个模板必须来自实际需求。
- 图型特有的视觉（刻度交替、元素名旋转）必须放在 IgneousWR 的 plot_* 函数里，不是 figkit。
- 使用 IgneousWR 拼版前先确认 plot_* 函数是否接受 ax 参数。SKILL.md 可能写了但代码没实现。
- **`finalize()` 已不再处理刻度。** 刻度方向/长度/副刻度/网格/Y轴竖排全部由 IgneousWR 控制。figkit 的 `finalize()` 只做 `auto_gap` 调间距。
- **`apply_format()` 不碰刻度方向。** 只处理：字体族、字号、轴框线粗、图例边框。
- **`apply_style()` 不做启发式图型判断。** 只处理：数据线粗/点大小、共享图例。不做基于标签数量的刻度交替。
- **matplotlib ≥3.8 踩坑：`Tick._direction` 和 `tick1line.set_ydata()` 均无效。** 正确做法：`tick1line.set_marker(2)` 向内、`set_marker(3)` 向外。详见 `references/matplotlib-tick-workarounds.md`。

## 排版格式

### A4 拼版

| 名字 | 说明 | 何时用 |
|------|------|--------|
| `A4-2x2-standard` | 4 图，每格 80×70mm | 最常用 |
| `A4-1x2-ree-spider` | REE+蛛网并排，77×40mm | 微量元素图 |
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

## IgneousWR / figkit 分工约定

| 谁 | 管什么 | 不能做什么 |
|----|--------|----------|
| **IgneousWR** | 轴标签文本内容、元素名、边界线/多边形、标准化数据、轴范围/尺度、参考线、数据分组、刻度方向/长度/副刻度/网格/Y轴竖排/X标签排列、画线设 `label=` | 不设 fontsize=；不画图例 |
| **figkit apply_format** | 字体族、字号（轴标签/刻度/底图文本/图例统一）、轴框线粗、图例边框 | 不动元素名内容、不改刻度 |
| **figkit apply_style** | 数据线粗/点大小/颜色（全局预设值）、共享图例（纯色点无线条，放第一个子图） | 不基于图型类型做不同处理 |

## 文件结构

```
~/.hermes/skills/plotting/figkit/
├── SKILL.md
├── references/
│   ├── architecture-principles.md
│   ├── journal-format-research.md
│   └── journal-specs.md
└── scripts/
    ├── layout.py      A4Grid（纯定位：格子计算、add_subplot、finalize、save）
    ├── formats.py     LayoutFormat + apply_format + apply_style
    ├── styles.py      DiagramStyle 风格预设 + 调色板
    └── __init__.py    导入指引
```

> matplotlib ≥3.8 tick 方向操控踩坑记录位于 IgneousWR skill 的 `references/matplotlib-tick-workarounds.md`。
