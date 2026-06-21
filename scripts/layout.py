"""
A4Grid — A4 纸 + mm 网格 + add_axes 绝对定位排版类。

用法：
    from layout import A4Grid

    layout = A4Grid(2, 2, paper='A4', left=20, right=15, top=15, bottom=20, hspace=7, wspace=7)
    ax_a = layout.add_subplot(0, 0, label='a')
    ax_b = layout.add_subplot(0, 1, label='b')
    ax_c = layout.add_subplot(1, 0, label='c')
    ax_d = layout.add_subplot(1, 1, label='d')

    # ... 画数据 ...

    layout.finalize(pairs=[('a', 'b'), ('c', 'd')])  # 多对并排
    layout.save('figure.png')

已知坑（来自踩踏经验）：
    - auto_gap 内部调 fig.canvas.draw() 会重置 tick._direction
    - finalize() 在 auto_gap 之后补 tick 设置，所以放最后调
"""

import matplotlib.pyplot as plt


class A4Grid:
    """A4纸+网格布局+add_axes绝对定位。

    支持多种纸张尺寸预设，mosaic 创建，colorbar 嵌入。
    row 0 = 最顶行（与 matplotlib GridSpec / subplots 一致）。

    Parameters
    ----------
    rows, cols : int
        网格行数和列数。
    paper : str or tuple
        'A4' (210×297), 'A4_landscape', 'A3', 'single_column' (85×70),
        'double_column' (175×130), 'wide' (180×110),
        或 (w_mm, h_mm) 自定义。
    left, right, top, bottom : float
        页边距，mm。
    hspace, wspace : float
        格子间距，mm。
    dpi : int
        输出 dpi。
    font_scale : float
        字号缩放因子。
    """

    PRESETS = {
        'A4': (210, 297),
        'A4_landscape': (297, 210),
        'A3': (297, 420),
        'single_column': (85, 70),
        'double_column': (175, 130),
        'wide': (180, 110),
    }

    def __init__(self, rows, cols, paper='A4',
                 left=20, right=15, top=15, bottom=20,
                 hspace=5, wspace=5, dpi=300, font_scale=1.0):
        if isinstance(paper, str):
            self.paper_w, self.paper_h = self.PRESETS[paper]
        else:
            self.paper_w, self.paper_h = paper
        self.rows, self.cols = rows, cols
        self.margins = {'left': left, 'right': right, 'top': top, 'bottom': bottom}
        self.hspace, self.wspace = hspace, wspace
        self.font_scale = font_scale
        self._y_offset = 0
        usable_w = self.paper_w - left - right
        usable_h = self.paper_h - top - bottom
        self.cell_w = (usable_w - (cols - 1) * wspace) / cols
        self.cell_h = (usable_h - (rows - 1) * hspace) / rows

        self.fig = plt.figure(
            figsize=(self.paper_w / 25.4, self.paper_h / 25.4),
            dpi=dpi, facecolor='white',
        )
        self._axes = {}
        self._axes_geom = {}  # name → (row, col, rowspan, colspan)
        self.paper = paper

    def _mm_to_fig(self, x_mm, y_mm, w_mm, h_mm):
        return [
            x_mm / self.paper_w,
            y_mm / self.paper_h,
            w_mm / self.paper_w,
            h_mm / self.paper_h,
        ]

    def _cell_rect(self, row, col, rowspan=1, colspan=1):
        """返回 [x_mm, y_mm, w_mm, h_mm]，row 0 = 最顶行。"""
        x = self.margins['left'] + col * (self.cell_w + self.wspace)
        y = (self.paper_h - self.margins['top']
             - (row + 1) * self.cell_h - row * self.hspace
             - self._y_offset)
        w = self.cell_w + (colspan - 1) * (self.cell_w + self.wspace)
        h = self.cell_h + (rowspan - 1) * (self.cell_h + self.hspace)
        return [x, y, w, h]

    def add_subplot(self, row, col, rowspan=1, colspan=1, label=None):
        """在 (row, col) 位置添加一个子图。label 用于 finalize() 传参。"""
        rect_mm = self._cell_rect(row, col, rowspan, colspan)
        rect = self._mm_to_fig(*rect_mm)
        ax = self.fig.add_axes(rect)
        name = label or f'{row}_{col}'
        self._axes[name] = ax
        self._axes_geom[name] = (row, col, rowspan, colspan)
        return ax

    def get_ax(self, name):
        """通过 label 获取子图。"""
        return self._axes[name]

    @property
    def axes(self):
        """所有子图列表。"""
        return list(self._axes.values())

    def add_colorbar(self, mappable, label='', which='right',
                     size_mm=4, pad_mm=2, fontsize=None):
        """添加 colorbar。"""
        if fontsize is None:
            fontsize = min(12, max(6, round(self.paper_h / 25.4 * 0.4 * self.font_scale)))
        ax = list(self._axes.values())[-1]
        pos = ax.get_position()
        if which == 'right':
            cax = self.fig.add_axes([
                pos.x1 + pad_mm / self.paper_w, pos.y0,
                size_mm / self.paper_w, pos.height,
            ])
        else:
            cax = self.fig.add_axes([
                pos.x0, pos.y0 - pad_mm / self.paper_h - size_mm / self.paper_h,
                pos.width, size_mm / self.paper_h,
            ])
        cb = self.fig.colorbar(mappable, cax=cax)
        cb.set_label(label, fontsize=fontsize)
        cb.ax.tick_params(labelsize=fontsize - 1)
        return cb

    def auto_gap(self, pairs=None, extra_padding_mm=3):
        """用 renderer 实测右图文字向左延伸宽度，自动重排 gap。

        修复说明：旧版错误地把左轴文本的左边缘与右轴 x0 做差，
        导致 gap 被撑到几乎整个页面宽度。
        新版只测每个文本相对它所在轴的延伸方向：
        - 右轴元素量向左延伸（超出右轴左边界进入 gap 的距离）
        - 左轴元素量向右延伸（超出左轴右边界进入 gap 的距离）

        Parameters
        ----------
        pairs : list of tuple or tuple
            （推荐）多对，如 [('ree0','sp0'), ('ree1','sp1')]。
            单对也可传 ('a','b')。
        extra_padding_mm : float
            额外 padding，默认 3 mm。

        ⚠️ 内部调 fig.canvas.draw() 会重置 tick._direction / Tick 对象。
        Tick 对象级样式（set_marker 等）必须在 auto_gap **之后**设置。
        """
        if pairs is None:
            return 0
        # 兼容单对 ('a','b') 用法
        if isinstance(pairs, tuple) and len(pairs) == 2 and isinstance(pairs[0], str):
            pairs = [pairs]

        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        inv = self.fig.transFigure.inverted()

        max_gap = self.wspace
        for left_name, right_name in pairs:
            left_ax, right_ax = self._axes[left_name], self._axes[right_name]

            ext_panel = 0

            # ── 右轴元素向左延伸（ylabel + 文本/标签） ──
            for t in [right_ax.yaxis.label] + right_ax.texts:
                b = inv.transform(t.get_window_extent(renderer))
                tb_left = min(b[:, 0])
                e = (right_ax.get_position().x0 - tb_left) * self.paper_w
                if e > ext_panel:
                    ext_panel = e

            # ── 左轴元素向右延伸（文本/标签；ylabel 默认在左侧，不进入 gap） ──
            for t in left_ax.texts:
                b = inv.transform(t.get_window_extent(renderer))
                tb_right = max(b[:, 0])
                e = (tb_right - left_ax.get_position().x1) * self.paper_w
                if e > ext_panel:
                    ext_panel = e

            gap = max(ext_panel + extra_padding_mm, 5)
            if gap > max_gap:
                max_gap = gap

        if max_gap > self.wspace:
            self.wspace = max_gap
            usable_w = self.paper_w - self.margins['left'] - self.margins['right']
            self.cell_w = (usable_w - (self.cols - 1) * self.wspace) / self.cols
            for name, ax in self._axes.items():
                row, col, rspan, cspan = self._axes_geom[name]
                rect_mm = self._cell_rect(row, col, rspan, cspan)
                ax.set_position(self._mm_to_fig(*rect_mm))
        return max_gap

    def finalize(self, pairs=None):
        """一步完成：auto_gap 调整左右间距。

        这是排版重定位的最后一步，之后不应再调 set_position()。
        Tick 对象级样式（set_marker、标签偏移）必须在 finalize **之后**设置。

        Parameters
        ----------
        pairs : list of tuple or tuple, optional
            （推荐）多对，如 [('ree0','sp0'), ('ree1','sp1')]。
            单对也可传 ('a','b')，不调传 None。
        """
        if pairs:
            self.auto_gap(pairs=pairs)
            return


    def save(self, path=None, bbox_inches=None, pad_inches=0.05,
             transparent=False, dpi=None):
        """保存图片。不传 bbox_inches 时保留精确 mm 定位。"""
        if path is None:
            path = f'Figure_{self.paper if isinstance(self.paper, str) else "custom"}.png'
        ext = path.rsplit('.', 1)[-1].lower()
        fmt = ext if ext in ('pdf', 'svg', 'eps') else None
        self.fig.savefig(
            path, dpi=dpi or self.fig.dpi, format=fmt,
            bbox_inches=bbox_inches, pad_inches=pad_inches,
            transparent=transparent,
        )
        plt.close(self.fig)
