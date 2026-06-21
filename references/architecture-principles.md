# figkit 架构设计原则（2026-06-21 最终版）

## 三个概念

| 概念 | 文件 | 职责 |
|------|------|------|
| 布局(Layout) | layout.py | A4Grid 格子定位、auto_gap、save。不做任何刻度/样式操作 |
| 格式(Format) | formats.py + apply_format | 字体族、字号（轴/刻度/底图/图例）、轴框线粗、图例边框。不碰刻度 |
| 风格(Style) | styles.py + apply_style | 数据点线粗/点大小/调色板、共享图例。不做图型判断 |

## 核心原则

**figkit 只能管"全局统一"的，不能管"图型特有"的。**

- 图型特有效果（刻度方向、刻度交替、标签偏移、Y轴网格）→ IgneousWR plot_* 函数
- 全局统一（字体、DPI、数据点风格、图例）→ figkit

## 六步出图法

```
1. 搭画布   → A4Grid(...)           figkit 布局
2. 画内容   → plot_*(gd, ax=ax)     IgneousWR（所有刻度/内容都在此完成）
3. 收尾     → layout.finalize()     figkit 布局（只做 auto_gap）
4. 格式把关 → apply_format()         figkit 格式（字体/轴框线/图例）
5. 风格覆盖 → apply_style()          figkit 风格（线粗/点大小/共享图例）
6. 保存     → layout.save()          figkit 布局
```

## 各模块职责

### layout.py — A4Grid
- 纸张尺寸、边距、格子计算
- add_subplot 放子图
- auto_gap 自动调整并排图的间距
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

## 明确排除出 figkit 的事项

| 事项 | 原因 | 归属 |
|------|------|------|
| 刻度方向(in/out) | 图型可自己决定 | IgneousWR |
| 刻度长度 | 内容默认值 | IgneousWR |
| 副刻度开关 | 图型特性（蜘蛛关/REE关/分类图开） | IgneousWR |
| Y轴标签竖排 | 读性需求 | IgneousWR |
| X轴多标签自动缩小/旋转 | 图型特性 | IgneousWR |
| 网格线 | 图型特性 | IgneousWR |
| 刻度交替内外 | 纯图型特性 | IgneousWR |

## 历史清理记录

- 2026-06-21: presets.py 删除，内容并入 formats.py 默认 format_params
- 2026-06-21: utils.py 删除（safe_ylabel 被 apply_format 重复实现）
- 2026-06-21: style_ax()/style_all() 从 A4Grid 中移除
- 2026-06-21: apply_format 从 layout.py 移入 formats.py
- 2026-06-21: finalize() 刻度相关代码全部移除，只留 auto_gap
- 2026-06-21: apply_style 中的刻度交替启发式代码移除（n_labels > 8）
- 2026-06-21: LayoutFormat 默认字段中 tick_direction/major/minor_size 移除

## 踩坑

- AI 编造的模板（A4-2x1-portrait、nature/elsevier 系列）已被用户删除。每个模板必须有实际需求来源。
- `_direction` 和 `set_ydata()` 在 matplotlib≥3.8 中无效，需用 `set_marker(2/3)`。
