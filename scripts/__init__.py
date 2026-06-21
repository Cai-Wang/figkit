"""figkit — 投稿图件工具箱。

三大模块：
  布局 (Layout) — A4Grid, finalize, auto_gap（格子定位、间距）
  格式 (Format) — 字体族/字号、DPI、轴框线粗、图例（apply_format）— ⚠️ DEPRECATED
  风格 (Style)  — 数据点线粗/点大小、共享图例（apply_style）— ⚠️ DEPRECATED

新流程（推荐）：
  1. 定风格：style = {'linewidth':1.0, 'markersize':8, ...}
     plt.rcParams.update({'font.size':9, 'font.family':'serif', ...})
  2. 建画布：layout = A4Grid(rows, cols, ...)
     ax = layout.add_subplot(row, col, label='name')
  3. 绘图：  plot_*(gd, ax=ax, **style)
  4. 排版：  layout.finalize(pairs=...)
  5. 后置：  apply_spider_axis_style(ax) / apply_ree_axis_style(ax)
  6. 保存：  layout.save(path)

旧流程（deprecated，apply_format/apply_style 会有副作用，勿用）：
  1. layout = A4Grid(...)
  2. plot_*(gd, ax=ax)
  3. layout.finalize(...)
  4. apply_format(layout, fmt)    ← 会重置 tick 属性，格线不匹配
  5. apply_style(layout, style)   ← 会覆盖数据线属性
  6. layout.save(path)

导入方式：
    import sys, os
    sys.path.insert(0, os.path.expanduser('~/.hermes/skills/plotting/figkit/scripts'))
    from layout import A4Grid
    from formats import get_format, list_formats, apply_format, apply_style
    from styles import get_style, list_styles, get_palette, list_palettes
"""
