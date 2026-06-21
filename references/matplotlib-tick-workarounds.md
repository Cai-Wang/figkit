# matplotlib Tick 方向/尺寸 操控踩坑记录

**验证环境：matplotlib 3.10.9，Python 3.12**

## 核心结论

控制 X 轴刻度方向（向内/向外）的正确做法只有一种：

```python
# ✅ 有效
t.tick1line.set_marker(2)  # 2=向上(向内)
t.tick1line.set_marker(3)  # 3=向下(向外)
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
