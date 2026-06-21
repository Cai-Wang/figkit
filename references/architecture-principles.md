# figkit 架构设计原则（2026-06-25 更新）

## 三个概念

| 概念 | 文件 | 职责 |
|------|------|------|
| 布局(Layout) | layout.py | A4Grid 格子定位、auto_gap、save。不做任何刻度/样式操作 |
| 格式(Format) | formats.py + apply_format | 字体族、字号（轴/刻度/底图/图例）、轴框线粗、图例边框。不碰刻度 |
| 风格(Style) | styles.py + apply_style | 数据点线粗/点大小/调色板、共享图例。不做图型判断 |

## 核心原则

**figkit 只能管"全局统一"的，不能管"图型特有"的。**

- 图型特有效果（刻度方向、刻度交替、标签偏移、Y轴网格）→ IgneousWR `apply_*_axis_style` 后置函数
- 内容级的图型设置（刻度位置/值、轴范围、参考线、标签文本）→ IgneousWR `plot_*` 函数
- 全局统一（字体、DPI、数据点风格、图例）→ figkit

## 关键时序约束：Tick 对象级样式必须在 finalize 和 apply_format 之后调用

matplotlib 3.8+ 的 `fig.canvas.draw()`（在 finalize→auto_gap 内部）通过 `_update_ticks()` 重建 Tick 对象。因此 `set_marker(2/3)` 等 Tick 对象级属性**不能**放在 `plot_*` 内容函数里——会在 finalize 时被冲掉。必须拆入 `apply_spider_axis_style(ax)` 后置函数。

**`ax.tick_params()` 全量重置 tick 属性**（非增量更新）。因此后置轴样式函数必须在 apply_format (其内部也可能调 tick_params) **之后**调用。

## 七步出图法（2026-06-25）

```
1. 搭画布        → A4Grid(...)               figkit 布局
2. 画内容        → plot_*(gd, ax=ax)         IgneousWR 内容（不碰 Tick 对象级属性）
3. 排版重定位    → layout.finalize(pairs=...) figkit 布局（⚠ draw 重置 Tick）
4. 格式把关      → apply_format(layout, fmt) figkit 格式（字体/轴框线/图例）
5. 风格覆盖      → apply_style(layout, name) figkit 风格（线粗/点大小/共享图例）
6. 后置轴样式    → apply_spider_axis_style   IgneousWR Tick 级（每个子图单独调）
                    / apply_ree_axis_style
7. 保存          → layout.save(path)         figkit 布局（save 不重建 Tick）
```

## 各模块职责

### layout.py — A4Grid
- 纸张尺寸、边距、格子计算
- add_subplot 放子图（保存几何到 _axes_geom）
- auto_gap 自动调整并排图的间距（支持多对 pairs=）
- finalize 只做 auto_gap（不碰刻度）
- save 保存
- 不含 style_ax、style_all、apply_format（均已清理）

### formats.py — LayoutFormat + apply_format + apply_style

**apply_format(layout, fmt) — 格式把关（第4步）：**
- 字体族（serif/sans-serif）
- 字号（轴标签、刻度标签、底图文本、图例）
- 轴框线粗
- 图例边框

**apply_style(layout, style_name) — 风格覆盖（第5步）：**
- 数据线线粗
- 数据点大小
- 共享图例（只画在 axes[0]，纯色点不显线）

### styles.py — DiagramStyle
- 各图型的默认点大小/线粗
- 调色板定义
- 传入 apply_style 调用

## 明确排除出 figkit 的事项（移至 IgneousWR 后置函数）

| 事项 | 归属 | 所在函数 |
|------|------|----------|
| 刻度方向(in/out) | IgneousWR | apply_spider_axis_style |
| 刻度交替内外 | IgneousWR | apply_spider_axis_style |
| 副刻度开关 | IgneousWR | apply_spider_axis_style |
| Y轴标签竖排 | IgneousWR | apply_spider_axis_style / apply_ree_axis_style |
| Y轴网格 | IgneousWR | apply_spider_axis_style / apply_ree_axis_style |
| 标签偏移（跟随刻度） | IgneousWR | apply_spider_axis_style |
| X轴多标签自动缩小/旋转 | IgneousWR | 未来可能也拆出 |

## 历史清理记录

- 2026-06-21: presets.py 删除，内容并入 formats.py 默认 format_params
- 2026-06-21: utils.py 删除（safe_ylabel 被 apply_format 重复实现）
- 2026-06-21: style_ax()/style_all() 从 A4Grid 中移除
- 2026-06-21: apply_format 从 layout.py 移入 formats.py
- 2026-06-21: finalize() 刻度相关代码全部移除，只留 auto_gap
- 2026-06-21: apply_style 中的刻度交替启发式代码移除（n_labels > 8）
- 2026-06-21: LayoutFormat 默认字段中 tick_direction/major/minor_size 移除
- **2026-06-25: layout.py auto_gap 修复：用 _axes_geom 替代 dict 插入顺序索引，支持 pairs= 多对**
- **2026-06-25: Tick 级刻度样式从 plot_spider 拆入 apply_spider_axis_style（后置函数）**

## 踩坑

- AI 编造的模板（A4-2x1-portrait、nature/elsevier 系列）已被用户删除。每个模板必须有实际需求来源。
- `_direction` 和 `set_ydata()` 在 matplotlib≥3.8 中无效，需用 `set_marker(2/3)`。
- `fig.canvas.draw()` 重建 Tick 对象——`set_marker` 必须在最后一次 draw 之后。
- `ax.tick_params()` 全量重置（非增量）——后置轴样式必须在 apply_format 之后调用。


