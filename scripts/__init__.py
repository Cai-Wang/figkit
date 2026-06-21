"""figkit — 投稿图件工具箱。

三大模块：
  布局 (Layout) — A4Grid, finalize, auto_gap（格子定位、间距）
  格式 (Format) — 字体族/字号、DPI、轴框线粗、图例（apply_format）
  风格 (Style)  — 数据点线粗/点大小、共享图例（apply_style）、调色板

出图顺序：
  1. 搭画布：  layout = A4Grid(...)
  2. 画内容：  plot_*(gd, ax=ax)
  3. 收尾：    layout.finalize(...)
  4. 格式把关：apply_format(layout, fmt)    ← 字号/字体/图例
  5. 风格覆盖：apply_style(layout, 'default')← 线粗/点大小
  6. 保存：    layout.save(path)

导入方式：
    import sys, os
    sys.path.insert(0, os.path.expanduser('~/.hermes/skills/plotting/figkit/scripts'))
    from layout import A4Grid
    from formats import get_format, list_formats, apply_format, apply_style
    from styles import get_style, list_styles, get_palette, list_palettes
"""
