# 2026-06-21 架构决策

## figkit 边界
该管（全局统一）：字体族、字号、DPI、轴框线粗、图例、数据点风格、刻度 SIZE（画前 rcParams）。
不碰（IgneousWR 管）：刻度方向/交替/偏移、副刻度、网格、Y 竖排、标签旋转。

## 关键踩坑
`ax.tick_params(length=X, width=Y)` 重置所有 tick 属性（含 marker 2/3）。
不是增量更新。正确做法：画图前 `plt.rcParams['xtick.major.size'] = X`。

## 各模块职责
- apply_format: font family/size, axes linewidth, legend frame only
- apply_style: line width, marker size, shared legend (dots only, axes[0] only)
- finalize: auto_gap only (no tick manipulation)
- A4Grid: pure layout (no style_ax/style_all)
