#!/usr/bin/env python3
"""
REE + Spider 1×2 A4 拼版管道模板（新流程 v2.1）。

用法：
    1. 改 DATA_PATH 为你的 Excel 文件路径
    2. 调整字体大小、边距等参数
    3. python3 ree-spider-1x2-pipeline.py

输出到桌面：ree_bare.png + spider_bare.png + ree_spider_panel.png
"""

import sys, os
# 添加 figkit 和 IgneousWR 路径
sys.path.insert(0, os.path.expanduser('~/.hermes/skills/plotting/figkit/scripts'))
sys.path.insert(0, os.path.expanduser('~/igneouswr/scripts'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from layout import A4Grid
from igneous_wr_core import (
    GeochemData, plot_ree, plot_spider,
    apply_spider_axis_style, apply_ree_axis_style,
)

# ════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════

DATA_PATH = '/mnt/c/Users/opcry/Desktop/MT01-04主微量.xlsx'
OUT_DIR = '/mnt/c/Users/opcry/Desktop/'

# 视觉参数（裸图和拼版共用——线粗、点大小保持一致）
STYLE = {
    'linewidth': 1.0,
    'markersize': 8,
}

# ════════════════════════════════════════════
# 裸图（正常宽高比预览）
# ════════════════════════════════════════════

gd = GeochemData(DATA_PATH)

# 裸图字号：8 英寸画布，9pt 足够
plt.rcParams.update({'font.size': 9, 'font.family': 'serif', 'axes.linewidth': 0.6})

# REE 裸图
fig, ax = plt.subplots(figsize=(8, 5))
plot_ree(gd, ax=ax, **STYLE)
apply_ree_axis_style(ax)
plt.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT_DIR, 'ree_bare.png'), dpi=300)

# Spider 裸图
fig, ax = plt.subplots(figsize=(8, 5))
plot_spider(gd, ax=ax, **STYLE)
apply_spider_axis_style(ax)
plt.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT_DIR, 'spider_bare.png'), dpi=300)

print('裸图完成 ✓')

# ════════════════════════════════════════════
# A4 拼版（字号须小于裸图——cell 宽度有限）
# ════════════════════════════════════════════

# 拼版字号：75mm cell 容纳 29 个蛛网标签→7pt
plt.rcParams.update({'font.size': 7, 'font.family': 'serif', 'axes.linewidth': 0.6})

layout = A4Grid(1, 2, paper='A4',
                left=25, right=25, top=128, bottom=128,
                hspace=0, wspace=10)

ax_ree = layout.add_subplot(0, 0, label='ree')
ax_sp  = layout.add_subplot(0, 1, label='sp')

plot_ree(gd, ax=ax_ree, **STYLE)
plot_spider(gd, ax=ax_sp, **STYLE)

layout.finalize(pairs=('ree', 'sp'))
apply_ree_axis_style(ax_ree)
apply_spider_axis_style(ax_sp)
layout.save(os.path.join(OUT_DIR, 'ree_spider_panel.png'))

print(f'拼版完成 ✓ → {OUT_DIR}')
