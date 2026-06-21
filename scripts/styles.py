"""
风格管理 — 各图型的视觉美学参数。

调色板说明（遵循期刊色盲友好规范）：
  tab10      → matplotlib 默认，10 色循环
  nature     → Nature 风格，柔和低饱和（蓝橙褐绿紫灰）
  colorblind → 蓝-橙-黄-绿-紫，避免红绿搭配
  grayscale  → 黑白打印专用灰度

用法：
    from styles import get_style, list_styles, get_palette
    s = get_style('tas')
    colors = get_palette('nature')
"""

from dataclasses import dataclass


# ── 调色板 ────────────────────────────────────────────

PALETTES = {
    'tab10': [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    ],
    'nature': [  # Nature 风格：低饱和度、学术感
        '#3B4992', '#EE0000', '#008B45', '#631879', '#008280',
        '#BB0021', '#5F559B', '#A20056', '#808080', '#1B9E77',
    ],
    'colorblind': [  # 色盲友好：蓝-橙-黄-绿-紫 + 变体
        '#0072B2', '#E69F00', '#F0E442', '#009E73', '#CC79A7',
        '#56B4E9', '#D55E00', '#999999', '#66C2A5', '#FC8D62',
    ],
    'grayscale': [  # 黑白打印用
        '#000000', '#333333', '#555555', '#777777', '#999999',
        '#BBBBBB', '#444444', '#666666', '#888888', '#AAAAAA',
    ],
}

DEFAULT_PALETTE = 'nature'  # 默认用 nature 风格


def get_palette(name: str = None) -> list:
    if name is None:
        name = DEFAULT_PALETTE
    if name not in PALETTES:
        name = DEFAULT_PALETTE
    return PALETTES[name]


def list_palettes() -> list[str]:
    return list(PALETTES.keys())


# ── 图型风格 ──────────────────────────────────────────

@dataclass
class DiagramStyle:
    name: str
    marker: str = 'o'
    marker_size: int = 40
    marker_edge_color: str | None = None
    marker_edge_width: float = 0
    line_width: float = 1.0
    palette: str = 'nature'
    legend_fontsize: int = 7
    note: str = ""


_STYLES: dict[str, DiagramStyle] = {}

def register(s: DiagramStyle):
    _STYLES[s.name] = s

def get_style(name: str) -> DiagramStyle:
    return _STYLES.get(name, _STYLES.get('default'))

def list_styles() -> list[str]:
    return list(_STYLES.keys())


register(DiagramStyle(name='default',
    marker='o', marker_size=40, line_width=1.0, palette='nature',
    note='通用默认。'))

register(DiagramStyle(name='tas',
    marker='o', marker_size=50, marker_edge_color='#333333',
    marker_edge_width=0.3, line_width=1.5, palette='nature',
    note='TAS 点稍大加细边，在黑线边界中清晰。'))

register(DiagramStyle(name='k2o_sio2',
    marker='o', marker_size=45, line_width=1.5, palette='nature'))

register(DiagramStyle(name='afm',
    marker='o', marker_size=45, line_width=1.5, palette='nature'))

register(DiagramStyle(name='discrimination',
    marker='o', marker_size=42, marker_edge_color='#333333',
    marker_edge_width=0.2, line_width=1.5, palette='nature',
    note='判别图。加细边，适合黑白打印。'))

register(DiagramStyle(name='ree',
    marker='o', marker_size=8, line_width=1.2, palette='nature',
    legend_fontsize=6,
    note='REE 小点在线段上。'))

register(DiagramStyle(name='spider',
    marker='o', marker_size=8, line_width=1.0, palette='nature',
    legend_fontsize=6,
    note='蛛网图小点在线段上。'))

register(DiagramStyle(name='miyashiro',
    marker='o', marker_size=40, line_width=1.5, palette='nature'))

register(DiagramStyle(name='shervais',
    marker='o', marker_size=42, marker_edge_color='#333333',
    marker_edge_width=0.2, line_width=1.5, palette='nature'))

register(DiagramStyle(name='ternary',
    marker='o', marker_size=15, line_width=1.5, palette='nature',
    note='三元图空间紧凑，点比二元图小一半。'))
