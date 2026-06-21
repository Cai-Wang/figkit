"""
格式管理 — 期刊投稿技术参数 + 出图后统一格式/风格控制。

LayoutFormat 组合了 布局 + 格式参数。
apply_format() 是出图第四步（调完 finalize 后），统一控制所有文本字号字体和图例。
apply_style()  覆盖数据点的视觉参数（线粗、点大小、色板）。

用法：
    from formats import get_format, apply_format, apply_style
    from styles import get_style

    fmt = get_format('A4-2x2-standard')
    apply_format(layout, fmt)        # 统一字号、字体、刻度
    apply_style(layout, 'default')   # 统一数据点线粗、点大小
"""

from dataclasses import dataclass, field


@dataclass
class LayoutFormat:
    name: str
    description: str
    layout_params: dict
    format_params: dict = field(default_factory=lambda: {
        'dpi': 300,
        'font_family': 'serif',
        'font_size': 12,
        'font_serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'font_sans': ['Helvetica', 'Arial', 'DejaVu Sans'],
        'legend_frameon': False,
        'axes_linewidth': 0.5,
        'tick_length': 5,
        'tick_width': 0.8,
        'tick_length_minor': 3,
    })
    note: str = ""


_FORMATS: dict[str, LayoutFormat] = {}

def register(fmt: LayoutFormat):
    _FORMATS[fmt.name] = fmt

def get_format(name: str) -> LayoutFormat:
    if name not in _FORMATS:
        raise KeyError(f"未知格式: {name}，可用: {', '.join(_FORMATS.keys())}")
    return _FORMATS[name]

def list_formats() -> list[str]:
    return list(_FORMATS.keys())


# ═══════════════════════════════════════════════════════════
# A4 拼版格式（你的主要工作流）
# ═══════════════════════════════════════════════════════════

register(LayoutFormat(
    name='A4-2x2-standard',
    description='4 图标准拼版 · 每格 80×70mm，近方形',
    layout_params={
        'rows': 2, 'cols': 2, 'paper': 'A4',
        'left': 20, 'right': 20, 'top': 73, 'bottom': 74,
        'hspace': 10, 'wspace': 10,
    },
    format_params={'dpi': 300, 'font_size': 12},
    note='4 图拼版。每格 80×70mm（高宽比 0.88），分类图不拉伸。',
))

register(LayoutFormat(
    name='A4-1x2-ree-spider',
    description='REE + 蛛网图并排 · 78×42mm 单元格',
    layout_params={
        'rows': 1, 'cols': 2, 'paper': 'A4',
        'left': 25, 'right': 25, 'top': 127, 'bottom': 128,
        'hspace': 0, 'wspace': 5,
    },
    format_params={'dpi': 400, 'font_size': 8, 'tick_length': 3.5, 'tick_width': 0.55, 'tick_length_minor': 2},
    note='REE + 蛛网图。top/bottom=127/128 手动居中 42mm cell，auto_gap 自动展开间距。',
))

register(LayoutFormat(
    name='A4-3x2-dense',
    description='6 图密排 · 55mm 宽 · 10pt 字体',
    layout_params={
        'rows': 3, 'cols': 2, 'paper': 'A4',
        'left': 15, 'right': 12, 'top': 12, 'bottom': 15,
        'hspace': 6, 'wspace': 6,
    },
    format_params={'dpi': 300, 'font_size': 10},
    note='6 图密排，会议 poster 或补充材料。A4→单栏缩小后 10pt→4pt，仅适合双栏。',
))


# ═══════════════════════════════════════════════════════════
# apply_format — 出图前统一覆盖文本字号、字体、刻度
# ═══════════════════════════════════════════════════════════

