# matplotlib Tick 方向/尺寸 操控踩坑记录

**验证环境：matplotlib 3.10.9，Python 3.12 | 最后更新：2026-06-25（新增根因：Tick 对象重建）**

## 核心结论

控制 X 轴刻度方向（向内/向外）的正确做法只有一种：

```python
# ✅ 有效
t.tick1line.set_marker(2)  # 2=向上(向内)
t.tick1line.set_marker(3)  # 3=向下(向外)
```

## 根因：fig.canvas.draw() 会重建 Tick 对象（2026-06-25 发现）

**这是本 session 最关键的发现。**

matplotlib 3.8+ 中，`fig.canvas.draw()` 内部会调用 `Axis._update_ticks()`，它会：
1. 销毁当前所有 Tick 对象
2. 根据当前 tick 位置/标签创建新的 Tick 对象
3. 新 Tick 对象的 `tick1line` 使用默认 marker 值（`marker=2`，全部向内）

这意味着：**任何在 `fig.canvas.draw()` 之前做的 `set_marker(2/3)` 都会被冲掉。**

在这个 session 之前，`plot_spider()` 在内容阶段设了 `set_marker(2/3)`，然后 `finalize→auto_gap` 内部调了 `fig.canvas.draw()` 来测量渲染尺寸——set_marker 就这样被静默蒸发了。刻度"恢复默认"看似是小问题，但本质是绘图管线的时序破坏。

### 后果

| 现象 | 根因 | 修复 |
|------|------|------|
| 拼版后刻度交替消失（全变向内） | auto_gap 内部的 draw() 重建了 Tick 对象 | 把 set_marker/标签偏移拆入后置函数 |
| 独立出图时正常（刻度交替在） | 独立模式只有一次 draw（在 plot_spider 尾部），之后不再有第二次 draw | — |

### 修复方案

把 Tick 对象级样式从 `plot_spider()` 主路径拆出为独立的 **后置函数**：

```python
def apply_spider_axis_style(ax):
    """必须在 finalize() 和 apply_format() **之后**调用。"""
    fig = ax.figure
    fig.canvas.draw()                # ← 本次 draw 初始化 Tick，之后不再有 draw
    for i, t in enumerate(...):
        t.tick1line.set_marker(3 if i % 2 else 2)  # ← 安全了
```

调用顺序：
```
1. plot_* (内容) → 2. finalize (排版, ⚠ draw) → 3. apply_format → 4. apply_*_axis_style (Tick 级) → 5. save
```

## 已证实的无效方法

| 方法 | 结果 | 原因 |
|------|------|------|
| `t._direction = 'out'` | ❌ 不生效 | `_direction` 属性在 3.10 中被渲染器忽略 |
| `t.tick1line.set_ydata([0, -length])` | ❌ 不生效 | 渲染器用 marker 绘制刻度，不是 ydata |

## `ax.tick_params()` 行为

`tick_params()` 不是"增量更新"——即使只传 `length` 和 `width`，它也会**重置所有 tick 的属性**（包括 marker 类型）。

```python
# 这会破坏 step 1 设置的 marker(2/3)
ax.tick_params(length=3.5, width=0.55)
# → 所有 tick 的 marker=2（全部向内），交替消失
```

**正确做法：** 不在画图后调 `tick_params`。改用 `plt.rcParams` 在画图前设好尺寸。

```python
import matplotlib.pyplot as plt

# 放在 plot_spider() / plot_ree() 之前
plt.rcParams['xtick.major.size'] = 3.5   # 主刻度长度
plt.rcParams['xtick.major.width'] = 0.55 # 主刻度粗细
plt.rcParams['xtick.minor.size'] = 2.0   # 副刻度长度
# Y 轴同理
plt.rcParams['ytick.major.size'] = 3.5
plt.rcParams['ytick.major.width'] = 0.55
plt.rcParams['ytick.minor.size'] = 2.0
```

`plot_spider` 内部会调 `fig.canvas.draw()` 来初始化 tick 对象，此时 rcParams 里的尺寸值已被读取，之后的 `set_marker(2/3)` 也存活。

## 初始化时机

tick 对象需要 `fig.canvas.draw()` 后才能被修改。`plot_spider` 在 standalone 模式下会调 `tight_layout` → `draw`。figkit 模式下调用方需确保 ticks 已初始化。

## 长度与字号缩放

刻度长度应随字号等比缩放。默认 IgneousWR 在字号 12pt 时使用：

- TICK_LENGTH = 5 (主刻度)
- TICK_LENGTH_M = 3 (副刻度)
- TICK_WIDTH = 0.8

缩放公式：`新长度 = 原长度 × (新字号 / 12)`

例如字号 8pt → `5 × (8/12) ≈ 3.5`