def apply_format(layout, fmt):
    """统一控制所有文本字号、字体族、图例、轴框线粗。

    出图顺序第4步，调完 finalize 后、save 之前调用。
    IgneousWR 只负责把文本放对位置，apply_format 统一改字号字体。

    Parameters
    ----------
    layout : A4Grid
        已画完内容的 A4Grid 实例（需有 .axes 和 .cell_w 属性）。
    fmt : LayoutFormat
        从 get_format() 读到的格式对象。
    """
    fp = fmt.format_params
    font_size = fp.get('font_size', 12)
    family = fp.get('font_family', 'serif')
    serif_list = fp.get('font_serif', ['Times New Roman', 'Times', 'DejaVu Serif'])
    sans_list = fp.get('font_sans', ['Helvetica', 'Arial', 'DejaVu Sans'])
    legend_frameon = fp.get('legend_frameon', False)
    ax_lw = fp.get('axes_linewidth', 0.5)
    tick_len = fp.get('tick_length', 5)
    tick_w = fp.get('tick_width', 0.8)
    tick_len_minor = fp.get('tick_length_minor', 3)

    import matplotlib.pyplot as plt
    # 字体族
    if family == 'sans-serif':
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = sans_list
    else:
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['font.serif'] = serif_list

    for ax in layout.axes:
        # 轴框线粗
        for sp in ax.spines.values():
            sp.set_linewidth(ax_lw)

        # 轴标签字号 + 刻度标签字号
        ax.xaxis.label.set_size(font_size)
        ax.yaxis.label.set_size(font_size)
        ax.tick_params(labelsize=font_size - 1)

        # 所有底图文本（TAS 分区名等）
        for t in ax.texts:
            t.set_fontsize(font_size - 1)

        # 图例
        leg = ax.get_legend()
        if leg:
            plt.setp(leg.get_texts(), fontsize=font_size - 2)
            leg.get_frame().set_visible(legend_frameon)
            leg.get_frame().set_linewidth(0.5)


# ═══════════════════════════════════════════════════════════
# apply_style — 出图后覆盖数据点视觉参数（线粗、点大小、色板）
# ═══════════════════════════════════════════════════════════

def apply_style(layout, style_name='default'):
    """用 styles.py 里的 DiagramStyle 参数覆盖所有数据元素。

    原理：遍历图中所有线条和散点集合，把数据元素（有标签的线条、
    所有 PathCollection）的视觉参数改成风格模板里的值。
    边界线/参考线无标签，不会被覆盖。
    图例会统一合并到第一个子图上，只显示颜色圆点、不显示线条。

    Parameters
    ----------
    layout : A4Grid
        已画完内容的 A4Grid 实例。
    style_name : str
        styles.py 中注册的风格名称（如 'default', 'ree', 'ternary'）。
    """
    from styles import get_style
    from matplotlib.lines import Line2D
    s = get_style(style_name)
    if s is None:
        return

    all_handles_labels = {}  # label → color 去重

    for ax in layout.axes:
        # ── 数据线：有标签的 Line2D（边界线/参考线无标签） ──
        for line in ax.get_lines():
            lbl = line.get_label()
            if lbl and not lbl.startswith('_'):
                line.set_linewidth(s.line_width)
                all_handles_labels[lbl] = line.get_color()

        # ── 数据点：所有 PathCollection 都是散点 ──
        for coll in ax.collections:
            if hasattr(coll, 'set_sizes'):
                coll.set_sizes([s.marker_size])
            if s.marker_edge_color and hasattr(coll, 'set_edgecolor'):
                coll.set_edgecolor(s.marker_edge_color)
            if s.marker_edge_width > 0 and hasattr(coll, 'set_linewidth'):
                coll.set_linewidth(s.marker_edge_width)

    # ── 共享图例：只画在第一个子图上（纯色点、无线条） ──
    if all_handles_labels and layout.axes:
        handles = [
            Line2D([0], [0], marker='o', color='white',
                   markerfacecolor=c, markersize=s.marker_size / 6,
                   markeredgecolor=c, markeredgewidth=0.5,
                   linewidth=0)
            for c in all_handles_labels.values()
        ]
        labels = list(all_handles_labels.keys())
        layout.axes[0].legend(
            handles, labels,
            loc='upper right',
            fontsize=s.legend_fontsize,
            framealpha=0.9,
            edgecolor='#CCCCCC',
        )
